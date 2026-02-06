# Pytest Fixtures Library Component

LEGO-compatible pytest fixture collection for FastAPI + SQLAlchemy async testing.

## Installation

Copy to your project or add to Python path:

```bash
# Copy to project
cp -r pytest-fixtures/ your_project/tests/

# Or add to conftest.py
import sys
sys.path.insert(0, "/path/to/library/components/testing/pytest-fixtures")
```

### Dependencies

```bash
pip install pytest pytest-asyncio httpx sqlalchemy[asyncio] asyncpg
```

Or add to requirements.txt:
```
pytest>=7.0.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.28.0
```

## Quick Start

### 1. Configure conftest.py

```python
# tests/conftest.py
import os
import pytest
import pytest_asyncio

# Configure environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test_db"

# Import fixtures
from pytest_fixtures import (
    event_loop,
    async_db_engine,
    db_session,
    mock_db_session,
    mock_redis_client,
    mock_websocket,
    performance_tracker,
    concurrent_executor,
    pytest_configure,
)

# Import factories
from pytest_fixtures.factories import (
    UserFactory,
    ProjectFactory,
    AgentFactory,
)

# Configure factories with your models
from app.models import User, Project, Agent
UserFactory.model = User
ProjectFactory.model = Project
AgentFactory.model = Agent

# Create app-specific fixtures
@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    from app.models import Base
    from pytest_fixtures.fixtures import async_db_engine as _engine
    async for engine in _engine(Base):
        yield engine

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    from app.database import get_db
    from app.main import app
    from pytest_fixtures.fixtures import async_client
    async for c in async_client(app, db_session, get_db):
        yield c
```

### 2. Write Tests

```python
# tests/test_users.py
import pytest
from pytest_fixtures.factories import UserFactory

@pytest.mark.integration
async def test_create_user(db_session):
    """Test user creation with real database."""
    user = UserFactory.create(username="testuser")
    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
    assert user.username == "testuser"

@pytest.mark.unit
async def test_get_user(mock_db_session):
    """Test user retrieval with mocked database."""
    expected = UserFactory.create(id=1)
    mock_db_session.scalar.return_value = expected

    # Call your service
    result = await user_service.get(mock_db_session, 1)

    assert result.id == 1
```

## Available Fixtures

### Core Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `event_loop` | session | Async event loop for tests |
| `async_db_engine` | function | SQLAlchemy async engine with table management |
| `db_session` | function | Database session with auto-rollback |
| `async_client` | function | httpx AsyncClient with dependency overrides |

### Mock Fixtures

| Fixture | Description |
|---------|-------------|
| `mock_db_session` | Mocked SQLAlchemy AsyncSession |
| `mock_redis_client` | Mocked Redis client |
| `mock_websocket` | Mocked WebSocket connection |
| `mock_memory_mcp_client` | Mocked Memory MCP client |

### Utility Fixtures

| Fixture | Description |
|---------|-------------|
| `performance_tracker` | Track and assert timing |
| `concurrent_executor` | Run tasks concurrently for race condition testing |
| `cleanup_after_test` | Auto-cleanup pending async tasks |

## Factories

### Base Factory Pattern

```python
from pytest_fixtures.factories import BaseFactory

class MyModelFactory(BaseFactory):
    model = MyModel
    defaults = {
        "name": "default",
        "created_at": lambda: datetime.now(),  # Callable = lazy eval
    }

# Usage
instance = MyModelFactory.create(name="override")
batch = MyModelFactory.create_batch(10)
payload = MyModelFactory.build()  # Returns dict only
```

### Included Factories

- `UserFactory` - User model with unique username/email
- `ProjectFactory` - Project with standard metadata
- `AgentFactory` - AI agent configuration
- `TaskFactory` - Scheduled task with cron
- `ExecutionResultFactory` - Task execution results
- `WebSocketMessageFactory` - WebSocket message payloads
- `APIRequestFactory` - HTTP request payloads
- `MemoryMCPQueryFactory` - Memory MCP query payloads

## Pytest Markers

Registered markers for test organization:

```python
@pytest.mark.unit           # Unit tests with mocks
@pytest.mark.integration    # Integration tests with database
@pytest.mark.websocket      # WebSocket tests
@pytest.mark.circuit_breaker # Circuit breaker tests
@pytest.mark.performance    # Performance tests
@pytest.mark.concurrent     # Race condition tests
@pytest.mark.slow           # Slow-running tests
```

Run specific markers:
```bash
pytest -m unit              # Only unit tests
pytest -m "not slow"        # Skip slow tests
pytest -m integration       # Only integration tests
```

## Advanced Usage

### Performance Testing

```python
def test_api_performance(client, performance_tracker):
    performance_tracker.start()
    response = await client.get("/api/heavy-endpoint")
    performance_tracker.stop()

    assert response.status_code == 200
    performance_tracker.assert_under(1.0)  # Must complete in <1s
```

### Race Condition Testing

```python
async def test_concurrent_updates(db_session, concurrent_executor):
    counter = Counter(value=0)
    db_session.add(counter)
    await db_session.commit()

    async def increment():
        await service.increment(counter.id)

    # Run 100 concurrent increments
    await concurrent_executor(increment, count=100)

    # Check for race conditions
    await db_session.refresh(counter)
    assert counter.value == 100
```

### WebSocket Testing

```python
async def test_ws_broadcast(mock_websocket, websocket_manager):
    await websocket_manager.connect(mock_websocket)
    await websocket_manager.broadcast({"type": "update"})

    mock_websocket.send_json.assert_called_once_with({"type": "update"})
```

## Project Compatibility

| Project | Compatible | Notes |
|---------|------------|-------|
| Life OS Dashboard | Yes | Source project |
| Trader AI | Yes | FastAPI + SQLAlchemy |
| Memory MCP | Yes | Async patterns |
| Any FastAPI project | Yes | With SQLAlchemy 2.0+ |

## File Structure

```
pytest-fixtures/
  __init__.py       # Package exports
  fixtures.py       # Core fixture definitions
  factories.py      # Test data factories
  README.md         # This documentation
```

## Version

1.0.0 - Initial extraction from Life OS Dashboard
