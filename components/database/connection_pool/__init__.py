"""
PostgreSQL Async Connection Pool.

LEGO Component: database/connection-pool
Version: 1.0.0

A production-ready async connection pool for PostgreSQL using SQLAlchemy 2.0+.

Features:
- Async connection pooling with configurable size
- Automatic retry logic with exponential backoff
- Connection health checks with latency monitoring
- Query logging (configurable)
- Kubernetes-compatible health endpoints
- Graceful shutdown

Installation:
    pip install sqlalchemy[asyncio] asyncpg

Environment Variables:
    DATABASE_URL: PostgreSQL connection URL
    DB_POOL_SIZE: Pool size (default: 5)
    DB_POOL_MAX_OVERFLOW: Max overflow (default: 10)
    DB_POOL_TIMEOUT: Pool timeout seconds (default: 30)
    DB_POOL_RECYCLE: Connection recycle seconds (default: 1800)
    DB_ECHO: Enable SQL logging (default: false)
    DB_RETRY_ATTEMPTS: Retry attempts (default: 3)
    DB_RETRY_DELAY: Retry delay seconds (default: 1.0)

Quick Start:
    from database.connection_pool import init_pool, get_db, close_pool

    # At startup
    await init_pool()

    # In FastAPI endpoints
    @app.get("/items")
    async def get_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()

    # At shutdown
    await close_pool()
"""

from .pool import (
    ConnectionPool,
    PoolConfig,
    Base,
    get_pool,
    get_db,
    init_pool,
    close_pool,
    with_retry,
)

from .health import (
    DatabaseHealthChecker,
    HealthCheckEndpoint,
    HealthCheckConfig,
    HealthStatus,
    HealthState,
)

__all__ = [
    # Pool
    "ConnectionPool",
    "PoolConfig",
    "Base",
    "get_pool",
    "get_db",
    "init_pool",
    "close_pool",
    "with_retry",
    # Health
    "DatabaseHealthChecker",
    "HealthCheckEndpoint",
    "HealthCheckConfig",
    "HealthStatus",
    "HealthState",
]

__version__ = "1.0.0"
