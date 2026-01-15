"""
PostgreSQL Async Connection Pool with SQLAlchemy.

LEGO Component: database/connection-pool
Purpose: Production-grade async connection pooling with retry logic

Configuration (Environment Variables):
    DATABASE_URL: PostgreSQL connection URL (required for postgres)
    DB_POOL_SIZE: Connection pool size (default: 5)
    DB_POOL_MAX_OVERFLOW: Max overflow connections (default: 10)
    DB_POOL_TIMEOUT: Pool timeout in seconds (default: 30)
    DB_POOL_RECYCLE: Connection recycle time in seconds (default: 1800)
    DB_ECHO: Enable SQL query logging (default: false)
    DB_RETRY_ATTEMPTS: Number of retry attempts (default: 3)
    DB_RETRY_DELAY: Delay between retries in seconds (default: 1.0)

Usage:
    from pool import ConnectionPool, get_db

    # Initialize pool (call once at startup)
    pool = ConnectionPool()
    await pool.initialize()

    # Use in FastAPI
    @app.get("/items")
    async def get_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()

    # Cleanup on shutdown
    await pool.close()
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Any, Callable, TypeVar
from functools import wraps

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import text, event
from sqlalchemy.exc import SQLAlchemyError, OperationalError

logger = logging.getLogger(__name__)

# Type variable for retry decorator
T = TypeVar("T")

# Base class for ORM models
Base = declarative_base()


def get_env_bool(key: str, default: bool = False) -> bool:
    """Parse boolean from environment variable."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_env_int(key: str, default: int) -> int:
    """Parse integer from environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_env_float(key: str, default: float) -> float:
    """Parse float from environment variable."""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


class PoolConfig:
    """Configuration for the connection pool."""

    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: Optional[int] = None,
        max_overflow: Optional[int] = None,
        pool_timeout: Optional[int] = None,
        pool_recycle: Optional[int] = None,
        echo: Optional[bool] = None,
        retry_attempts: Optional[int] = None,
        retry_delay: Optional[float] = None,
    ):
        self.database_url = database_url or os.getenv("DATABASE_URL", "")
        self.pool_size = pool_size or get_env_int("DB_POOL_SIZE", 5)
        self.max_overflow = max_overflow or get_env_int("DB_POOL_MAX_OVERFLOW", 10)
        self.pool_timeout = pool_timeout or get_env_int("DB_POOL_TIMEOUT", 30)
        self.pool_recycle = pool_recycle or get_env_int("DB_POOL_RECYCLE", 1800)
        self.echo = echo if echo is not None else get_env_bool("DB_ECHO", False)
        self.retry_attempts = retry_attempts or get_env_int("DB_RETRY_ATTEMPTS", 3)
        self.retry_delay = retry_delay or get_env_float("DB_RETRY_DELAY", 1.0)

    def get_async_url(self) -> str:
        """Convert standard PostgreSQL URL to async format."""
        url = self.database_url
        if not url:
            raise ValueError("DATABASE_URL environment variable not set")

        # Handle Railway/Heroku postgres:// format
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return url


def with_retry(
    attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (OperationalError,),
) -> Callable:
    """Decorator for retry logic on database operations."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None

            for attempt in range(1, attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt >= attempts:
                        logger.error(
                            f"Database operation failed after {attempts} attempts: {e}"
                        )
                        break
                    logger.warning(
                        f"Database operation failed (attempt {attempt}/{attempts}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay * attempt)  # Exponential backoff

            raise last_exception  # type: ignore

        return wrapper

    return decorator


class ConnectionPool:
    """
    Async PostgreSQL connection pool using SQLAlchemy 2.0+.

    Features:
    - Connection pooling with configurable size
    - Automatic retry logic with exponential backoff
    - Query logging (configurable)
    - Health check support
    - Graceful shutdown
    """

    _instance: Optional["ConnectionPool"] = None
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    def __new__(cls, config: Optional[PoolConfig] = None) -> "ConnectionPool":
        """Singleton pattern for connection pool."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[PoolConfig] = None):
        if self._initialized:
            return

        self.config = config or PoolConfig()
        self._initialized = False
        self._query_count = 0
        self._error_count = 0

    async def initialize(self) -> None:
        """Initialize the connection pool and engine."""
        if self._initialized:
            logger.info("Connection pool already initialized")
            return

        try:
            database_url = self.config.get_async_url()
            logger.info(f"Initializing connection pool: {database_url[:30]}...")

            self._engine = create_async_engine(
                database_url,
                echo=self.config.echo,
                future=True,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                pool_pre_ping=True,  # Enable connection health check
            )

            # Set up query logging event
            if self.config.echo:
                self._setup_query_logging()

            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            # Verify connection
            await self._verify_connection()

            self._initialized = True
            logger.info("Connection pool initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def _setup_query_logging(self) -> None:
        """Set up SQLAlchemy event listeners for query logging."""

        @event.listens_for(self._engine.sync_engine, "before_cursor_execute")
        def log_query(conn, cursor, statement, parameters, context, executemany):
            self._query_count += 1
            logger.debug(f"Query #{self._query_count}: {statement[:100]}...")

    @with_retry(attempts=3, delay=1.0)
    async def _verify_connection(self) -> None:
        """Verify database connection is working."""
        async with self._engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")

    @property
    def engine(self) -> AsyncEngine:
        """Get the async engine."""
        if self._engine is None:
            raise RuntimeError("Connection pool not initialized. Call initialize() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory."""
        if self._session_factory is None:
            raise RuntimeError("Connection pool not initialized. Call initialize() first.")
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for database sessions with automatic retry.

        Usage:
            async with pool.session() as session:
                result = await session.execute(select(User))
        """
        if not self._initialized:
            await self.initialize()

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except SQLAlchemyError as e:
                self._error_count += 1
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()

    async def execute_with_retry(
        self,
        statement: Any,
        params: Optional[dict] = None,
    ) -> Any:
        """
        Execute a statement with automatic retry logic.

        Args:
            statement: SQLAlchemy statement or raw SQL text
            params: Optional parameters for the statement

        Returns:
            Result of the execution
        """
        @with_retry(
            attempts=self.config.retry_attempts,
            delay=self.config.retry_delay,
        )
        async def _execute():
            async with self.session() as session:
                if params:
                    result = await session.execute(statement, params)
                else:
                    result = await session.execute(statement)
                return result

        return await _execute()

    def get_stats(self) -> dict:
        """Get connection pool statistics."""
        if self._engine is None:
            return {"initialized": False}

        pool = self._engine.pool
        return {
            "initialized": True,
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalidatedcount() if hasattr(pool, 'invalidatedcount') else 0,
            "query_count": self._query_count,
            "error_count": self._error_count,
        }

    async def close(self) -> None:
        """Close the connection pool and dispose of the engine."""
        if self._engine is not None:
            logger.info("Closing connection pool...")
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._initialized = False
            logger.info("Connection pool closed")


# Global pool instance
_pool: Optional[ConnectionPool] = None


def get_pool() -> ConnectionPool:
    """Get the global connection pool instance."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool()
    return _pool


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    pool = get_pool()
    async with pool.session() as session:
        yield session


async def init_pool(config: Optional[PoolConfig] = None) -> ConnectionPool:
    """Initialize the global connection pool."""
    global _pool
    _pool = ConnectionPool(config)
    await _pool.initialize()
    return _pool


async def close_pool() -> None:
    """Close the global connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
