"""
Task Scheduler Component

Async task scheduling for FastAPI with APScheduler backend.

Features:
- Interval-based scheduling
- Cron expressions with validation
- One-time scheduled jobs
- FastAPI lifespan integration
- Decorator-based job registration
- Programmatic job management
- Job/Task status enums for persistence

References:
- https://github.com/agronholm/apscheduler
- https://github.com/amisadmin/fastapi-scheduler

Installation:
    pip install apscheduler

Example:
    from library.components.scheduling.task_scheduler import (
        TaskScheduler,
        validate_cron_expression,
        JobStatus,
        TaskStatus,
    )

    scheduler = TaskScheduler()

    @scheduler.interval(minutes=5)
    async def check_health():
        await ping_services()

    @scheduler.cron(hour=2, minute=0)
    async def nightly_cleanup():
        await cleanup_database()

    # Validate cron before storing
    is_valid, error = validate_cron_expression("0 2 * * *")
    if not is_valid:
        raise ValueError(error)

Extracted from:
    - life-os-dashboard (D:\\Projects\\life-os-dashboard)
"""

from .scheduler import (
    TaskScheduler,
    SchedulerConfig,
    JobConfig,
    TriggerType,
    JobStatus,
    TaskStatus,
    create_scheduler_lifespan,
    validate_cron_expression,
    parse_cron_expression,
)

__all__ = [
    # Core scheduler
    "TaskScheduler",
    "SchedulerConfig",
    "JobConfig",
    "TriggerType",
    "create_scheduler_lifespan",
    # Status enums (for persistence layers)
    "JobStatus",
    "TaskStatus",
    # Cron utilities
    "validate_cron_expression",
    "parse_cron_expression",
]
