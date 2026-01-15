"""
Redis Pub/Sub Event Bus - Reusable Library Component

A generalized, async-native Redis Pub/Sub implementation for message
broadcasting across distributed systems.

Quick Start:
    from redis_pubsub import RedisPubSub

    pubsub = RedisPubSub()
    await pubsub.initialize("redis://localhost:6379")

    async def handler(data: dict):
        print(f"Received: {data}")

    await pubsub.subscribe("my:channel", handler)
    await pubsub.publish("my:channel", {"event": "hello"})
    await pubsub.close()

Features:
    - Async/await native using redis.asyncio
    - Automatic reconnection on listener failure
    - Channel and pattern-based subscriptions
    - JSON serialization with fallback for non-serializable types
    - Subscriber count and active channel monitoring
    - Graceful shutdown handling

Requirements:
    - Python 3.8+
    - redis[hiredis] >= 4.0.0

Installation:
    pip install redis[hiredis]

See Also:
    - redis_pubsub.py for full implementation details
    - RedisPubSub class docstring for complete API reference
"""

from .redis_pubsub import (
    RedisPubSub,
    MessageHandler,
    create_redis_pubsub,
)

__all__ = [
    "RedisPubSub",
    "MessageHandler",
    "create_redis_pubsub",
]

__version__ = "1.0.0"
__author__ = "Extracted from Life OS Dashboard"
