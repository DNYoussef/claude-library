"""
Test Data Factories
===================

Factory classes for generating test data with sensible defaults.
Designed for LEGO-style composition - extend BaseFactory for your models.

Usage:
    # Create a factory for your model
    class MyModelFactory(BaseFactory):
        model = MyModel
        defaults = {
            "name": "default_name",
            "status": "active",
        }

    # Use the factory
    instance = MyModelFactory.create(name="custom")
    batch = MyModelFactory.create_batch(10)
"""

from datetime import datetime, timezone
from typing import Any, TypeVar, Generic
from uuid import uuid4


T = TypeVar("T")


class BaseFactory(Generic[T]):
    """
    Base factory class for generating test data.

    Subclasses should define:
        - model: The model class to instantiate
        - defaults: Dict of default values

    Features:
        - Lazy evaluation of callable defaults
        - Batch creation
        - Override any default at creation time
    """

    model: type[T] | None = None
    defaults: dict[str, Any] = {}

    @classmethod
    def _resolve_value(cls, value: Any) -> Any:
        """Resolve callable values lazily."""
        if callable(value):
            return value()
        return value

    @classmethod
    def build(cls, **overrides: Any) -> dict[str, Any]:
        """
        Build a dict of attributes without creating instance.

        Useful for creating API request payloads.
        """
        data = {}
        for key, value in cls.defaults.items():
            data[key] = cls._resolve_value(value)
        data.update(overrides)
        return data

    @classmethod
    def create(cls, **overrides: Any) -> T:
        """
        Create a model instance with defaults + overrides.

        Args:
            **overrides: Fields to override from defaults

        Returns:
            Model instance
        """
        if cls.model is None:
            raise ValueError("Factory must define model class")

        data = cls.build(**overrides)
        return cls.model(**data)

    @classmethod
    def create_batch(cls, count: int, **overrides: Any) -> list[T]:
        """
        Create multiple model instances.

        Args:
            count: Number of instances to create
            **overrides: Fields to override for all instances

        Returns:
            List of model instances
        """
        return [cls.create(**overrides) for _ in range(count)]


# =============================================================================
# Common Factories
# =============================================================================

class UserFactory(BaseFactory):
    """
    Factory for User model test data.

    Defaults:
        - username: Unique username (user_<uuid>)
        - email: Unique email (<uuid>@test.com)
        - is_active: True
        - created_at: Current UTC time
    """

    model = None  # Set to your User model
    defaults = {
        "username": lambda: f"user_{uuid4().hex[:8]}",
        "email": lambda: f"{uuid4().hex[:8]}@test.com",
        "is_active": True,
        "created_at": lambda: datetime.now(timezone.utc),
    }


class ProjectFactory(BaseFactory):
    """
    Factory for Project model test data.

    Defaults:
        - name: "Test Project"
        - description: "A test project"
        - status: "active"
        - sparc_mode: "specification"
        - metadata: Standard test metadata
        - created_at: Current UTC time
    """

    model = None  # Set to your Project model
    defaults = {
        "name": "Test Project",
        "description": "A test project",
        "status": "active",
        "sparc_mode": "specification",
        "metadata": lambda: {
            "created_by": "test_user",
            "tags": ["test", "sample"],
            "environment": "test",
        },
        "created_at": lambda: datetime.now(timezone.utc),
    }


class AgentFactory(BaseFactory):
    """
    Factory for Agent model test data.

    Defaults:
        - name: Unique agent name
        - agent_type: "researcher"
        - status: "active"
        - capabilities: ["research", "analysis"]
        - metadata: Standard test metadata
    """

    model = None  # Set to your Agent model
    defaults = {
        "name": lambda: f"test-agent-{uuid4().hex[:6]}",
        "agent_type": "researcher",
        "status": "active",
        "capabilities": lambda: ["research", "analysis"],
        "metadata": lambda: {
            "version": "1.0.0",
            "environment": "test",
        },
    }


class TaskFactory(BaseFactory):
    """
    Factory for ScheduledTask model test data.

    Defaults:
        - name: Unique task name
        - description: "A test scheduled task"
        - cron_expression: Daily at midnight
        - command: Simple echo command
        - enabled: True
        - metadata: Timeout and retry config
    """

    model = None  # Set to your Task model
    defaults = {
        "name": lambda: f"test-task-{uuid4().hex[:6]}",
        "description": "A test scheduled task",
        "cron_expression": "0 0 * * *",
        "command": "echo 'test'",
        "enabled": True,
        "metadata": lambda: {
            "timeout": 300,
            "retries": 3,
        },
    }


class ExecutionResultFactory(BaseFactory):
    """
    Factory for ExecutionResult model test data.

    Defaults:
        - status: "success"
        - output: "Test output"
        - error: None
        - duration_seconds: 1.5
        - metadata: Exit code and memory usage
        - executed_at: Current UTC time
    """

    model = None  # Set to your ExecutionResult model
    defaults = {
        "status": "success",
        "output": "Test output",
        "error": None,
        "duration_seconds": 1.5,
        "metadata": lambda: {
            "exit_code": 0,
            "memory_used": "100MB",
        },
        "executed_at": lambda: datetime.now(timezone.utc),
    }


# =============================================================================
# Specialized Factories
# =============================================================================

class WebSocketMessageFactory(BaseFactory):
    """Factory for WebSocket message payloads."""

    model = dict  # Returns raw dict
    defaults = {
        "type": "event",
        "payload": lambda: {"data": "test"},
        "timestamp": lambda: datetime.now(timezone.utc).isoformat(),
    }


class APIRequestFactory(BaseFactory):
    """Factory for API request payloads."""

    model = dict  # Returns raw dict
    defaults = {
        "headers": lambda: {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token",
        },
        "body": lambda: {},
    }


class MemoryMCPQueryFactory(BaseFactory):
    """Factory for Memory MCP query payloads."""

    model = dict  # Returns raw dict
    defaults = {
        "query": "test query",
        "namespace": "test",
        "top_k": 10,
        "filters": lambda: {},
        "tags": lambda: {
            "WHO": "test-agent:1.0.0",
            "PROJECT": "test-project",
            "WHY": "testing",
        },
    }
