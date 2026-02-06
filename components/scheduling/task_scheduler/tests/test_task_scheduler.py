from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.scheduling.task_scheduler'
EXPORTS = [
    # Core scheduler
    'JobConfig',
    'SchedulerConfig',
    'TaskScheduler',
    'TriggerType',
    'create_scheduler_lifespan',
    # Status enums (from life-os-dashboard)
    'JobStatus',
    'TaskStatus',
    # Cron utilities
    'validate_cron_expression',
    'parse_cron_expression',
]


def _import_module():
    return import_component_module(MODULE_PATH)

def test_module_imports():
    _import_module()


def test_exports_present():
    module = _import_module()
    if not EXPORTS:
        return
    missing = [name for name in EXPORTS if not hasattr(module, name)]
    assert not missing, f"Missing exports: {missing}"


def test_cron_validation_valid():
    """Test valid cron expressions."""
    module = _import_module()
    validate = module.validate_cron_expression

    # Valid expressions
    valid_cases = [
        "0 2 * * *",      # Daily at 2 AM
        "*/5 * * * *",    # Every 5 minutes
        "0 0 1 * *",      # First of each month
        "30 14 * * mon",  # Monday at 2:30 PM
        "0 0 * * 0-6",    # Every day (range)
        "0,30 * * * *",   # On the hour and half hour
    ]

    for expr in valid_cases:
        is_valid, error = validate(expr)
        assert is_valid, f"Expected valid: {expr}, got error: {error}"


def test_cron_validation_invalid():
    """Test invalid cron expressions."""
    module = _import_module()
    validate = module.validate_cron_expression

    # Invalid expressions
    invalid_cases = [
        ("invalid", "Expected 5 fields"),
        ("60 * * * *", "Minute must be 0-59"),
        ("* 25 * * *", "Hour must be 0-23"),
        ("* * 32 * *", "Day must be 1-31"),
        ("* * * 13 *", "Month must be 1-12"),
        ("* * * * 8", "Day of week must be 0-6"),
    ]

    for expr, expected_error in invalid_cases:
        is_valid, error = validate(expr)
        assert not is_valid, f"Expected invalid: {expr}"
        assert expected_error in error, f"Expected '{expected_error}' in '{error}'"


def test_cron_parse():
    """Test cron expression parsing."""
    module = _import_module()
    parse = module.parse_cron_expression

    result = parse("30 14 * * mon")
    assert result["minute"] == "30"
    assert result["hour"] == "14"
    assert result["day"] == "*"
    assert result["month"] == "*"
    assert result["day_of_week"] == "mon"


def test_cron_parse_invalid_raises():
    """Test that invalid cron raises ValueError."""
    module = _import_module()
    parse = module.parse_cron_expression

    with pytest.raises(ValueError):
        parse("invalid expression")


def test_job_status_enum():
    """Test JobStatus enum values."""
    module = _import_module()
    JobStatus = module.JobStatus

    assert JobStatus.PENDING.value == "pending"
    assert JobStatus.RUNNING.value == "running"
    assert JobStatus.COMPLETED.value == "completed"
    assert JobStatus.FAILED.value == "failed"
    assert JobStatus.PAUSED.value == "paused"
    assert JobStatus.DISABLED.value == "disabled"


def test_task_status_enum():
    """Test TaskStatus enum values (Kanban workflow)."""
    module = _import_module()
    TaskStatus = module.TaskStatus

    assert TaskStatus.TODO.value == "todo"
    assert TaskStatus.IN_PROGRESS.value == "in_progress"
    assert TaskStatus.IN_REVIEW.value == "in_review"
    assert TaskStatus.DONE.value == "done"
    assert TaskStatus.CANCELLED.value == "cancelled"
