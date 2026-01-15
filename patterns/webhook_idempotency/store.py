"""
Idempotency Store - Storage backends for idempotency keys and cached responses.

Provides multiple backends:
- InMemoryIdempotencyStore: For development/testing
- RedisIdempotencyStore: For production (requires redis)
- PostgresIdempotencyStore: For production (requires asyncpg/sqlalchemy)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


@dataclass
class CachedResponse:
    """Cached response from a previous request."""
    status_code: int
    body: str
    headers: Dict[str, str]
    processed_at: str
    idempotency_key: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CachedResponse":
        return cls(**data)


class IdempotencyStore(ABC):
    """
    Abstract base for idempotency storage.

    All implementations must provide async get/set/exists/delete operations.
    Keys should automatically expire after the TTL.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[CachedResponse]:
        """
        Get cached response for key, or None if not found/expired.

        Args:
            key: Idempotency key

        Returns:
            CachedResponse if found and not expired, None otherwise
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        response: CachedResponse,
        ttl_seconds: int = 86400
    ) -> None:
        """
        Store response with TTL.

        Args:
            key: Idempotency key
            response: Response to cache
            ttl_seconds: Time to live in seconds (default: 24 hours)
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists and is not expired.

        Args:
            key: Idempotency key

        Returns:
            True if key exists, False otherwise
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a key.

        Args:
            key: Idempotency key

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def acquire_lock(self, key: str, timeout_seconds: int = 30) -> bool:
        """
        Acquire a lock for processing a key (prevents race conditions).

        Args:
            key: Idempotency key
            timeout_seconds: How long to hold the lock

        Returns:
            True if lock acquired, False if already locked
        """
        pass

    @abstractmethod
    async def release_lock(self, key: str) -> None:
        """
        Release a processing lock.

        Args:
            key: Idempotency key
        """
        pass


class InMemoryIdempotencyStore(IdempotencyStore):
    """
    Simple in-memory store for development/testing.

    WARNING: This store is NOT suitable for production:
    - Data is lost on restart
    - No distributed locking
    - Memory grows unbounded without cleanup

    For production, use RedisIdempotencyStore or PostgresIdempotencyStore.
    """

    def __init__(self):
        self._store: Dict[str, tuple[CachedResponse, datetime]] = {}
        self._locks: Dict[str, datetime] = {}

    async def get(self, key: str) -> Optional[CachedResponse]:
        """Get cached response, respecting TTL."""
        if key not in self._store:
            return None

        response, expires_at = self._store[key]
        if datetime.utcnow() > expires_at:
            # Expired - clean up
            del self._store[key]
            return None

        logger.debug(f"Cache hit for key: {key[:16]}...")
        return response

    async def set(
        self,
        key: str,
        response: CachedResponse,
        ttl_seconds: int = 86400
    ) -> None:
        """Store response with TTL."""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._store[key] = (response, expires_at)
        logger.debug(f"Cached response for key: {key[:16]}... (TTL: {ttl_seconds}s)")

    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return await self.get(key) is not None

    async def delete(self, key: str) -> bool:
        """Delete a key."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    async def acquire_lock(self, key: str, timeout_seconds: int = 30) -> bool:
        """Acquire a processing lock (simple in-memory version)."""
        lock_key = f"lock:{key}"
        now = datetime.utcnow()

        # Check if lock exists and is still valid
        if lock_key in self._locks:
            lock_expires = self._locks[lock_key]
            if now < lock_expires:
                return False  # Lock held by another process
            # Lock expired, we can take it

        # Acquire lock
        self._locks[lock_key] = now + timedelta(seconds=timeout_seconds)
        return True

    async def release_lock(self, key: str) -> None:
        """Release a processing lock."""
        lock_key = f"lock:{key}"
        if lock_key in self._locks:
            del self._locks[lock_key]

    async def cleanup_expired(self) -> int:
        """
        Remove expired entries. Call periodically to prevent memory growth.

        Returns:
            Number of entries removed
        """
        now = datetime.utcnow()
        expired_keys = [
            key for key, (_, expires_at) in self._store.items()
            if now > expires_at
        ]
        for key in expired_keys:
            del self._store[key]

        # Also clean expired locks
        expired_locks = [
            key for key, expires_at in self._locks.items()
            if now > expires_at
        ]
        for key in expired_locks:
            del self._locks[key]

        return len(expired_keys)


class RedisIdempotencyStore(IdempotencyStore):
    """
    Redis-based store for production use.

    Requires: redis (pip install redis)

    Features:
    - Automatic TTL expiration
    - Distributed locking with SETNX
    - Suitable for multi-process/multi-server deployments
    """

    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "idem:"):
        """
        Initialize Redis store.

        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for namespacing
        """
        try:
            import redis.asyncio as redis
        except ImportError:
            raise ImportError("redis package required: pip install redis")

        self._redis = redis.from_url(redis_url, decode_responses=True)
        self._prefix = prefix

    def _key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Optional[CachedResponse]:
        """Get cached response from Redis."""
        data = await self._redis.get(self._key(key))
        if data is None:
            return None

        try:
            return CachedResponse.from_dict(json.loads(data))
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to deserialize cached response: {e}")
            return None

    async def set(
        self,
        key: str,
        response: CachedResponse,
        ttl_seconds: int = 86400
    ) -> None:
        """Store response in Redis with TTL."""
        data = json.dumps(response.to_dict())
        await self._redis.setex(self._key(key), ttl_seconds, data)

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        return await self._redis.exists(self._key(key)) > 0

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        return await self._redis.delete(self._key(key)) > 0

    async def acquire_lock(self, key: str, timeout_seconds: int = 30) -> bool:
        """Acquire distributed lock using SETNX."""
        lock_key = f"{self._prefix}lock:{key}"
        acquired = await self._redis.set(
            lock_key,
            "locked",
            nx=True,  # Only set if not exists
            ex=timeout_seconds
        )
        return acquired is not None

    async def release_lock(self, key: str) -> None:
        """Release distributed lock."""
        lock_key = f"{self._prefix}lock:{key}"
        await self._redis.delete(lock_key)


class PostgresIdempotencyStore(IdempotencyStore):
    """
    PostgreSQL-based store for production use.

    Requires: asyncpg (pip install asyncpg)

    Features:
    - Durable storage
    - Automatic cleanup via scheduled task or trigger
    - Advisory locks for distributed locking

    Schema:
    CREATE TABLE idempotency_keys (
        key VARCHAR(255) PRIMARY KEY,
        response JSONB NOT NULL,
        expires_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    CREATE INDEX idx_idempotency_expires ON idempotency_keys(expires_at);
    """

    def __init__(self, connection_string: str, table_name: str = "idempotency_keys"):
        """
        Initialize PostgreSQL store.

        Args:
            connection_string: PostgreSQL connection string
            table_name: Table name for storing keys
        """
        self._connection_string = connection_string
        self._table = table_name
        self._pool = None

    async def _get_pool(self):
        """Lazy-initialize connection pool."""
        if self._pool is None:
            try:
                import asyncpg
            except ImportError:
                raise ImportError("asyncpg package required: pip install asyncpg")

            self._pool = await asyncpg.create_pool(self._connection_string)
        return self._pool

    async def get(self, key: str) -> Optional[CachedResponse]:
        """Get cached response from PostgreSQL."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT response FROM {self._table}
                WHERE key = $1 AND expires_at > NOW()
                """,
                key
            )
            if row is None:
                return None
            return CachedResponse.from_dict(row['response'])

    async def set(
        self,
        key: str,
        response: CachedResponse,
        ttl_seconds: int = 86400
    ) -> None:
        """Store response in PostgreSQL with TTL."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {self._table} (key, response, expires_at)
                VALUES ($1, $2, NOW() + INTERVAL '{ttl_seconds} seconds')
                ON CONFLICT (key) DO UPDATE SET
                    response = EXCLUDED.response,
                    expires_at = EXCLUDED.expires_at
                """,
                key,
                json.dumps(response.to_dict())
            )

    async def exists(self, key: str) -> bool:
        """Check if key exists in PostgreSQL."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT 1 FROM {self._table}
                WHERE key = $1 AND expires_at > NOW()
                """,
                key
            )
            return row is not None

    async def delete(self, key: str) -> bool:
        """Delete key from PostgreSQL."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self._table} WHERE key = $1",
                key
            )
            return result.split()[-1] != '0'

    async def acquire_lock(self, key: str, timeout_seconds: int = 30) -> bool:
        """Acquire advisory lock in PostgreSQL."""
        pool = await self._get_pool()
        # Use hash of key as lock ID (advisory locks use bigint)
        lock_id = int(hashlib.md5(key.encode()).hexdigest()[:15], 16)

        async with pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT pg_try_advisory_lock($1)",
                lock_id
            )
            return result

    async def release_lock(self, key: str) -> None:
        """Release advisory lock in PostgreSQL."""
        pool = await self._get_pool()
        lock_id = int(hashlib.md5(key.encode()).hexdigest()[:15], 16)

        async with pool.acquire() as conn:
            await conn.execute(
                "SELECT pg_advisory_unlock($1)",
                lock_id
            )

    async def cleanup_expired(self) -> int:
        """
        Remove expired entries from PostgreSQL.

        Returns:
            Number of entries removed
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self._table} WHERE expires_at < NOW()"
            )
            count = int(result.split()[-1])
            if count > 0:
                logger.info(f"Cleaned up {count} expired idempotency keys")
            return count
