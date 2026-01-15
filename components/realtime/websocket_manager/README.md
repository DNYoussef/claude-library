# WebSocket Manager Component

Production-ready WebSocket connection management with room support, broadcasting, and optional Redis pub/sub for horizontal scaling.

## Features

- Connection lifecycle management
- Room-based subscriptions
- Broadcast to all/room/user
- Redis pub/sub for multi-instance scaling
- Message type support (text, JSON, bytes)
- Graceful disconnect handling

## Usage

### Basic Connection Manager

```python
from library.components.realtime.websocket_manager import ConnectionManager

manager = ConnectionManager()

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str):
    # Accept and register connection
    connection = await manager.connect(websocket, room_id, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast to room (excluding sender)
            await manager.broadcast_to_room(
                room_id,
                data,
                exclude={connection.connection_id}
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### Room Management

```python
# Join additional rooms
await manager.join_room(websocket, "announcements")

# Leave room
await manager.leave_room(websocket, "chat")

# Get room members
members = manager.get_room_members("chat")
print(f"{len(members)} users in chat")

# Get user's connections (multi-device)
connections = manager.get_user_connections("user123")
```

### Broadcasting

```python
# Broadcast to everyone
await manager.broadcast("Server maintenance in 5 minutes")

# Broadcast to room
await manager.broadcast_to_room("announcements", "New feature released!")

# Send to specific user (all their devices)
await manager.send_to_user("user123", "You have a new message")

# Send JSON
await manager.send_personal(
    websocket,
    '{"type": "notification", "count": 5}',
    MessageType.JSON
)
```

### Distributed Setup (Redis)

For horizontal scaling across multiple server instances:

```python
from library.components.realtime.websocket_manager import (
    DistributedWebSocketManager,
)

# Use distributed manager
manager = DistributedWebSocketManager("redis://localhost:6379")

@app.on_event("startup")
async def startup():
    await manager.start()

@app.on_event("shutdown")
async def shutdown():
    await manager.stop()

# Broadcasting now works across all instances
await manager.broadcast_to_room("global", "Hello from any server!")
```

## API Reference

### ConnectionManager

Central connection registry for single-instance deployments.

```python
manager = ConnectionManager()

# Properties
manager.active_connections  # int: Number of active connections
manager.active_rooms        # List[str]: Active room IDs

# Methods
await manager.connect(websocket, room?, user_id?, metadata?) -> Connection
manager.disconnect(websocket) -> Optional[Connection]
await manager.join_room(websocket, room) -> bool
await manager.leave_room(websocket, room) -> bool
await manager.send_personal(websocket, message, type?)
await manager.send_to_user(user_id, message, type?)
await manager.broadcast(message, type?, exclude?)
await manager.broadcast_to_room(room, message, type?, exclude?)
manager.get_room_members(room) -> List[Connection]
manager.get_user_connections(user_id) -> List[Connection]
```

### DistributedWebSocketManager

Extends ConnectionManager with Redis pub/sub for horizontal scaling.

```python
manager = DistributedWebSocketManager("redis://localhost:6379")
await manager.start()
# ... use like ConnectionManager
await manager.stop()
```

### Connection

```python
@dataclass
class Connection:
    websocket: Any           # WebSocket instance
    user_id: Optional[str]   # User identifier
    rooms: Set[str]          # Rooms joined
    connected_at: datetime   # Connection time
    metadata: Dict[str, Any] # Custom metadata
    connection_id: str       # Unique ID (property)
```

### MessageType

```python
class MessageType(Enum):
    TEXT = "text"
    JSON = "json"
    BYTES = "bytes"
    PING = "ping"
    PONG = "pong"
    CLOSE = "close"
```

## Sources

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [encode/broadcaster](https://github.com/encode/broadcaster)
- [fastapi-distributed-websocket](https://libraries.io/pypi/fastapi-distributed-websocket)
