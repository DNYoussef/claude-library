"""
WebSocket Manager Component

Production-ready WebSocket connection management with room support,
broadcasting, and optional Redis pub/sub for horizontal scaling.

Based on:
- FastAPI WebSocket patterns: https://fastapi.tiangolo.com/advanced/websockets/
- encode/broadcaster: https://github.com/encode/broadcaster
- fastapi-distributed-websocket patterns

Features:
- Connection lifecycle management
- Room-based subscriptions
- Broadcast to all/room/user
- Redis pub/sub for multi-instance scaling
- Heartbeat/ping-pong support
- Graceful disconnect handling

Example:
    from library.components.realtime.websocket_manager import (
        WebSocketManager,
        ConnectionManager,
    )

    manager = ConnectionManager()

    @app.websocket("/ws/{room_id}")
    async def websocket_endpoint(websocket: WebSocket, room_id: str):
        await manager.connect(websocket, room_id)
        try:
            while True:
                data = await websocket.receive_text()
                await manager.broadcast_to_room(room_id, data)
        except WebSocketDisconnect:
            manager.disconnect(websocket, room_id)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""
    TEXT = "text"
    JSON = "json"
    BYTES = "bytes"
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"


@dataclass
class Connection:
    """Represents a WebSocket connection."""
    websocket: Any  # WebSocket instance
    user_id: Optional[str] = None
    rooms: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def connection_id(self) -> str:
        """Unique connection identifier."""
        return str(id(self.websocket))


@dataclass
class Message:
    """WebSocket message wrapper."""
    type: MessageType
    data: Any
    sender_id: Optional[str] = None
    room: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_json(self) -> str:
        """Serialize message to JSON."""
        return json.dumps({
            "type": self.type.value,
            "data": self.data,
            "sender_id": self.sender_id,
            "room": self.room,
            "timestamp": self.timestamp.isoformat(),
        })


class ConnectionManager:
    """
    WebSocket connection manager with room support.

    Manages WebSocket connections, rooms, and broadcasting.
    For single-instance deployments.

    Example:
        manager = ConnectionManager()

        async def websocket_handler(websocket, room_id, user_id):
            await manager.connect(websocket, room_id, user_id)
            try:
                async for message in websocket.iter_text():
                    await manager.broadcast_to_room(room_id, message)
            finally:
                manager.disconnect(websocket)
    """

    def __init__(self):
        self._connections: Dict[str, Connection] = {}  # connection_id -> Connection
        self._rooms: Dict[str, Set[str]] = {}  # room_id -> set of connection_ids
        self._users: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self._lock = asyncio.Lock()

    @property
    def active_connections(self) -> int:
        """Number of active connections."""
        return len(self._connections)

    @property
    def active_rooms(self) -> List[str]:
        """List of active room IDs."""
        return list(self._rooms.keys())

    async def connect(
        self,
        websocket: Any,
        room: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Connection:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket instance
            room: Optional room to join immediately
            user_id: Optional user identifier
            metadata: Optional connection metadata

        Returns:
            Connection object
        """
        await websocket.accept()

        connection = Connection(
            websocket=websocket,
            user_id=user_id,
            metadata=metadata or {},
        )

        async with self._lock:
            self._connections[connection.connection_id] = connection

            if user_id:
                self._users.setdefault(user_id, set()).add(connection.connection_id)

            if room:
                await self._join_room(connection, room)

        logger.info(
            f"WebSocket connected: {connection.connection_id}, "
            f"user={user_id}, room={room}"
        )
        return connection

    def disconnect(self, websocket: Any) -> Optional[Connection]:
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket instance

        Returns:
            The disconnected Connection object, or None
        """
        connection_id = str(id(websocket))
        connection = self._connections.pop(connection_id, None)

        if not connection:
            return None

        # Remove from all rooms
        for room in list(connection.rooms):
            self._leave_room_sync(connection, room)

        # Remove from user tracking
        if connection.user_id and connection.user_id in self._users:
            self._users[connection.user_id].discard(connection_id)
            if not self._users[connection.user_id]:
                del self._users[connection.user_id]

        logger.info(f"WebSocket disconnected: {connection_id}")

        return connection

    async def join_room(self, websocket: Any, room: str) -> bool:
        """Add connection to a room."""
        connection_id = str(id(websocket))
        connection = self._connections.get(connection_id)

        if connection:
            async with self._lock:
                await self._join_room(connection, room)
            return True
        return False

    async def leave_room(self, websocket: Any, room: str) -> bool:
        """Remove connection from a room."""
        connection_id = str(id(websocket))
        connection = self._connections.get(connection_id)

        if connection:
            async with self._lock:
                self._leave_room_sync(connection, room)
            return True
        return False

    async def _join_room(self, connection: Connection, room: str):
        """Internal: Add connection to room."""
        if room not in self._rooms:
            self._rooms[room] = set()
        self._rooms[room].add(connection.connection_id)
        connection.rooms.add(room)

    def _leave_room_sync(self, connection: Connection, room: str):
        """Internal: Remove connection from room (sync)."""
        if room in self._rooms:
            self._rooms[room].discard(connection.connection_id)
            if not self._rooms[room]:
                del self._rooms[room]
        connection.rooms.discard(room)

    async def send_personal(
        self,
        websocket: Any,
        message: str,
        message_type: MessageType = MessageType.TEXT,
    ):
        """Send message to a specific connection."""
        try:
            if message_type == MessageType.TEXT:
                await websocket.send_text(message)
            elif message_type == MessageType.JSON:
                await websocket.send_json(json.loads(message))
            elif message_type == MessageType.BYTES:
                await websocket.send_bytes(message.encode())
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.disconnect(websocket)

    async def send_to_user(
        self,
        user_id: str,
        message: str,
        message_type: MessageType = MessageType.TEXT,
    ):
        """Send message to all connections of a user."""
        connection_ids = self._users.get(user_id, set())
        tasks = []

        for conn_id in connection_ids:
            connection = self._connections.get(conn_id)
            if connection:
                tasks.append(
                    self.send_personal(
                        connection.websocket, message, message_type
                    )
                )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast(
        self,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        exclude: Optional[Set[str]] = None,
    ):
        """Broadcast message to all connections."""
        exclude = exclude or set()
        tasks = []

        for conn_id, connection in self._connections.items():
            if conn_id not in exclude:
                tasks.append(
                    self.send_personal(
                        connection.websocket, message, message_type
                    )
                )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_to_room(
        self,
        room: str,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        exclude: Optional[Set[str]] = None,
    ):
        """Broadcast message to all connections in a room."""
        exclude = exclude or set()
        connection_ids = self._rooms.get(room, set())
        tasks = []

        for conn_id in connection_ids:
            if conn_id not in exclude:
                connection = self._connections.get(conn_id)
                if connection:
                    tasks.append(
                        self.send_personal(
                            connection.websocket, message, message_type
                        )
                    )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_room_members(self, room: str) -> List[Connection]:
        """Get all connections in a room."""
        connection_ids = self._rooms.get(room, set())
        return [
            self._connections[cid]
            for cid in connection_ids
            if cid in self._connections
        ]

    def get_user_connections(self, user_id: str) -> List[Connection]:
        """Get all connections for a user."""
        connection_ids = self._users.get(user_id, set())
        return [
            self._connections[cid]
            for cid in connection_ids
            if cid in self._connections
        ]


class RedisBroadcaster:
    """
    Redis-backed broadcaster for horizontal scaling.

    Enables WebSocket broadcasting across multiple server instances
    using Redis pub/sub.

    Example:
        broadcaster = RedisBroadcaster("redis://localhost:6379")
        await broadcaster.connect()

        # Subscribe to channel
        async for message in broadcaster.subscribe("chat:room1"):
            await manager.broadcast_to_room("room1", message)

        # Publish message
        await broadcaster.publish("chat:room1", "Hello!")
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis = None
        self._pubsub = None

    async def connect(self):
        """Connect to Redis."""
        try:
            import redis.asyncio as redis
            self._redis = redis.from_url(self.redis_url)
            self._pubsub = self._redis.pubsub()
            logger.info(f"Connected to Redis: {self.redis_url}")
        except ImportError:
            raise ImportError("redis package required: pip install redis")

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()

    async def publish(self, channel: str, message: str):
        """Publish message to a channel."""
        if self._redis:
            await self._redis.publish(channel, message)

    async def subscribe(self, channel: str):
        """Subscribe to a channel and yield messages."""
        if self._pubsub:
            await self._pubsub.subscribe(channel)
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    yield message["data"].decode()

    async def unsubscribe(self, channel: str):
        """Unsubscribe from a channel."""
        if self._pubsub:
            await self._pubsub.unsubscribe(channel)


class DistributedWebSocketManager(ConnectionManager):
    """
    WebSocket manager with Redis pub/sub for horizontal scaling.

    Extends ConnectionManager with cross-instance broadcasting.

    Example:
        manager = DistributedWebSocketManager("redis://localhost:6379")
        await manager.start()

        # This will broadcast to all instances
        await manager.broadcast_to_room("room1", "Hello!")

        await manager.stop()
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        super().__init__()
        self._broadcaster = RedisBroadcaster(redis_url)
        self._subscription_tasks: Dict[str, asyncio.Task] = {}

    async def start(self):
        """Start the distributed manager."""
        await self._broadcaster.connect()

    async def stop(self):
        """Stop the distributed manager."""
        for task in self._subscription_tasks.values():
            task.cancel()
        await self._broadcaster.disconnect()

    async def _join_room(self, connection: Connection, room: str):
        """Join room and subscribe to Redis channel."""
        await super()._join_room(connection, room)

        # Start listening to Redis channel if first connection in room
        if room not in self._subscription_tasks:
            self._subscription_tasks[room] = asyncio.create_task(
                self._listen_to_channel(room)
            )

    async def _listen_to_channel(self, room: str):
        """Listen to Redis channel and broadcast locally."""
        channel = f"ws:room:{room}"
        try:
            async for message in self._broadcaster.subscribe(channel):
                # Broadcast to local connections only
                await super().broadcast_to_room(room, message)
        except asyncio.CancelledError:
            await self._broadcaster.unsubscribe(channel)

    async def broadcast_to_room(
        self,
        room: str,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        exclude: Optional[Set[str]] = None,
    ):
        """Broadcast to room across all instances via Redis."""
        channel = f"ws:room:{room}"
        await self._broadcaster.publish(channel, message)
