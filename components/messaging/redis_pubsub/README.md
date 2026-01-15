# Redis Pub/Sub Component

Redis-based publish/subscribe messaging for real-time event distribution.

## Features

- Async pub/sub operations
- Channel pattern subscriptions
- Message serialization (JSON)
- Connection pooling
- Automatic reconnection

## Usage

```python
import asyncio
from redis_pubsub import RedisPubSub, PubSubConfig

async def main():
    # Configure
    config = PubSubConfig(
        redis_url="redis://localhost:6379",
        channel_prefix="app:"
    )

    pubsub = RedisPubSub(config)
    await pubsub.connect()

    # Subscribe to channels
    async def message_handler(channel: str, message: dict):
        print(f"Received on {channel}: {message}")

    await pubsub.subscribe("events", message_handler)
    await pubsub.subscribe("notifications", message_handler)

    # Pattern subscription
    await pubsub.psubscribe("user:*", message_handler)

    # Publish messages
    await pubsub.publish("events", {"type": "user_login", "user_id": "123"})
    await pubsub.publish("notifications", {"title": "Welcome!", "body": "..."})
    await pubsub.publish("user:123", {"action": "profile_update"})

    # Cleanup
    await pubsub.disconnect()

asyncio.run(main())
```

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| redis_url | str | required | Redis connection URL |
| channel_prefix | str | "" | Prefix for all channels |
| max_retries | int | 3 | Reconnection attempts |
| retry_delay | float | 1.0 | Delay between retries |

## Message Format

Messages are automatically serialized to JSON:

```python
# Publishing
await pubsub.publish("channel", {"key": "value"})

# Receiving
async def handler(channel: str, message: dict):
    # message is already deserialized
    print(message["key"])  # "value"
```
