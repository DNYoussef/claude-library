"""
Redis Pub/Sub Event Bus - Reusable Library Component

A generalized Redis Pub/Sub implementation for broadcasting messages across
multiple application workers or processes. Commonly used for:
- WebSocket message broadcasting across FastAPI/ASGI workers
- Microservice event distribution
- Real-time notification systems
- Distributed task coordination

Features:
- Async/await native using redis.asyncio
- Automatic reconnection on listener failure
- Channel-based message routing with custom handlers
- JSON serialization with fallback for non-serializable types
- Subscriber count monitoring
- Graceful shutdown handling

Usage Example:
    from redis_pubsub import RedisPubSub

    # Initialize
    pubsub = RedisPubSub()
    await pubsub.initialize("redis://localhost:6379")

    # Subscribe with handler
    async def my_handler(data: dict):
        print(f"Received: {data}")

    await pubsub.subscribe("my:channel", my_handler)

    # Publish messages
    await pubsub.publish("my:channel", {"event": "user_joined", "user_id": "123"})

    # Cleanup
    await pubsub.close()

Channel Naming Conventions (suggested):
- broadcast - Global broadcast to all subscribers
- user:{user_id} - User-specific channel
- connection:{connection_id} - Connection-specific channel
- service:{service_name} - Service-to-service communication
- topic:{topic_name} - Topic-based pub/sub

Author: Extracted from Life OS Dashboard
License: MIT
"""

import asyncio
import json
import logging
import random
from typing import Callable, Optional, Dict, Any, Awaitable, Union

try:
    import redis.asyncio as aioredis
except ImportError:
    raise ImportError(
        "redis package with async support is required. "
        "Install with: pip install redis[hiredis]"
    )

logger = logging.getLogger(__name__)


# Type alias for message handlers
MessageHandler = Callable[[Dict[str, Any]], Awaitable[None]]

# Type alias for error callbacks (channel, data, exception)
ErrorCallback = Callable[[str, Dict[str, Any], Exception], Awaitable[None]]


class RedisPubSub:
    """
    Redis Pub/Sub manager for broadcasting messages across distributed systems.

    This class provides a high-level interface for Redis pub/sub operations,
    handling connection management, message serialization, and automatic
    listener recovery.

    Attributes:
        redis: The underlying async Redis connection.
        pubsub: The Redis pub/sub interface.
        channels: Mapping of channel names to their message handlers.

    Example:
        >>> pubsub = RedisPubSub()
        >>> await pubsub.initialize("redis://localhost:6379")
        >>> await pubsub.subscribe("events", handler_func)
        >>> await pubsub.publish("events", {"type": "notification"})
        >>> await pubsub.close()
    """

    def __init__(self):
        """Initialize RedisPubSub instance (call initialize() to connect)."""
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.channels: Dict[str, MessageHandler] = {}
        self._channel_error_callbacks: Dict[str, ErrorCallback] = {}
        self._listening_task: Optional[asyncio.Task] = None
        self._listener_lock: asyncio.Lock = asyncio.Lock()
        self._reconnect_delay: float = 5.0
        self._max_reconnect_delay: float = 300.0  # 5 minutes max backoff
        self._reconnect_attempt: int = 0
        self._max_connections: int = 50
        self._redis_url: Optional[str] = None
        self._encoding: str = "utf-8"
        self._decode_responses: bool = True

    async def initialize(
        self,
        redis_url: str,
        max_connections: int = 50,
        encoding: str = "utf-8",
        decode_responses: bool = True,
    ) -> None:
        """
        Initialize Redis pub/sub connection.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379",
                       "redis://:password@host:port/db").
            max_connections: Maximum number of connections in the pool.
                            Default is 50.
            encoding: Character encoding for messages. Default is "utf-8".
            decode_responses: Whether to decode response bytes to strings.
                             Default is True.

        Raises:
            ConnectionError: If unable to connect to Redis.
            ValueError: If redis_url is invalid.

        Example:
            >>> pubsub = RedisPubSub()
            >>> await pubsub.initialize("redis://localhost:6379")
        """
        if not redis_url:
            raise ValueError("redis_url is required")

        self._max_connections = max_connections
        self._redis_url = redis_url
        self._encoding = encoding
        self._decode_responses = decode_responses

        try:
            self.redis = await aioredis.from_url(
                redis_url,
                encoding=encoding,
                decode_responses=decode_responses,
                max_connections=max_connections,
            )
            self.pubsub = self.redis.pubsub()
            logger.info("RedisPubSub initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis pub/sub: {e}")
            raise ConnectionError(f"Failed to connect to Redis: {e}") from e

    async def close(self) -> None:
        """
        Close Redis pub/sub connection and cleanup resources.

        This method gracefully shuts down:
        1. The background listener task
        2. The pub/sub subscription
        3. The Redis connection

        Safe to call multiple times.

        Example:
            >>> await pubsub.close()
        """
        # Cancel listening task
        if self._listening_task:
            self._listening_task.cancel()
            try:
                await self._listening_task
            except asyncio.CancelledError:
                pass
            self._listening_task = None

        # Close pub/sub
        if self.pubsub:
            await self.pubsub.close()
            self.pubsub = None

        # Close Redis connection
        if self.redis:
            await self.redis.close()
            self.redis = None

        self.channels.clear()
        self._channel_error_callbacks.clear()
        self._reconnect_attempt = 0
        logger.info("RedisPubSub closed")

    async def subscribe(
        self,
        channel: str,
        handler: MessageHandler,
        error_callback: Optional[ErrorCallback] = None,
    ) -> None:
        """
        Subscribe to a channel with a message handler.

        The handler will be called asynchronously for each message received
        on the channel. Multiple subscriptions can be active simultaneously.

        Args:
            channel: Redis channel name to subscribe to.
            handler: Async function that receives parsed message data.
                    Signature: async def handler(data: Dict[str, Any]) -> None
            error_callback: Optional async function called when handler raises
                           an exception. Useful for dead-letter queues, retries,
                           or custom error handling.
                           Signature: async def error_callback(
                               channel: str, data: Dict[str, Any], error: Exception
                           ) -> None

        Raises:
            RuntimeError: If RedisPubSub is not initialized.

        Example:
            >>> async def on_message(data: dict):
            ...     print(f"Received: {data}")
            >>> async def on_error(channel: str, data: dict, error: Exception):
            ...     print(f"Error on {channel}: {error}")
            ...     # Send to dead-letter queue, retry, etc.
            >>> await pubsub.subscribe("notifications", on_message, on_error)
        """
        if not self.pubsub:
            raise RuntimeError(
                "RedisPubSub not initialized. Call initialize() first."
            )

        self.channels[channel] = handler
        if error_callback:
            self._channel_error_callbacks[channel] = error_callback
        await self.pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")

        # Start listening if not already running
        if not self._listening_task or self._listening_task.done():
            self._listening_task = asyncio.create_task(self._listen())

    async def subscribe_pattern(
        self,
        pattern: str,
        handler: MessageHandler,
        error_callback: Optional[ErrorCallback] = None,
    ) -> None:
        """
        Subscribe to channels matching a pattern.

        Patterns use glob-style matching:
        - * matches any sequence of characters
        - ? matches any single character
        - [abc] matches any character in the set

        Args:
            pattern: Redis channel pattern (e.g., "user:*", "events:?:created").
            handler: Async function that receives parsed message data.
            error_callback: Optional async function called when handler raises
                           an exception. Useful for dead-letter queues, retries,
                           or custom error handling.

        Raises:
            RuntimeError: If RedisPubSub is not initialized.

        Example:
            >>> await pubsub.subscribe_pattern("user:*", on_user_event)
        """
        if not self.pubsub:
            raise RuntimeError(
                "RedisPubSub not initialized. Call initialize() first."
            )

        self.channels[pattern] = handler
        if error_callback:
            self._channel_error_callbacks[pattern] = error_callback
        await self.pubsub.psubscribe(pattern)
        logger.info(f"Subscribed to pattern: {pattern}")

        # Start listening if not already running
        if not self._listening_task or self._listening_task.done():
            self._listening_task = asyncio.create_task(self._listen())

    async def unsubscribe(self, channel: str) -> None:
        """
        Unsubscribe from a channel.

        Args:
            channel: Redis channel name to unsubscribe from.

        Example:
            >>> await pubsub.unsubscribe("notifications")
        """
        if not self.pubsub:
            return

        await self.pubsub.unsubscribe(channel)
        self.channels.pop(channel, None)
        self._channel_error_callbacks.pop(channel, None)
        logger.info(f"Unsubscribed from channel: {channel}")

    async def unsubscribe_pattern(self, pattern: str) -> None:
        """
        Unsubscribe from a channel pattern.

        Args:
            pattern: Redis channel pattern to unsubscribe from.

        Example:
            >>> await pubsub.unsubscribe_pattern("user:*")
        """
        if not self.pubsub:
            return

        await self.pubsub.punsubscribe(pattern)
        self.channels.pop(pattern, None)
        self._channel_error_callbacks.pop(pattern, None)
        logger.info(f"Unsubscribed from pattern: {pattern}")

    async def _ensure_connection(self) -> bool:
        """
        Verify Redis connection health and attempt reconnection if stale.

        Returns:
            True if connection is healthy or successfully reconnected.

        Raises:
            RuntimeError: If Redis was never initialized (no URL stored).
        """
        if not self._redis_url:
            return False

        # Check if redis client exists
        if not self.redis:
            logger.info("Redis client missing, attempting reconnection")
            await self._reconnect()
            return self.redis is not None

        # Ping to verify connection is alive
        try:
            await self.redis.ping()
        except Exception as e:
            logger.warning(f"Redis connection stale: {e}, attempting reconnection")
            await self._reconnect()
            return self.redis is not None
        return True

    async def _reconnect(self) -> None:
        """
        Attempt to reconnect to Redis using stored configuration.
        """
        if not self._redis_url:
            logger.error("Cannot reconnect: no redis_url stored")
            return

        try:
            # Close existing connections if any
            if self.pubsub:
                try:
                    await self.pubsub.close()
                except Exception:
                    pass
            if self.redis:
                try:
                    await self.redis.close()
                except Exception:
                    pass

            # Reconnect
            self.redis = await aioredis.from_url(
                self._redis_url,
                encoding=self._encoding,
                decode_responses=self._decode_responses,
                max_connections=self._max_connections,
            )
            self.pubsub = self.redis.pubsub()

            # Re-subscribe to all channels
            for channel in list(self.channels.keys()):
                if "*" in channel or "?" in channel or "[" in channel:
                    await self.pubsub.psubscribe(channel)
                else:
                    await self.pubsub.subscribe(channel)

            logger.info("Successfully reconnected to Redis")
        except Exception as e:
            logger.error(f"Failed to reconnect to Redis: {e}")
            self.redis = None
            self.pubsub = None

    async def publish(
        self,
        channel: str,
        data: Union[Dict[str, Any], str],
    ) -> int:
        """
        Publish a message to a channel.

        Args:
            channel: Redis channel to publish to.
            data: Message data. If a dict, will be JSON-encoded.
                 If a string, will be sent as-is.

        Returns:
            Number of subscribers that received the message.

        Raises:
            RuntimeError: If Redis is not connected and reconnection fails.

        Example:
            >>> count = await pubsub.publish("events", {"type": "user_joined"})
            >>> print(f"Delivered to {count} subscribers")
        """
        if not self.redis:
            logger.warning("Cannot publish: Redis not initialized")
            raise RuntimeError("Redis not initialized")

        # Verify connection health and reconnect if needed (LOW-PUBSUB-01)
        if not await self._ensure_connection():
            logger.error("Cannot publish: Redis connection unavailable")
            raise RuntimeError("Redis connection unavailable after reconnection attempt")

        try:
            if isinstance(data, dict):
                message_json = json.dumps(data, default=str)
            else:
                message_json = data

            result = await self.redis.publish(channel, message_json)
            logger.debug(
                f"Published to {channel}: "
                f"{data.get('type', 'unknown') if isinstance(data, dict) else 'raw'}"
            )
            return result
        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}")
            raise

    async def publish_broadcast(
        self,
        data: Dict[str, Any],
        channel_prefix: str = "broadcast",
    ) -> int:
        """
        Publish message to a broadcast channel.

        Convenience method for broadcasting to all subscribers.

        Args:
            data: Message data to broadcast.
            channel_prefix: Channel prefix for broadcast. Default is "broadcast".

        Returns:
            Number of subscribers that received the message.

        Example:
            >>> await pubsub.publish_broadcast({"event": "system_update"})
        """
        return await self.publish(channel_prefix, data)

    async def publish_to_user(
        self,
        user_id: str,
        data: Dict[str, Any],
        channel_prefix: str = "user",
    ) -> int:
        """
        Publish message to a user-specific channel.

        Convenience method for sending messages to a specific user.

        Args:
            user_id: Target user identifier.
            data: Message data to send.
            channel_prefix: Channel prefix for user channels. Default is "user".

        Returns:
            Number of subscribers that received the message.

        Example:
            >>> await pubsub.publish_to_user("user123", {"notification": "Hello!"})
        """
        channel = f"{channel_prefix}:{user_id}"
        return await self.publish(channel, data)

    async def publish_to_connection(
        self,
        connection_id: str,
        data: Dict[str, Any],
        channel_prefix: str = "connection",
    ) -> int:
        """
        Publish message to a connection-specific channel.

        Convenience method for sending messages to a specific connection.

        Args:
            connection_id: Target connection identifier.
            data: Message data to send.
            channel_prefix: Channel prefix for connection channels.
                           Default is "connection".

        Returns:
            Number of subscribers that received the message.

        Example:
            >>> await pubsub.publish_to_connection("conn_abc", {"ping": True})
        """
        channel = f"{channel_prefix}:{connection_id}"
        return await self.publish(channel, data)

    async def _listen(self) -> None:
        """
        Listen for messages on subscribed channels.

        This is a background task that runs continuously, dispatching
        messages to their registered handlers. Automatically attempts
        to reconnect on failure with exponential backoff.
        """
        logger.info("Started listening for Redis pub/sub messages")

        # Known message types from Redis pub/sub
        # - subscribe/unsubscribe: subscription confirmation
        # - psubscribe/punsubscribe: pattern subscription confirmation
        # - message: regular channel message
        # - pmessage: pattern-matched message
        SUBSCRIPTION_TYPES = {"subscribe", "unsubscribe", "psubscribe", "punsubscribe"}
        MESSAGE_TYPES = {"message", "pmessage"}

        try:
            async for message in self.pubsub.listen():
                msg_type = message.get("type")

                # Handle regular messages (HIGH-PUBSUB-01)
                if msg_type == "message":
                    channel = message["channel"]
                    await self._dispatch_message(channel, message["data"])
                    # Reset reconnect attempts on successful message processing
                    self._reconnect_attempt = 0

                # Handle pattern messages (HIGH-PUBSUB-01)
                elif msg_type == "pmessage":
                    pattern = message["pattern"]
                    await self._dispatch_message(pattern, message["data"])
                    # Reset reconnect attempts on successful message processing
                    self._reconnect_attempt = 0

                # Handle subscription confirmations (HIGH-PUBSUB-01)
                elif msg_type in SUBSCRIPTION_TYPES:
                    logger.debug(
                        f"Subscription event: {msg_type} for "
                        f"{message.get('channel') or message.get('pattern')}"
                    )

                # Log warning for unexpected message types (HIGH-PUBSUB-01)
                else:
                    logger.warning(
                        f"Received unexpected message type '{msg_type}' from Redis: "
                        f"{message}"
                    )

        except asyncio.CancelledError:
            logger.info("Stopped listening for Redis pub/sub messages")
            raise
        except Exception as e:
            logger.error(f"Error in pub/sub listener: {e}", exc_info=True)

            # Exponential backoff with jitter (HIGH-PUBSUB-02)
            self._reconnect_attempt += 1
            backoff = min(
                self._reconnect_delay * (2 ** self._reconnect_attempt),
                self._max_reconnect_delay
            )
            jitter = random.uniform(0, backoff * 0.1)
            wait_time = backoff + jitter

            logger.info(
                f"Reconnect attempt {self._reconnect_attempt}: "
                f"waiting {wait_time:.2f}s before retry"
            )
            await asyncio.sleep(wait_time)

            async with self._listener_lock:
                # Double-check no other task was created while waiting
                if self.pubsub and self.channels:
                    if self._listening_task is None or self._listening_task.done():
                        self._listening_task = asyncio.create_task(self._listen())

    async def _dispatch_message(
        self,
        channel: str,
        data: str,
    ) -> None:
        """
        Dispatch a message to its registered handler.

        Args:
            channel: The channel or pattern the message was received on.
            data: Raw message data (JSON string).
        """
        # Parse JSON data
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {channel}: {e}")
            return

        # Find and call handler
        handler = self.channels.get(channel)
        if not handler:
            logger.warning(f"No handler for channel: {channel}")
            return

        try:
            await handler(parsed_data)
        except Exception as e:
            logger.error(
                f"Error in handler for {channel}: {e}",
                exc_info=True,
            )

            # Call error callback if registered (MED-PUBSUB-02)
            # Allows custom error handling: dead-letter queue, retry, alerting, etc.
            error_callback = self._channel_error_callbacks.get(channel)
            if not error_callback:
                return
            try:
                await error_callback(channel, parsed_data, e)
            except Exception as callback_error:
                logger.error(
                    f"Error in error_callback for {channel}: {callback_error}",
                    exc_info=True,
                )

    async def get_subscriber_count(self, channel: str) -> int:
        """
        Get number of subscribers to a channel.

        Args:
            channel: Channel name to check.

        Returns:
            Number of active subscribers to the channel.

        Example:
            >>> count = await pubsub.get_subscriber_count("notifications")
            >>> print(f"{count} subscribers listening")
        """
        if not self.redis:
            return 0

        try:
            # pubsub_numsub returns a list of tuples: [(channel, count), ...]
            result = await self.redis.pubsub_numsub(channel)
            if result and isinstance(result, (list, tuple)) and len(result) > 0:
                # First tuple is (channel_name, subscriber_count)
                return result[0][1] if len(result[0]) > 1 else 0
            return 0
        except Exception as e:
            logger.error(f"Error getting subscriber count: {e}")
            return 0

    async def get_active_channels(self, pattern: str = "*") -> list:
        """
        Get list of active channels matching a pattern.

        Args:
            pattern: Glob-style pattern to match channel names.
                    Default is "*" (all channels).

        Returns:
            List of active channel names.

        Example:
            >>> channels = await pubsub.get_active_channels("user:*")
            >>> print(f"Active user channels: {channels}")
        """
        if not self.redis:
            return []

        try:
            return await self.redis.pubsub_channels(pattern)
        except Exception as e:
            logger.error(f"Error getting active channels: {e}")
            return []

    @property
    def is_connected(self) -> bool:
        """Check if Redis connection is active."""
        return self.redis is not None and self.pubsub is not None

    @property
    def subscribed_channels(self) -> list:
        """Get list of currently subscribed channels/patterns."""
        return list(self.channels.keys())


def create_redis_pubsub() -> RedisPubSub:
    """
    Factory function to create a new RedisPubSub instance.

    Returns:
        A new, uninitialized RedisPubSub instance.

    Example:
        >>> pubsub = create_redis_pubsub()
        >>> await pubsub.initialize("redis://localhost:6379")
    """
    return RedisPubSub()
