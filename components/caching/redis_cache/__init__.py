"""
Redis Cache Library Component

A reusable async Redis caching solution for Python applications.

Quick Start:
    from redis_cache import RedisCache, RedisCacheConfig, cached, invalidate_on_write

    # Configure and connect
    config = RedisCacheConfig(url="redis://localhost:6379", default_ttl=300)
    cache = RedisCache(config)
    await cache.connect()

    # Use decorators for automatic caching
    @cached(cache, "users", ttl=600)
    async def get_user(user_id: int):
        return await db.get_user(user_id)

    @invalidate_on_write(cache, "users")
    async def update_user(user_id: int, data: dict):
        return await db.update_user(user_id, data)

    # Or use direct methods
    await cache.set("my_key", {"data": "value"}, ttl=120)
    result = await cache.get("my_key")

    # Context manager support
    async with RedisCache(config) as cache:
        await cache.set("key", "value")
"""

from .redis_cache import (
    # Core classes
    RedisCache,
    RedisCacheConfig,
    # Decorators
    cached,
    invalidate_on_write,
    # Utility functions
    generate_cache_key,
    # Module-level convenience
    init_default_cache,
    close_default_cache,
    get_default_cache,
)

__all__ = [
    # Core classes
    "RedisCache",
    "RedisCacheConfig",
    # Decorators
    "cached",
    "invalidate_on_write",
    # Utility functions
    "generate_cache_key",
    # Module-level convenience
    "init_default_cache",
    "close_default_cache",
    "get_default_cache",
]

__version__ = "1.0.0"
__author__ = "David Youssef"
__source__ = "Extracted from Life-OS Dashboard"
