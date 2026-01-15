# WebSocket Manager Component

Production-ready WebSocket connection management with room support, broadcasting, and optional Redis pub/sub for horizontal scaling. Designed for 45-50k concurrent connections.

## Features

- Connection lifecycle management with user tracking
- Room-based subscriptions for targeted messaging
- Broadcast to all/room/user patterns
- Redis pub/sub for multi-instance scaling (RedisPubSub class)
- Heartbeat/ping-pong with automatic stale connection cleanup
- JWT authentication support (pluggable authenticator)
- Message type safety with dataclass-based schemas
- Graceful disconnect handling with TTL-based cleanup

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

## Redis Pub/Sub for Multi-Worker

For horizontal scaling across multiple server instances with full pub/sub support:

```python
from library.components.realtime.websocket_manager import RedisPubSub

# Initialize pub/sub
pubsub = RedisPubSub("redis://localhost:6379")
await pubsub.initialize()

# Subscribe to channels
async def handle_broadcast(data: dict):
    await manager.broadcast(data)

await pubsub.subscribe("ws:broadcast", handle_broadcast)
await pubsub.subscribe(f"ws:user:{user_id}", handle_user_message)

# Publish messages
await pubsub.publish_broadcast(message)       # All connections
await pubsub.publish_to_user("user123", msg)  # Specific user
await pubsub.publish_to_room("room1", msg)    # Room subscribers

# Cleanup
await pubsub.close()
```

Channel conventions:
- `ws:broadcast` - All connections across all workers
- `ws:user:{user_id}` - All connections for a specific user
- `ws:connection:{conn_id}` - Single specific connection
- `ws:room:{room_id}` - Room subscribers

## Heartbeat Manager

Monitor connection health with automatic cleanup:

```python
from library.components.realtime.websocket_manager import HeartbeatManager

heartbeat = HeartbeatManager(ping_interval=30, pong_timeout=60)

# Start heartbeat for a connection
heartbeat.start_heartbeat(
    connection_id="conn-123",
    websocket=ws,
    on_disconnect_callback=handle_disconnect
)

# Record pong from client
heartbeat.record_pong("conn-123")

# Check health
is_alive = heartbeat.is_connection_alive("conn-123")
metrics = heartbeat.get_all_health_metrics()

# Stop heartbeat
heartbeat.stop_heartbeat("conn-123")
```

## Message Types

Base message schemas for type-safe WebSocket communication:

```python
from library.components.realtime.websocket_manager import (
    WSMessage, PingMessage, PongMessage, ErrorMessage, AckMessage
)

# Create messages
ping = PingMessage(event_id="uuid-123")
error = ErrorMessage(event_id="uuid-456", error="Invalid request")
ack = AckMessage(event_id="uuid-789", ack_event_id="uuid-123")

# Serialize
json_str = ping.to_json()
data_dict = error.to_dict()

# Parse
msg = WSMessage.from_json(json_str)
```

## Authentication-Enabled Manager

For JWT authentication with pluggable authenticators:

```python
from library.components.realtime.websocket_manager import (
    AuthConnectionManager,
    ConnectionConfig,
)

config = ConnectionConfig(
    redis_url="redis://localhost:6379",
    connection_ttl=3600,
    max_redis_connections=100,
)
manager = AuthConnectionManager(config)
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

# Cleanup
await manager.disconnect(conn_id)
await manager.close()
```

## Production Configuration

### Redis for 45-50k connections

```bash
redis-server --maxmemory 2gb \
             --maxmemory-policy allkeys-lru \
             --maxclients 50000 \
             --tcp-backlog 511
```

### TLS/SSL (Nginx)

```nginx
location /ws {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## Sources

- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [encode/broadcaster](https://github.com/encode/broadcaster)
- [fastapi-distributed-websocket](https://libraries.io/pypi/fastapi-distributed-websocket)
- [Redis Pub/Sub](https://redis.io/topics/pubsub)
- [WebSocket RFC 6455](https://tools.ietf.org/html/rfc6455)
