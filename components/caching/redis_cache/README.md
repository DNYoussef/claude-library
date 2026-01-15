# Redis Cache Library Component

A reusable async Redis caching solution with TTL support, automatic invalidation, and decorator-based endpoint caching.

## Source

Extracted from: `D:\Projects\life-os-dashboard\backend\app\optimizations\redis_cache.py`

## Features

- **TTL-based caching** with configurable defaults
- **Automatic cache invalidation** on write operations
- **Cache key hashing** for query parameters (deterministic, sorted)
- **Performance metrics** tracking (hits, misses, hit rate)
- **Connection pool management** with configurable limits
- **Decorator-based caching** for clean integration
- **Context manager support** for automatic cleanup
- **Global key prefix** support for multi-tenant scenarios

## Installation

### Dependencies

```bash
pip install redis>=4.5.0
```

### Copy to Project

```bash
cp -r redis-cache/ your-project/lib/caching/
```

## Quick Start

### Basic Usage

```python
from redis_cache import RedisCache, RedisCacheConfig

# Configure
config = RedisCacheConfig(
    url="redis://localhost:6379",
    default_ttl=300,  # 5 minutes
    max_connections=50,
    key_prefix="myapp"  # Optional global prefix
)

# Connect
cache = RedisCache(config)
await cache.connect()

# Set/Get
await cache.set("user:123", {"name": "John", "email": "john@example.com"})
user = await cache.get("user:123")  # Returns dict or None

# Delete
await cache.delete("user:123")

# Pattern invalidation
await cache.invalidate("user:*")  # Deletes all user:* keys

# Stats
stats = await cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1f}%")

# Cleanup
await cache.close()
```

### Context Manager

```python
async with RedisCache(config) as cache:
    await cache.set("key", "value")
    result = await cache.get("key")
# Automatically closes on exit
```

### Decorator-Based Caching

```python
from redis_cache import RedisCache, RedisCacheConfig, cached, invalidate_on_write

cache = RedisCache(RedisCacheConfig())
await cache.connect()

# Cache function results
@cached(cache, "users", ttl=600, key_params=["user_id"])
async def get_user(user_id: int, include_details: bool = False):
    """Only user_id affects cache key, not include_details"""
    return await db.get_user(user_id, include_details)

# Auto-invalidate on writes
@invalidate_on_write(cache, "users")
async def update_user(user_id: int, data: dict):
    """Clears all users:* cache entries after update"""
    return await db.update_user(user_id, data)
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from redis_cache import RedisCache, RedisCacheConfig, cached, invalidate_on_write

cache = RedisCache(RedisCacheConfig(url="redis://redis:6379"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache.connect()
    yield
    await cache.close()

app = FastAPI(lifespan=lifespan)

@app.get("/users/{user_id}")
@cached(cache, "users", ttl=300, key_params=["user_id"])
async def get_user(user_id: int):
    return await db.get_user(user_id)

@app.put("/users/{user_id}")
@invalidate_on_write(cache, "users")
async def update_user(user_id: int, data: UserUpdate):
    return await db.update_user(user_id, data.dict())

@app.get("/cache/stats")
async def get_cache_stats():
    return await cache.get_stats()
```

## Configuration Reference

```python
@dataclass
class RedisCacheConfig:
    url: str = "redis://localhost:6379"      # Redis connection URL
    max_connections: int = 50                 # Connection pool size
    socket_timeout: float = 5.0               # Socket timeout (seconds)
    socket_keepalive: bool = True             # TCP keepalive
    default_ttl: int = 300                    # Default TTL (seconds)
    encoding: str = "utf-8"                   # String encoding
    decode_responses: bool = True             # Decode to strings
    key_prefix: str = ""                      # Global key prefix
```

## API Reference

### RedisCache

| Method | Description |
|--------|-------------|
| `connect()` | Initialize connection pool |
| `close()` | Close all connections |
| `get(key)` | Get cached value (JSON parsed) |
| `set(key, value, ttl=None)` | Set value with TTL |
| `delete(key)` | Delete specific key |
| `invalidate(pattern)` | Delete keys matching pattern |
| `exists(key)` | Check if key exists |
| `get_ttl(key)` | Get remaining TTL |
| `get_stats()` | Get cache statistics |

### Decorators

| Decorator | Description |
|-----------|-------------|
| `@cached(cache, prefix, ttl, key_params)` | Cache function results |
| `@invalidate_on_write(cache, prefix)` | Invalidate cache after write |

### Utility Functions

| Function | Description |
|----------|-------------|
| `generate_cache_key(prefix, **kwargs)` | Generate deterministic cache key |
| `init_default_cache(config)` | Initialize module-level cache |
| `close_default_cache()` | Close module-level cache |
| `get_default_cache()` | Get module-level cache instance |

## Cache Key Generation

Keys are generated using SHA256 hashing of sorted parameters:

```python
from redis_cache import generate_cache_key

# Same key regardless of parameter order
key1 = generate_cache_key("tasks", user_id=1, status="active")
key2 = generate_cache_key("tasks", status="active", user_id=1)
assert key1 == key2  # "tasks:a1b2c3d4e5f6g7h8"
```

## Performance Considerations

1. **Connection Pooling**: Default 50 connections, adjust based on load
2. **TTL Strategy**: Set appropriate TTLs to balance freshness vs. performance
3. **Key Patterns**: Use specific patterns for invalidation to avoid clearing unrelated data
4. **Serialization**: Values are JSON serialized; complex objects need `default=str` handling

## Error Handling

All methods handle Redis connection errors gracefully:

```python
# Returns None on error (doesn't raise)
result = await cache.get("key")

# Returns False on error
success = await cache.set("key", "value")

# Returns 0 on error
deleted = await cache.invalidate("pattern:*")

# Returns error dict on failure
stats = await cache.get_stats()
if "error" in stats:
    logger.error(f"Cache error: {stats['error']}")
```

## Testing

```python
import pytest
from redis_cache import RedisCache, RedisCacheConfig

@pytest.fixture
async def cache():
    config = RedisCacheConfig(url="redis://localhost:6379/1")  # Use DB 1 for tests
    cache = RedisCache(config)
    await cache.connect()
    yield cache
    await cache.invalidate("*")  # Cleanup
    await cache.close()

@pytest.mark.asyncio
async def test_set_get(cache):
    await cache.set("test_key", {"foo": "bar"})
    result = await cache.get("test_key")
    assert result == {"foo": "bar"}
```

## Version History

- **1.0.0** - Initial extraction from Life-OS Dashboard
  - Core caching operations (get, set, delete)
  - Pattern-based invalidation
  - Decorator-based caching
  - Connection pool management
  - Performance metrics

## License

MIT - Part of the Context Cascade ecosystem.
