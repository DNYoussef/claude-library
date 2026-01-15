"""
WebSocket Manager Component

Production-ready WebSocket connection management with room support,
broadcasting, and optional Redis pub/sub for horizontal scaling.

References:
- https://fastapi.tiangolo.com/advanced/websockets/
- https://github.com/encode/broadcaster

Example:
    from library.components.realtime.websocket_manager import (
        ConnectionManager,
        DistributedWebSocketManager,
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

__all__ = [
    "ConnectionManager",
    "DistributedWebSocketManager",
    "RedisBroadcaster",
    "Connection",
    "Message",
    "MessageType",
]
