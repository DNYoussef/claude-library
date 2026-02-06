"""
Pytest Fixtures Collection
==========================

Reusable pytest fixtures for FastAPI + SQLAlchemy async testing.
Designed for LEGO-style composition across projects.

Configuration:
    Set these environment variables before importing:
    - DATABASE_URL: Async PostgreSQL URL (postgresql+asyncpg://...)
    - REDIS_URL: Redis connection URL (redis://...)
    - ENVIRONMENT: Set to "test" for testing mode
"""

import asyncio
import os
import time
from typing import AsyncGenerator, Generator, Any, Callable, Awaitable
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


# =============================================================================
# Environment Configuration
# =============================================================================

def configure_test_environment(
    database_url: str = "postgresql+asyncpg://test:test@localhost:5432/test_db",
    redis_url: str = "redis://localhost:6379/1",
) -> None:
    """Configure environment variables for testing."""
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("DATABASE_URL", database_url)
    os.environ.setdefault("REDIS_URL", redis_url)


# =============================================================================
# Event Loop Fixture
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create event loop for async tests.

    Session-scoped to share across all tests for performance.
    Properly closes loop on teardown.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="function")
async def async_db_engine(
    base_model: Any = None,
) -> AsyncGenerator[AsyncEngine, None]:
    """
    Create test database engine with automatic table management.

    Args:
        base_model: SQLAlchemy Base class with metadata (import from your app)

    Features:
        - Creates fresh tables before each test
        - Drops tables after test completes
        - Uses NullPool to prevent connection leaks

    Usage:
        @pytest_asyncio.fixture(scope="function")
        async def test_db_engine():
            from app.models import Base
            async for engine in async_db_engine(Base):
                yield engine
    """
    engine = create_async_engine(
        os.getenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db"),
        echo=False,
        poolclass=NullPool,  # No connection pooling in tests
    )

    if base_model is not None:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(base_model.metadata.drop_all)
            await conn.run_sync(base_model.metadata.create_all)

    yield engine

    if base_model is not None:
        # Cleanup tables
        async with engine.begin() as conn:
            await conn.run_sync(base_model.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(
    test_db_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session with automatic rollback.

    Features:
        - Creates fresh session for each test
        - Rolls back all changes after test
        - Uses expire_on_commit=False for cleaner assertions

    Usage:
        async def test_create_user(db_session):
            user = User(name="test")
            db_session.add(user)
            await db_session.commit()
            assert user.id is not None
    """
    async_session_factory = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()


# =============================================================================
# HTTP Client Fixtures
# =============================================================================

@pytest_asyncio.fixture(scope="function")
async def async_client(
    app: Any,
    db_session: AsyncSession,
    get_db_dependency: Callable,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client with dependency overrides.

    Args:
        app: FastAPI application instance
        db_session: Test database session
        get_db_dependency: The get_db dependency function to override

    Features:
        - Overrides database dependency for isolated testing
        - Uses httpx AsyncClient for async requests
        - Clears overrides after test

    Usage:
        @pytest_asyncio.fixture
        async def client(app, db_session):
            from app.database import get_db
            async for c in async_client(app, db_session, get_db):
                yield c

        async def test_endpoint(client):
            response = await client.get("/api/users")
            assert response.status_code == 200
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db_dependency] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_db_session() -> AsyncMock:
    """
    Mock database session for unit tests.

    Pre-configured with common SQLAlchemy session methods:
        - commit, rollback, refresh, flush
        - execute, scalar, scalars
        - add, delete

    Usage:
        def test_service(mock_db_session):
            mock_db_session.scalar.return_value = User(id=1, name="test")
            result = await service.get_user(mock_db_session, 1)
            assert result.name == "test"
    """
    mock = AsyncMock(spec=AsyncSession)
    mock.commit = AsyncMock()
    mock.rollback = AsyncMock()
    mock.refresh = AsyncMock()
    mock.execute = AsyncMock()
    mock.scalar = AsyncMock()
    mock.scalars = AsyncMock()
    mock.add = MagicMock()
    mock.delete = AsyncMock()
    mock.flush = AsyncMock()
    return mock


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """
    Mock Redis client for unit tests.

    Pre-configured with common Redis operations:
        - publish, subscribe, unsubscribe
        - get, set, delete
        - ping

    Usage:
        def test_cache(mock_redis_client):
            mock_redis_client.get.return_value = '{"cached": true}'
            result = await cache.get("key")
            assert result == '{"cached": true}'
    """
    mock = AsyncMock()
    mock.publish = AsyncMock(return_value=1)
    mock.subscribe = AsyncMock()
    mock.unsubscribe = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.ping = AsyncMock(return_value=True)
    mock.setex = AsyncMock(return_value=True)
    mock.expire = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=0)
    mock.keys = AsyncMock(return_value=[])
    mock.hget = AsyncMock(return_value=None)
    mock.hset = AsyncMock(return_value=1)
    mock.hdel = AsyncMock(return_value=1)
    mock.hgetall = AsyncMock(return_value={})
    return mock


@pytest.fixture
def mock_websocket() -> AsyncMock:
    """
    Mock WebSocket connection for testing.

    Pre-configured with common WebSocket methods:
        - accept, close
        - send_text, send_json
        - receive_text, receive_json

    Usage:
        async def test_ws_handler(mock_websocket):
            mock_websocket.receive_json.return_value = {"type": "ping"}
            await handler(mock_websocket)
            mock_websocket.send_json.assert_called()
    """
    mock = AsyncMock()
    mock.accept = AsyncMock()
    mock.send_text = AsyncMock()
    mock.send_json = AsyncMock()
    mock.receive_text = AsyncMock()
    mock.receive_json = AsyncMock()
    mock.close = AsyncMock()
    mock.client = Mock()
    mock.client.host = "127.0.0.1"
    mock.client.port = 12345
    return mock


@pytest.fixture
def mock_memory_mcp_client() -> Mock:
    """
    Mock Memory MCP client for unit tests.

    Pre-configured with Memory MCP operations:
        - is_healthy, circuit_state, fallback_mode
        - vector_search, memory_store

    Usage:
        def test_memory_search(mock_memory_mcp_client):
            mock_memory_mcp_client.vector_search.return_value = {"results": [...]}
            results = await memory_service.search("query")
    """
    mock = Mock()
    mock.is_healthy = Mock(return_value=True)
    mock.vector_search = AsyncMock(return_value={
        "results": [],
        "total": 0
    })
    mock.memory_store = AsyncMock(return_value={
        "success": True,
        "key": "test-key"
    })
    mock.fallback_mode = False
    mock.circuit_state = "CLOSED"
    return mock


# =============================================================================
# Utility Fixtures
# =============================================================================

class PerformanceTracker:
    """Track performance metrics for tests."""

    def __init__(self):
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.measurements: list[float] = []

    def start(self) -> None:
        """Start timing."""
        self.start_time = time.perf_counter()

    def stop(self) -> float:
        """Stop timing and return duration."""
        self.end_time = time.perf_counter()
        duration = self.duration
        if duration:
            self.measurements.append(duration)
        return duration or 0.0

    @property
    def duration(self) -> float | None:
        """Get current duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def average(self) -> float:
        """Get average of all measurements."""
        return sum(self.measurements) / len(self.measurements) if self.measurements else 0.0

    def assert_under(self, max_seconds: float) -> None:
        """Assert duration is under threshold."""
        assert self.duration is not None, "Timer not stopped"
        assert self.duration < max_seconds, f"Duration {self.duration:.3f}s exceeded {max_seconds}s"


@pytest.fixture
def performance_tracker() -> PerformanceTracker:
    """
    Track performance metrics for tests.

    Usage:
        def test_performance(performance_tracker):
            performance_tracker.start()
            await slow_operation()
            performance_tracker.stop()
            performance_tracker.assert_under(1.0)  # Assert < 1 second
    """
    return PerformanceTracker()


@pytest.fixture
def concurrent_executor() -> Callable[[Callable[[], Awaitable[Any]], int], Awaitable[list[Any]]]:
    """
    Execute multiple async tasks concurrently for race condition testing.

    Usage:
        async def test_concurrent(concurrent_executor):
            async def increment():
                await service.increment_counter()

            results = await concurrent_executor(increment, count=100)
            # Check for race conditions
    """
    async def execute_concurrent(
        task: Callable[[], Awaitable[Any]],
        count: int = 10
    ) -> list[Any]:
        """Execute task multiple times concurrently."""
        return await asyncio.gather(*[task() for _ in range(count)])

    return execute_concurrent


@pytest.fixture(autouse=True)
async def cleanup_after_test() -> AsyncGenerator[None, None]:
    """
    Cleanup resources after each test.

    Auto-used fixture that runs after every test to ensure
    pending async tasks complete before teardown.
    """
    yield
    # Allow pending tasks to complete
    await asyncio.sleep(0)


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config: pytest.Config) -> None:
    """
    Register custom pytest markers.

    Available markers:
        - @pytest.mark.unit: Unit tests with mocked dependencies
        - @pytest.mark.integration: Integration tests with real database
        - @pytest.mark.websocket: WebSocket connection tests
        - @pytest.mark.circuit_breaker: Circuit breaker and fallback tests
        - @pytest.mark.performance: Performance and load tests
        - @pytest.mark.concurrent: Concurrent operation tests
        - @pytest.mark.slow: Slow running tests
    """
    config.addinivalue_line("markers", "unit: Unit tests with mocked dependencies")
    config.addinivalue_line("markers", "integration: Integration tests with real database")
    config.addinivalue_line("markers", "websocket: WebSocket connection tests")
    config.addinivalue_line("markers", "circuit_breaker: Circuit breaker and fallback tests")
    config.addinivalue_line("markers", "performance: Performance and load tests")
    config.addinivalue_line("markers", "concurrent: Concurrent operation tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
