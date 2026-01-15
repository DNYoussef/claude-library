"""
Pytest Fixtures Library Component
=================================

LEGO-compatible pytest fixture collection for FastAPI + SQLAlchemy async testing.
Provides reusable fixtures for database sessions, HTTP clients, mocks, and test data factories.

Usage:
    # In your conftest.py
    from pytest_fixtures import (
        event_loop,
        async_db_engine,
        db_session,
        async_client,
        mock_db_session,
        mock_redis_client,
    )

    # Import specific factories
    from pytest_fixtures.factories import UserFactory, ProjectFactory

Dependencies:
    - pytest>=7.0.0
    - pytest-asyncio>=0.21.0
    - httpx>=0.24.0
    - sqlalchemy[asyncio]>=2.0.0
"""

try:
    from .fixtures import (
        # Core fixtures
        event_loop,
        async_db_engine,
        db_session,
        async_client,
        # Mock fixtures
        mock_db_session,
        mock_redis_client,
        mock_websocket,
        mock_memory_mcp_client,
        # Utility fixtures
        performance_tracker,
        concurrent_executor,
        cleanup_after_test,
        # Configuration
        pytest_configure,
    )

    from .factories import (
        BaseFactory,
        UserFactory,
        ProjectFactory,
        AgentFactory,
        TaskFactory,
        ExecutionResultFactory,
    )
except ImportError:
    import importlib.util
    from pathlib import Path

    _module_dir = Path(__file__).parent

    def _load_module(name: str, filename: str):
        spec = importlib.util.spec_from_file_location(name, _module_dir / filename)
        if not spec or not spec.loader:
            raise ImportError(f"Unable to load {filename}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    _fixtures = _load_module("pytest_fixtures_fixtures", "fixtures.py")
    _factories = _load_module("pytest_fixtures_factories", "factories.py")

    # Core fixtures
    event_loop = _fixtures.event_loop
    async_db_engine = _fixtures.async_db_engine
    db_session = _fixtures.db_session
    async_client = _fixtures.async_client
    # Mock fixtures
    mock_db_session = _fixtures.mock_db_session
    mock_redis_client = _fixtures.mock_redis_client
    mock_websocket = _fixtures.mock_websocket
    mock_memory_mcp_client = _fixtures.mock_memory_mcp_client
    # Utility fixtures
    performance_tracker = _fixtures.performance_tracker
    concurrent_executor = _fixtures.concurrent_executor
    cleanup_after_test = _fixtures.cleanup_after_test
    # Configuration
    pytest_configure = _fixtures.pytest_configure

    BaseFactory = _factories.BaseFactory
    UserFactory = _factories.UserFactory
    ProjectFactory = _factories.ProjectFactory
    AgentFactory = _factories.AgentFactory
    TaskFactory = _factories.TaskFactory
    ExecutionResultFactory = _factories.ExecutionResultFactory

__all__ = [
    # Core fixtures
    "event_loop",
    "async_db_engine",
    "db_session",
    "async_client",
    # Mock fixtures
    "mock_db_session",
    "mock_redis_client",
    "mock_websocket",
    "mock_memory_mcp_client",
    # Utility fixtures
    "performance_tracker",
    "concurrent_executor",
    "cleanup_after_test",
    # Configuration
    "pytest_configure",
    # Factories
    "BaseFactory",
    "UserFactory",
    "ProjectFactory",
    "AgentFactory",
    "TaskFactory",
    "ExecutionResultFactory",
]

__version__ = "1.0.0"
