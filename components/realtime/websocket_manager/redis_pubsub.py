"""
Redis Pub/Sub for WebSocket Broadcasting

Enables message broadcasting across multiple FastAPI workers via Redis pub/sub.
Designed for horizontal scaling to support 45-50k concurrent connections.

Dependencies:
- redis (optional, for Redis backing): pip install redis

Channel Conventions:
- ws:broadcast - Broadcast to all connections
- ws:user:{user_id} - Send to specific user's connections
- ws:connection:{connection_id} - Send to specific connection
- ws:room:{room_id} - Send to room subscribers

Zero external dependencies beyond stdlib + optional redis.
"""

import asyncio
import json
import logging
from typing import Callable, Optional, Dict, Any, Protocol

logger = logging.getLogger(__name__)


class MessageProtocol(Protocol):
    """Protocol for message objects that can be converted to dict."""
    def to_dict(self) -> Dict[str, Any]: ...


class RedisPubSub:
    """
    Redis Pub/Sub manager for broadcasting WebSocket messages across workers.

    Features:
    - Multi-worker coordination via Redis pub/sub
    - Channel-based message routing (broadcast, user, connection, room)
    - Automatic reconnection on Redis failure
    - Async message handlers per channel
    - Performance monitoring ready

    Usage:
        pubsub = RedisPubSub("redis://localhost:6379")
        await pubsub.initialize()

        # Subscribe to broadcast channel
        await pubsub.subscribe("ws:broadcast", handle_broadcast)

        # Publish to all connections
        await pubsub.publish_broadcast(message)

        # Publish to specific user
        await pubsub.publish_to_user("user123", message)

        # Cleanup
        await pubsub.close()
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Redis pub/sub manager.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._redis: Optional[Any] = None
        self._pubsub: Optional[Any] = None
        self._channels: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self._listening_task: Optional[asyncio.Task] = None
        self._max_connections = 50

    async def initialize(self) -> None:
        """
        Initialize Redis pub/sub connection.

        Call this before subscribing to channels.

        Raises:
            ImportError: If redis package not installed
            Exception: If Redis connection fails
        """
        try:
            import redis.asyncio as aioredis
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self._max_connections,
            )
            self._pubsub = self._redis.pubsub()
            logger.info(f"RedisPubSub initialized: {self.redis_url}")
        except ImportError:
            logger.warning("redis package not installed, pub/sub disabled")
            raise ImportError("redis package required: pip install redis")
        except Exception as e:
            logger.error(f"Failed to initialize Redis pub/sub: {e}")
            raise

    async def close(self) -> None:
        """Close Redis pub/sub connection and cleanup."""
        # Cancel listening task
        if self._listening_task:
            self._listening_task.cancel()
            try:
                await self._listening_task
            except asyncio.CancelledError:
                pass
            self._listening_task = None

        # Close pubsub
        if self._pubsub:
            await self._pubsub.close()
            self._pubsub = None

        # Close Redis connection
        if self._redis:
            await self._redis.close()
            self._redis = None

        self._channels.clear()
        logger.info("RedisPubSub closed")

    async def subscribe(
        self,
        channel: str,
        handler: Callable[[Dict[str, Any]], Any]
    ) -> None:
        """
        Subscribe to a channel with a message handler.

        Args:
            channel: Redis channel name (e.g., "ws:broadcast")
            handler: Async function to handle received messages

        Raises:
            RuntimeError: If RedisPubSub not initialized
        """
        if not self._pubsub:
            raise RuntimeError("RedisPubSub not initialized")

        self._channels[channel] = handler
        await self._pubsub.subscribe(channel)
        logger.info(f"Subscribed to channel: {channel}")

        # Start listening if not already running
        if not self._listening_task or self._listening_task.done():
            self._listening_task = asyncio.create_task(self._listen_loop())

    async def unsubscribe(self, channel: str) -> None:
        """
        Unsubscribe from a channel.

        Args:
            channel: Redis channel name
        """
        if not self._pubsub:
            return

        await self._pubsub.unsubscribe(channel)
        self._channels.pop(channel, None)
        logger.info(f"Unsubscribed from channel: {channel}")

    async def publish_broadcast(self, message: Any) -> None:
        """
        Publish message to broadcast channel (all connections).

        Args:
            message: Message to broadcast (dict or object with to_dict())
        """
        await self._publish("ws:broadcast", message)

    async def publish_to_user(self, user_id: str, message: Any) -> None:
        """
        Publish message to user-specific channel.

        Args:
            user_id: Target user ID
            message: Message to send
        """
        channel = f"ws:user:{user_id}"
        await self._publish(channel, message)

    async def publish_to_connection(
        self,
        connection_id: str,
        message: Any
    ) -> None:
        """
        Publish message to connection-specific channel.

        Args:
            connection_id: Target connection ID
            message: Message to send
        """
        channel = f"ws:connection:{connection_id}"
        await self._publish(channel, message)

    async def publish_to_room(self, room_id: str, message: Any) -> None:
        """
        Publish message to room channel.

        Args:
            room_id: Target room ID
            message: Message to send
        """
        channel = f"ws:room:{room_id}"
        await self._publish(channel, message)

    async def _publish(self, channel: str, message: Any) -> None:
        """
        Internal publish method.

        Args:
            channel: Redis channel
            message: Message data (dict, object with to_dict(), or serializable)
        """
        if not self._redis:
            logger.warning("Cannot publish: Redis not initialized")
            return

        try:
            # Convert message to dict
            if hasattr(message, "to_dict"):
                data = message.to_dict()
            elif hasattr(message, "dict"):
                data = message.dict()  # Pydantic compatibility
            elif isinstance(message, dict):
                data = message
            else:
                data = {"data": message}

            message_json = json.dumps(data, default=str)
            await self._redis.publish(channel, message_json)
            logger.debug(f"Published to {channel}: {data.get('type', 'unknown')}")

        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}")

    async def _listen_loop(self) -> None:
        """
        Listen for messages on subscribed channels.
        Background task that runs continuously.
        """
        logger.info("Started listening for Redis pub/sub messages")

        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    data = message["data"]

                    # Parse JSON data
                    try:
                        parsed_data = json.loads(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON from {channel}: {e}")
                        continue

                    # Call handler
                    handler = self._channels.get(channel)
                    if handler:
                        try:
                            result = handler(parsed_data)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception as e:
                            logger.error(
                                f"Error in handler for {channel}: {e}",
                                exc_info=True
                            )
                    else:
                        logger.warning(f"No handler for channel: {channel}")

        except asyncio.CancelledError:
            logger.info("Stopped listening for Redis pub/sub messages")
            raise

        except Exception as e:
            logger.error(f"Error in pub/sub listener: {e}", exc_info=True)
            # Attempt to restart listener after delay
            await asyncio.sleep(5)
            if self._pubsub and self._channels:
                self._listening_task = asyncio.create_task(self._listen_loop())

    async def get_subscriber_count(self, channel: str) -> int:
        """
        Get number of subscribers to a channel.

        Args:
            channel: Channel name

        Returns:
            Number of subscribers (0 if Redis not available)
        """
        if not self._redis:
            return 0

        try:
            result = await self._redis.pubsub_numsub(channel)
            return result.get(channel, 0) if result else 0
        except Exception as e:
            logger.error(f"Error getting subscriber count: {e}")
            return 0

    @property
    def is_connected(self) -> bool:
        """Check if Redis connection is active."""
        return self._redis is not None

    @property
    def subscribed_channels(self) -> list:
        """Get list of subscribed channel names."""
        return list(self._channels.keys())

    def get_stats(self) -> Dict[str, Any]:
        """
        Get pub/sub statistics.

        Returns:
            Dictionary with connection and subscription stats
        """
        return {
            "connected": self.is_connected,
            "redis_url": self.redis_url,
            "subscribed_channels": self.subscribed_channels,
            "channel_count": len(self._channels),
            "listening": self._listening_task is not None
                         and not self._listening_task.done(),
        }
