"""
WebSocket Manager Component

Production-ready WebSocket connection management with room support,
broadcasting, and optional Redis pub/sub for horizontal scaling.

Features:
- Connection lifecycle management with user tracking
- Room-based subscriptions for targeted messaging
- Broadcast to all/room/user patterns
- Redis pub/sub for multi-instance scaling (45-50k connections target)
- Heartbeat/ping-pong with automatic stale connection cleanup
- Message type safety with dataclass-based schemas

References:
- https://fastapi.tiangolo.com/advanced/websockets/
- https://github.com/encode/broadcaster

Example:
    from library.components.realtime.websocket_manager import (
        ConnectionManager,
        DistributedWebSocketManager,
        RedisPubSub,
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
            manager.disconnect(websocket)
"""

from .manager import (
    ConnectionManager,
    DistributedWebSocketManager,
    RedisBroadcaster,
    Connection,
    Message,
    MessageType,
)
from .connection_manager import (
    ConnectionManager as AuthConnectionManager,
    ConnectionConfig,
    WebSocketProtocol,
    AuthenticatorProtocol,
)
from .heartbeat import HeartbeatManager
from .message_types import (
    WSMessage,
    BaseMessageType,
    PingMessage,
    PongMessage,
    ErrorMessage,
    AckMessage,
)
from .redis_pubsub import RedisPubSub

__all__ = [
    # Room-based manager (from manager.py)
    "ConnectionManager",
    "DistributedWebSocketManager",
    "RedisBroadcaster",
    "Connection",
    "Message",
    "MessageType",
    # Auth-enabled manager (from connection_manager.py)
    "AuthConnectionManager",
    "ConnectionConfig",
    "WebSocketProtocol",
    "AuthenticatorProtocol",
    # Heartbeat
    "HeartbeatManager",
    # Message types
    "WSMessage",
    "BaseMessageType",
    "PingMessage",
    "PongMessage",
    "ErrorMessage",
    "AckMessage",
    # Redis pub/sub
    "RedisPubSub",
]
