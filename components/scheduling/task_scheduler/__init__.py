"""
Task Scheduler Component

Async task scheduling for FastAPI with APScheduler backend.

Features:
- Interval-based scheduling
- Cron expressions
- One-time scheduled jobs
- FastAPI lifespan integration
- Decorator-based job registration

References:
- https://github.com/agronholm/apscheduler
- https://github.com/amisadmin/fastapi-scheduler

Installation:
    pip install apscheduler

Example:
    from library.components.scheduling.task_scheduler import TaskScheduler

    scheduler = TaskScheduler()

    @scheduler.interval(minutes=5)
    async def check_health():
        await ping_services()

    @scheduler.cron(hour=2, minute=0)
    async def nightly_cleanup():
        await cleanup_database()
"""

from .scheduler import (
    TaskScheduler,
    SchedulerConfig,
    JobConfig,
    TriggerType,
    create_scheduler_lifespan,
)

__all__ = [
    "TaskScheduler",
    "SchedulerConfig",
    "JobConfig",
    "TriggerType",
    "create_scheduler_lifespan",
]
