# PostgreSQL Async Connection Pool

LEGO Component: `database/connection-pool`

## Overview

Production-ready async connection pool for PostgreSQL using SQLAlchemy 2.0+ with asyncpg driver.

## Features

- **Connection Pooling**: Configurable pool size with overflow support
- **Retry Logic**: Automatic retry with exponential backoff
- **Health Checks**: Latency monitoring and degraded state detection
- **Query Logging**: Optional SQL query logging
- **Kubernetes Ready**: Liveness and readiness probe endpoints
- **Graceful Shutdown**: Clean connection disposal

## Installation

```bash
pip install sqlalchemy[asyncio] asyncpg
```

## Quick Start

### Basic Usage

```python
from database.connection_pool import init_pool, get_db, close_pool

# Initialize at startup
await init_pool()

# Use in FastAPI
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@app.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item))
    return result.scalars().all()

# Close at shutdown
await close_pool()
```

### FastAPI Integration

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database.connection_pool import init_pool, close_pool, get_db, HealthCheckEndpoint, get_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_pool()
    yield
    # Shutdown
    await close_pool()

app = FastAPI(lifespan=lifespan)

# Health endpoints
health = HealthCheckEndpoint(get_pool())

@app.get("/health")
async def health_check():
    return await health.check()

@app.get("/health/ready")
async def readiness():
    body, status = await health.readiness_check()
    return JSONResponse(body, status_code=status)

@app.get("/health/live")
async def liveness():
    body, status = await health.liveness_check()
    return JSONResponse(body, status_code=status)
```

### Custom Configuration

```python
from database.connection_pool import PoolConfig, ConnectionPool

config = PoolConfig(
    database_url="postgresql://user:pass@localhost:5432/db",
    pool_size=10,
    max_overflow=20,
    pool_timeout=60,
    pool_recycle=3600,
    echo=True,  # Enable SQL logging
    retry_attempts=5,
    retry_delay=2.0,
)

pool = ConnectionPool(config)
await pool.initialize()
```

### Manual Session Management

```python
pool = get_pool()

# Using context manager
async with pool.session() as session:
    result = await session.execute(select(User))
    users = result.scalars().all()

# With retry logic
result = await pool.execute_with_retry(
    text("SELECT * FROM users WHERE active = :active"),
    {"active": True}
)
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | (required) | PostgreSQL connection URL |
| `DB_POOL_SIZE` | 5 | Connection pool size |
| `DB_POOL_MAX_OVERFLOW` | 10 | Max overflow connections |
| `DB_POOL_TIMEOUT` | 30 | Pool timeout (seconds) |
| `DB_POOL_RECYCLE` | 1800 | Connection recycle time (seconds) |
| `DB_ECHO` | false | Enable SQL query logging |
| `DB_RETRY_ATTEMPTS` | 3 | Number of retry attempts |
| `DB_RETRY_DELAY` | 1.0 | Base delay between retries (seconds) |

## Health Check States

| State | Description |
|-------|-------------|
| `healthy` | All metrics within normal range |
| `degraded` | Elevated latency or minor issues |
| `unhealthy` | Connection failures or critical issues |
| `unknown` | Unable to determine state |

## Pool Statistics

```python
stats = pool.get_stats()
# {
#     "initialized": True,
#     "pool_size": 5,
#     "checked_in": 4,
#     "checked_out": 1,
#     "overflow": 0,
#     "invalid": 0,
#     "query_count": 150,
#     "error_count": 2,
# }
```

## Source

Extracted from: `D:\Projects\life-os-dashboard\backend\app\core\database.py`

## Dependencies

- `sqlalchemy[asyncio]>=2.0.0`
- `asyncpg>=0.29.0`

## License

MIT
