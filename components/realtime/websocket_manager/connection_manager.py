"""
WebSocket Connection Manager

Manages WebSocket connections with optional Redis backing for horizontal scaling.
Supports JWT authentication, user-to-connection mapping, and broadcast.

Dependencies:
- aioredis (optional, for Redis backing)
- PyJWT (optional, for JWT authentication)
"""

import logging
import uuid
from typing import Dict, Set, Optional, Any, Protocol
from dataclasses import dataclass
from datetime import datetime, timezone

from .message_types import WSMessage

logger = logging.getLogger(__name__)


class WebSocketProtocol(Protocol):
    """Protocol for WebSocket-like objects."""
    async def accept(self) -> None: ...
    async def close(self, code: int = 1000, reason: str = "") -> None: ...
    async def send_json(self, data: Dict[str, Any]) -> None: ...


class AuthenticatorProtocol(Protocol):
    """Protocol for token authenticators."""
    async def authenticate(self, token: str) -> Optional[str]:
        """
        Authenticate token and return user_id.

        Args:
            token: Authentication token

        Returns:
            user_id if valid, None if invalid
        """
        ...


@dataclass
class ConnectionConfig:
    """
    Configuration for ConnectionManager.

    Attributes:
        connection_ttl: TTL in seconds for Redis connection tracking (default 3600)
        redis_url: Optional Redis URL for multi-worker support
        max_redis_connections: Max connections in Redis pool (default 100)
    """
    connection_ttl: int = 3600
    redis_url: Optional[str] = None
    max_redis_connections: int = 100


class ConnectionManager:
    """
    Manages WebSocket connections with optional Redis backing.

    Features:
    - Connection tracking (in-memory or Redis-backed)
    - User-to-connection mapping (one user can have multiple connections)
    - Pluggable authentication
    - Broadcast and targeted messaging
    - Multi-worker coordination via Redis (optional)

    Usage:
        # Create manager
        config = ConnectionConfig(redis_url="redis://localhost:6379")
        manager = ConnectionManager(config)

        # Initialize Redis (if configured)
        await manager.initialize()

        # Connect with authentication
        conn_id, user_id = await manager.connect(
            websocket=ws,
            token="jwt-token",
            authenticator=my_jwt_authenticator
        )

        # Send messages
        await manager.send_to_user(message, user_id)
        await manager.broadcast(message)

        # Disconnect
        await manager.disconnect(conn_id)

        # Cleanup
        await manager.close()
    """

    def __init__(self, config: Optional[ConnectionConfig] = None):
        """
        Initialize connection manager.

        Args:
            config: Optional configuration, uses defaults if not provided
        """
        self.config = config or ConnectionConfig()

        # Local connection storage
        self._active_connections: Dict[str, WebSocketProtocol] = {}
        self._user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self._connection_users: Dict[str, str] = {}  # connection_id -> user_id

        # Redis client (initialized in initialize())
        self._redis: Optional[Any] = None

    async def initialize(self) -> None:
        """
        Initialize Redis connection if configured.

        Call this before accepting connections if using Redis.
        """
        if self.config.redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(
                    self.config.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=self.config.max_redis_connections,
                )
                logger.info("ConnectionManager initialized with Redis")
            except ImportError:
                logger.warning("aioredis not installed, using in-memory storage")
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {e}")
                raise

    async def close(self) -> None:
        """Close Redis connection and cleanup."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def connect(
        self,
        websocket: WebSocketProtocol,
        token: Optional[str] = None,
        authenticator: Optional[AuthenticatorProtocol] = None,
        connection_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> tuple:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket instance
            token: Optional authentication token
            authenticator: Optional token authenticator
            connection_id: Optional existing connection ID for reconnection
            user_id: Optional user_id (if already authenticated elsewhere)

        Returns:
            Tuple of (connection_id, user_id)

        Raises:
            ValueError: If authentication fails
        """
        # Authenticate if token and authenticator provided
        if token and authenticator:
            user_id = await authenticator.authenticate(token)
            if not user_id:
                await websocket.close(code=1008, reason="Authentication failed")
                raise ValueError("Authentication failed")

        # Use anonymous if no authentication
        if not user_id:
            user_id = f"anonymous:{uuid.uuid4().hex[:8]}"

        # Accept connection
        await websocket.accept()

        # Generate or reuse connection ID
        if not connection_id:
            connection_id = str(uuid.uuid4())

        # Store connection locally
        self._active_connections[connection_id] = websocket
        self._connection_users[connection_id] = user_id

        # Track user connections
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(connection_id)

        # Store in Redis if available
        await self._store_connection_in_redis(connection_id, user_id)

        logger.info(
            f"WebSocket connected: connection_id={connection_id}, "
            f"user_id={user_id}, total_connections={len(self._active_connections)}"
        )

        return connection_id, user_id

    async def disconnect(self, connection_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            connection_id: Connection identifier
        """
        # Remove from local storage
        websocket = self._active_connections.pop(connection_id, None)
        user_id = self._connection_users.pop(connection_id, None)

        # Remove from user_connections
        if user_id and user_id in self._user_connections:
            self._user_connections[user_id].discard(connection_id)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

        # Remove from Redis
        await self._remove_connection_from_redis(connection_id)

        # Close WebSocket
        if websocket:
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing websocket {connection_id}: {e}")

        logger.info(
            f"WebSocket disconnected: connection_id={connection_id}, "
            f"user_id={user_id}, remaining={len(self._active_connections)}"
        )

    async def send_personal_message(
        self,
        message: WSMessage,
        connection_id: str
    ) -> bool:
        """
        Send message to specific connection.

        Args:
            message: Message to send
            connection_id: Target connection ID

        Returns:
            True if sent successfully, False otherwise
        """
        websocket = self._active_connections.get(connection_id)
        if not websocket:
            return False

        try:
            await websocket.send_json(message.to_dict())
            return True
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.disconnect(connection_id)
        return False

    async def send_to_user(
        self,
        message: WSMessage,
        user_id: str
    ) -> int:
        """
        Send message to all connections of a user.

        Args:
            message: Message to send
            user_id: Target user ID

        Returns:
            Number of connections message was sent to
        """
        connection_ids = self._user_connections.get(user_id, set())
        sent_count = 0

        for connection_id in list(connection_ids):
            if await self.send_personal_message(message, connection_id):
                sent_count += 1

        return sent_count

    async def broadcast(self, message: WSMessage) -> int:
        """
        Broadcast message to all active connections.

        Args:
            message: Message to broadcast

        Returns:
            Number of connections message was sent to
        """
        message_dict = message.to_dict()
        disconnected = []
        sent_count = 0

        for connection_id, websocket in list(self._active_connections.items()):
            try:
                await websocket.send_json(message_dict)
                sent_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)

        # Clean up disconnected
        for connection_id in disconnected:
            await self.disconnect(connection_id)

        return sent_count

    def get_user_id(self, connection_id: str) -> Optional[str]:
        """
        Get user ID for a connection.

        Args:
            connection_id: Connection identifier

        Returns:
            user_id or None
        """
        return self._connection_users.get(connection_id)

    def get_user_connections(self, user_id: str) -> Set[str]:
        """
        Get all connection IDs for a user.

        Args:
            user_id: User identifier

        Returns:
            Set of connection IDs
        """
        return self._user_connections.get(user_id, set()).copy()

    @property
    def connection_count(self) -> int:
        """Get total active connection count (local)."""
        return len(self._active_connections)

    @property
    def user_count(self) -> int:
        """Get total unique user count (local)."""
        return len(self._user_connections)

    async def get_global_connection_count(self) -> int:
        """
        Get total connection count across all workers (via Redis).

        Returns:
            Total connection count
        """
        if self._redis:
            keys = await self._redis.keys("ws:connection:*")
            return len(keys)
        return self.connection_count

    async def _store_connection_in_redis(
        self,
        connection_id: str,
        user_id: str
    ) -> None:
        """Store connection metadata in Redis."""
        if self._redis:
            key = f"ws:connection:{connection_id}"
            await self._redis.hset(
                key,
                mapping={
                    "user_id": user_id,
                    "connected_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            await self._redis.expire(key, self.config.connection_ttl)

            # Add to user's connection set
            user_set_key = f"ws:user:{user_id}:connections"
            await self._redis.sadd(user_set_key, connection_id)
            await self._redis.expire(user_set_key, self.config.connection_ttl)

    async def _remove_connection_from_redis(self, connection_id: str) -> None:
        """Remove connection from Redis."""
        if self._redis:
            key = f"ws:connection:{connection_id}"
            user_id = await self._redis.hget(key, "user_id")

            await self._redis.delete(key)

            if user_id:
                user_set_key = f"ws:user:{user_id}:connections"
                await self._redis.srem(user_set_key, connection_id)

    async def refresh_connection_ttl(self, connection_id: str) -> None:
        """
        Refresh connection TTL in Redis (called by heartbeat).

        Args:
            connection_id: Connection to refresh
        """
        if self._redis:
            key = f"ws:connection:{connection_id}"
            await self._redis.expire(key, self.config.connection_ttl)

            user_id = await self._redis.hget(key, "user_id")
            if user_id:
                user_set_key = f"ws:user:{user_id}:connections"
                await self._redis.expire(user_set_key, self.config.connection_ttl)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.

        Returns:
            Dictionary with connection stats
        """
        return {
            "total_connections": self.connection_count,
            "total_users": self.user_count,
            "connections_per_user": {
                user_id: len(conn_ids)
                for user_id, conn_ids in self._user_connections.items()
            },
            "redis_enabled": self._redis is not None,
        }
