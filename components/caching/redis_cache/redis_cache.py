"""
Redis Query Caching Library Component

A reusable async Redis caching solution with:
- TTL-based caching with configurable defaults
- Automatic cache invalidation on writes
- Cache key hashing for query parameters
- Performance metrics tracking
- Connection pool management
- Decorator-based endpoint caching

Extracted from Life-OS Dashboard and generalized for reuse.
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, ParamSpec

import redis.asyncio as redis

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class RedisCacheConfig:
    """
    Configuration for Redis cache client.

    Attributes:
        url: Redis connection URL (default: redis://localhost:6379)
        max_connections: Connection pool size (default: 50)
        socket_timeout: Socket timeout in seconds (default: 5.0)
        socket_keepalive: Enable TCP keepalive (default: True)
        default_ttl: Default TTL for cached items in seconds (default: 300)
        encoding: String encoding (default: utf-8)
        decode_responses: Decode responses to strings (default: True)
        key_prefix: Global prefix for all cache keys (default: "")
    """
    url: str = "redis://localhost:6379"
    max_connections: int = 50
    socket_timeout: float = 5.0
    socket_keepalive: bool = True
    default_ttl: int = 300
    encoding: str = "utf-8"
    decode_responses: bool = True
    key_prefix: str = ""


class RedisCache:
    """
    Async Redis cache client with connection pooling and TTL support.

    Example:
        config = RedisCacheConfig(url="redis://localhost:6379", default_ttl=600)
        cache = RedisCache(config)

        await cache.connect()

        # Basic operations
        await cache.set("my_key", {"data": "value"})
        result = await cache.get("my_key")

        # With custom TTL
        await cache.set("temp_key", "value", ttl=60)

        # Invalidation
        await cache.invalidate("prefix:*")

        await cache.close()
    """

    def __init__(self, config: Optional[RedisCacheConfig] = None) -> None:
        """
        Initialize Redis cache with configuration.

        Args:
            config: RedisCacheConfig instance (uses defaults if None)
        """
        self.config = config or RedisCacheConfig()
        self._client: Optional[redis.Redis] = None
        self._connected: bool = False

    @property
    def client(self) -> Optional[redis.Redis]:
        """Get the underlying Redis client."""
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if Redis client is connected."""
        return self._connected and self._client is not None

    async def connect(self) -> None:
        """
        Initialize Redis client connection pool.

        Raises:
            redis.ConnectionError: If connection fails
        """
        self._client = redis.from_url(
            self.config.url,
            encoding=self.config.encoding,
            decode_responses=self.config.decode_responses,
            max_connections=self.config.max_connections,
            socket_keepalive=self.config.socket_keepalive,
            socket_timeout=self.config.socket_timeout,
        )
        # Verify connection is actually reachable (MED-CACHE-01)
        await self._client.ping()
        self._connected = True
        logger.info(f"Redis cache connected: {self.config.url}")

    async def close(self) -> None:
        """Close Redis client connections."""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Redis cache connections closed")

    async def __aenter__(self) -> "RedisCache":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    def _make_key(self, key: str) -> str:
        """
        Apply global key prefix if configured.

        Args:
            key: Original cache key

        Returns:
            Key with prefix applied
        """
        if self.config.key_prefix:
            return f"{self.config.key_prefix}:{key}"
        return key

    async def get(self, key: str) -> Optional[Any]:
        """
        Get cached value from Redis.

        Args:
            key: Cache key

        Returns:
            Cached value (parsed JSON) or None if not found
        """
        if not self.is_connected:
            return None

        full_key = self._make_key(key)

        try:
            cached_value = await self._client.get(full_key)
            if not cached_value:
                logger.debug(f"Cache MISS: {full_key}")
                return None

            logger.debug(f"Cache HIT: {full_key}")
            return json.loads(cached_value)

        except Exception as e:
            logger.error(f"Redis get error for key {full_key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set cached value in Redis with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (uses config default if None)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False

        full_key = self._make_key(key)
        effective_ttl = ttl if ttl is not None else self.config.default_ttl

        try:
            serialized_value = json.dumps(value, default=str)
            await self._client.setex(full_key, effective_ttl, serialized_value)
            logger.debug(f"Cache SET: {full_key} (TTL: {effective_ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Redis set error for key {full_key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a specific cache key.

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted, False otherwise
        """
        if not self.is_connected:
            return False

        full_key = self._make_key(key)

        try:
            deleted = await self._client.delete(full_key)
            logger.debug(f"Cache DELETE: {full_key} (deleted: {deleted})")
            return deleted > 0

        except Exception as e:
            logger.error(f"Redis delete error for key {full_key}: {e}")
            return False

    async def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.

        Uses SCAN instead of KEYS for production safety (HIGH-CACHE-01).
        KEYS command blocks Redis and can cause issues in production.

        Args:
            pattern: Redis key pattern (e.g., "tasks:*")

        Returns:
            Number of keys deleted
        """
        if not self.is_connected:
            return 0

        full_pattern = self._make_key(pattern)

        try:
            # Use SCAN instead of KEYS for production safety (HIGH-CACHE-01)
            cursor = 0
            deleted_count = 0
            while True:
                cursor, keys = await self._client.scan(cursor, match=full_pattern, count=100)
                if keys:
                    deleted_count += await self._client.delete(*keys)
                if cursor == 0:
                    break

            if deleted_count > 0:
                logger.info(f"Cache INVALIDATE: {full_pattern} ({deleted_count} keys)")
            return deleted_count

        except Exception as e:
            logger.error(f"Redis invalidate error for pattern {full_pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        if not self.is_connected:
            return False

        full_key = self._make_key(key)

        try:
            return await self._client.exists(full_key) > 0

        except Exception as e:
            logger.error(f"Redis exists error for key {full_key}: {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if no TTL, -2 if key doesn't exist
        """
        if not self.is_connected:
            return -2

        full_key = self._make_key(key)

        try:
            return await self._client.ttl(full_key)

        except Exception as e:
            logger.error(f"Redis TTL error for key {full_key}: {e}")
            return -2

    async def get_stats(self) -> dict[str, Any]:
        """
        Get Redis cache statistics.

        Returns:
            Dictionary with cache stats (keys, memory, hit rate)
        """
        if not self.is_connected:
            return {"connected": False, "error": "Redis not connected"}

        try:
            info = await self._client.info("stats")

            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = hits + misses

            return {
                "connected": True,
                "keys": await self._client.dbsize(),
                "hits": hits,
                "misses": misses,
                "hit_rate": (hits / max(1, total)) * 100,
                "memory_used": info.get("used_memory_human", "N/A"),
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"connected": False, "error": str(e)}

    async def reset_stats(self) -> bool:
        """
        Reset Redis cache statistics (LOW-CACHE-01).

        Resets the hit/miss counters by issuing CONFIG RESETSTAT.
        Note: This requires CONFIG permissions on the Redis server.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            return False

        try:
            await self._client.config_resetstat()
            logger.info("Cache statistics reset")
            return True

        except Exception as e:
            logger.error(f"Error resetting cache stats: {e}")
            return False


def generate_cache_key(prefix: str, **kwargs: Any) -> str:
    """
    Generate cache key from prefix and parameters.

    Creates a deterministic hash-based cache key from the provided
    prefix and keyword arguments. Parameters are sorted to ensure
    consistent key generation regardless of argument order.

    Args:
        prefix: Cache key prefix (e.g., "tasks", "projects")
        **kwargs: Query parameters to include in key

    Returns:
        Hashed cache key in format "prefix:hash16"

    Example:
        >>> generate_cache_key("tasks", user_id=1, status="enabled")
        'tasks:a1b2c3d4e5f6g7h8'
    """
    # Sort params for consistent hashing
    sorted_params = sorted(kwargs.items())
    params_str = json.dumps(sorted_params, sort_keys=True)

    # Create SHA256 hash of parameters (16 char truncation)
    params_hash = hashlib.sha256(params_str.encode()).hexdigest()[:16]

    return f"{prefix}:{params_hash}"


def cached(
    cache: RedisCache,
    prefix: str,
    ttl: Optional[int] = None,
    key_params: Optional[list[str]] = None
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for caching async function results.

    Args:
        cache: RedisCache instance
        prefix: Cache key prefix
        ttl: Time-to-live in seconds (uses cache default if None)
        key_params: Specific kwargs to include in cache key (default: all)

    Returns:
        Decorated function with caching behavior

    Example:
        cache = RedisCache(RedisCacheConfig())

        @cached(cache, "users", ttl=300, key_params=["user_id"])
        async def get_user(user_id: int, include_details: bool = False):
            # Only user_id affects cache key, not include_details
            return await db.get_user(user_id, include_details)
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Build cache key from specified params or all kwargs
            if key_params:
                cache_params = {k: v for k, v in kwargs.items() if k in key_params}
            else:
                cache_params = dict(kwargs)

            cache_key = generate_cache_key(prefix, **cache_params)

            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Cache miss - execute function
            result = await func(*args, **kwargs)

            # Cache the result - wrap in try-except for graceful failure (MED-CACHE-02)
            try:
                await cache.set(cache_key, result, ttl)
            except Exception as e:
                logger.warning(f"Cache write failed for key {cache_key}: {e}")
                # Don't break the decorated function - just log and continue

            return result

        return wrapper
    return decorator


def invalidate_on_write(
    cache: RedisCache,
    prefix: str
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for invalidating cache on write operations.

    Automatically invalidates all cache entries matching the prefix
    pattern after the decorated function executes successfully.

    Args:
        cache: RedisCache instance
        prefix: Cache key prefix to invalidate (will match "prefix:*")

    Returns:
        Decorated function with cache invalidation

    Example:
        cache = RedisCache(RedisCacheConfig())

        @invalidate_on_write(cache, "users")
        async def update_user(user_id: int, data: dict):
            # After this completes, all "users:*" cache entries are cleared
            return await db.update_user(user_id, data)
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Execute the write operation
            result = await func(*args, **kwargs)

            # Invalidate related cache entries
            await cache.invalidate(f"{prefix}:*")

            return result

        return wrapper
    return decorator


# Module-level convenience functions for simple usage patterns (HIGH-CACHE-02)
# Thread-safe singleton pattern with asyncio.Lock protection
_default_cache: Optional[RedisCache] = None
_default_cache_lock: asyncio.Lock = asyncio.Lock()


async def init_default_cache(config: Optional[RedisCacheConfig] = None) -> RedisCache:
    """
    Initialize the module-level default cache.

    Thread-safe initialization using asyncio.Lock (HIGH-CACHE-02).

    Args:
        config: RedisCacheConfig instance (uses defaults if None)

    Returns:
        The initialized RedisCache instance
    """
    global _default_cache
    async with _default_cache_lock:
        if _default_cache is not None:
            # Already initialized, return existing instance
            return _default_cache
        _default_cache = RedisCache(config)
        await _default_cache.connect()
        return _default_cache


async def close_default_cache() -> None:
    """
    Close the module-level default cache.

    Thread-safe cleanup using asyncio.Lock (HIGH-CACHE-02).
    """
    global _default_cache
    async with _default_cache_lock:
        if _default_cache:
            await _default_cache.close()
            _default_cache = None


def get_default_cache() -> Optional[RedisCache]:
    """
    Get the module-level default cache instance.

    Note: This is a synchronous getter. For thread-safe initialization,
    use init_default_cache() instead.
    """
    return _default_cache
