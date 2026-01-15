"""
Task Scheduler Component

Production-ready async task scheduling for FastAPI applications.
Based on APScheduler patterns with FastAPI lifespan integration.

References:
- https://github.com/agronholm/apscheduler
- https://github.com/amisadmin/fastapi-scheduler

Installation:
    pip install apscheduler
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union, Awaitable
from datetime import datetime
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Scheduler trigger types."""
    INTERVAL = "interval"
    CRON = "cron"
    DATE = "date"


@dataclass
class JobConfig:
    """Job configuration."""
    id: str
    func: Callable[..., Awaitable[Any]]
    trigger: TriggerType
    trigger_args: Dict[str, Any] = field(default_factory=dict)
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    max_instances: int = 1
    replace_existing: bool = True
    misfire_grace_time: Optional[int] = None  # seconds


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""
    timezone: str = "UTC"
    job_defaults: Dict[str, Any] = field(default_factory=lambda: {
        "coalesce": True,
        "max_instances": 3,
        "misfire_grace_time": 60,
    })
    executors: Dict[str, Any] = field(default_factory=lambda: {
        "default": {"type": "asyncio"},
    })


class TaskScheduler:
    """
    Async task scheduler with APScheduler backend.

    Supports:
    - Interval-based jobs (every N seconds/minutes/hours)
    - Cron-based jobs (crontab syntax)
    - One-time scheduled jobs
    - FastAPI lifespan integration

    Example:
        scheduler = TaskScheduler()

        # Interval job
        @scheduler.interval(seconds=30)
        async def heartbeat():
            print("Heartbeat")

        # Cron job (every day at 2am)
        @scheduler.cron(hour=2, minute=0)
        async def daily_cleanup():
            await cleanup_old_records()

        # FastAPI integration
        from contextlib import asynccontextmanager
        from fastapi import FastAPI

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await scheduler.start()
            yield
            await scheduler.shutdown()

        app = FastAPI(lifespan=lifespan)
    """

    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()
        self._scheduler = None
        self._pending_jobs: List[JobConfig] = []
        self._started = False

    async def _get_scheduler(self):
        """Lazy initialize APScheduler."""
        if self._scheduler is None:
            try:
                from apscheduler.schedulers.asyncio import AsyncIOScheduler
                from apscheduler.triggers.interval import IntervalTrigger
                from apscheduler.triggers.cron import CronTrigger
                from apscheduler.triggers.date import DateTrigger

                self._scheduler = AsyncIOScheduler(
                    timezone=self.config.timezone,
                    job_defaults=self.config.job_defaults,
                )
            except ImportError:
                raise ImportError(
                    "apscheduler required. Install with: pip install apscheduler"
                )
        return self._scheduler

    async def start(self):
        """Start the scheduler."""
        if self._started:
            return

        scheduler = await self._get_scheduler()

        # Add pending jobs
        for job in self._pending_jobs:
            await self._add_job(job)

        scheduler.start()
        self._started = True
        logger.info("Task scheduler started")

    async def shutdown(self, wait: bool = True):
        """Shutdown the scheduler."""
        if not self._started:
            return

        scheduler = await self._get_scheduler()
        scheduler.shutdown(wait=wait)
        self._started = False
        logger.info("Task scheduler stopped")

    async def _add_job(self, job_config: JobConfig):
        """Add a job to the scheduler."""
        scheduler = await self._get_scheduler()

        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.date import DateTrigger

        if job_config.trigger == TriggerType.INTERVAL:
            trigger = IntervalTrigger(**job_config.trigger_args)
        elif job_config.trigger == TriggerType.CRON:
            trigger = CronTrigger(**job_config.trigger_args)
        elif job_config.trigger == TriggerType.DATE:
            trigger = DateTrigger(**job_config.trigger_args)
        else:
            raise ValueError(f"Unknown trigger type: {job_config.trigger}")

        scheduler.add_job(
            job_config.func,
            trigger=trigger,
            id=job_config.id,
            args=job_config.args,
            kwargs=job_config.kwargs,
            max_instances=job_config.max_instances,
            replace_existing=job_config.replace_existing,
            misfire_grace_time=job_config.misfire_grace_time,
        )

    def interval(
        self,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
        weeks: int = 0,
        job_id: Optional[str] = None,
    ):
        """
        Decorator for interval-based jobs.

        Example:
            @scheduler.interval(minutes=5)
            async def check_status():
                await update_status()
        """
        def decorator(func: Callable[..., Awaitable[Any]]):
            job = JobConfig(
                id=job_id or func.__name__,
                func=func,
                trigger=TriggerType.INTERVAL,
                trigger_args={
                    "seconds": seconds,
                    "minutes": minutes,
                    "hours": hours,
                    "days": days,
                    "weeks": weeks,
                },
            )

            if not self._started:
                self._pending_jobs.append(job)
                return func

            asyncio.create_task(self._add_job(job))
            return func
        return decorator

    def cron(
        self,
        year: Optional[Union[int, str]] = None,
        month: Optional[Union[int, str]] = None,
        day: Optional[Union[int, str]] = None,
        week: Optional[Union[int, str]] = None,
        day_of_week: Optional[Union[int, str]] = None,
        hour: Optional[Union[int, str]] = None,
        minute: Optional[Union[int, str]] = None,
        second: Optional[Union[int, str]] = None,
        job_id: Optional[str] = None,
    ):
        """
        Decorator for cron-based jobs.

        Example:
            # Every day at 2:30 AM
            @scheduler.cron(hour=2, minute=30)
            async def daily_job():
                await run_daily_task()

            # Every Monday at 9 AM
            @scheduler.cron(day_of_week='mon', hour=9)
            async def weekly_report():
                await send_report()
        """
        def decorator(func: Callable[..., Awaitable[Any]]):
            trigger_args = {}
            if year is not None:
                trigger_args["year"] = year
            if month is not None:
                trigger_args["month"] = month
            if day is not None:
                trigger_args["day"] = day
            if week is not None:
                trigger_args["week"] = week
            if day_of_week is not None:
                trigger_args["day_of_week"] = day_of_week
            if hour is not None:
                trigger_args["hour"] = hour
            if minute is not None:
                trigger_args["minute"] = minute
            if second is not None:
                trigger_args["second"] = second

            job = JobConfig(
                id=job_id or func.__name__,
                func=func,
                trigger=TriggerType.CRON,
                trigger_args=trigger_args,
            )

            if self._started:
                asyncio.create_task(self._add_job(job))
            else:
                self._pending_jobs.append(job)

            return func
        return decorator

    def at(
        self,
        run_date: datetime,
        job_id: Optional[str] = None,
    ):
        """
        Decorator for one-time scheduled jobs.

        Example:
            @scheduler.at(datetime(2024, 12, 31, 23, 59))
            async def new_years_countdown():
                print("Happy New Year!")
        """
        def decorator(func: Callable[..., Awaitable[Any]]):
            job = JobConfig(
                id=job_id or func.__name__,
                func=func,
                trigger=TriggerType.DATE,
                trigger_args={"run_date": run_date},
            )

            if self._started:
                asyncio.create_task(self._add_job(job))
            else:
                self._pending_jobs.append(job)

            return func
        return decorator

    async def add_interval_job(
        self,
        func: Callable[..., Awaitable[Any]],
        job_id: str,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ):
        """Programmatically add an interval job."""
        job = JobConfig(
            id=job_id,
            func=func,
            trigger=TriggerType.INTERVAL,
            trigger_args={
                "seconds": seconds,
                "minutes": minutes,
                "hours": hours,
            },
            args=args,
            kwargs=kwargs or {},
        )

        if self._started:
            await self._add_job(job)
        else:
            self._pending_jobs.append(job)

    async def add_cron_job(
        self,
        func: Callable[..., Awaitable[Any]],
        job_id: str,
        cron_expression: Optional[str] = None,
        hour: Optional[int] = None,
        minute: Optional[int] = None,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Programmatically add a cron job.

        Args:
            func: Async function to run
            job_id: Unique job ID
            cron_expression: Cron string (e.g., "0 2 * * *") OR use hour/minute
            hour: Hour (0-23)
            minute: Minute (0-59)
        """
        trigger_args = {}

        if cron_expression:
            # Parse cron expression: minute hour day month day_of_week
            parts = cron_expression.split()
            if len(parts) >= 5:
                trigger_args["minute"] = parts[0]
                trigger_args["hour"] = parts[1]
                trigger_args["day"] = parts[2]
                trigger_args["month"] = parts[3]
                trigger_args["day_of_week"] = parts[4]
        else:
            if hour is not None:
                trigger_args["hour"] = hour
            if minute is not None:
                trigger_args["minute"] = minute

        job = JobConfig(
            id=job_id,
            func=func,
            trigger=TriggerType.CRON,
            trigger_args=trigger_args,
            args=args,
            kwargs=kwargs or {},
        )

        if self._started:
            await self._add_job(job)
        else:
            self._pending_jobs.append(job)

    async def remove_job(self, job_id: str):
        """Remove a job by ID."""
        scheduler = await self._get_scheduler()
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass  # Job may not exist

    async def pause_job(self, job_id: str):
        """Pause a job."""
        scheduler = await self._get_scheduler()
        scheduler.pause_job(job_id)

    async def resume_job(self, job_id: str):
        """Resume a paused job."""
        scheduler = await self._get_scheduler()
        scheduler.resume_job(job_id)

    async def get_jobs(self) -> List[Dict[str, Any]]:
        """Get all scheduled jobs."""
        scheduler = await self._get_scheduler()
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger),
            })
        return jobs


# Convenience function for FastAPI lifespan
def create_scheduler_lifespan(scheduler: TaskScheduler):
    """
    Create a FastAPI lifespan context manager for the scheduler.

    Example:
        from fastapi import FastAPI
        from contextlib import asynccontextmanager

        scheduler = TaskScheduler()

        @scheduler.interval(seconds=60)
        async def periodic_task():
            print("Running...")

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with create_scheduler_lifespan(scheduler):
                yield

        app = FastAPI(lifespan=lifespan)
    """
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan_context():
        await scheduler.start()
        try:
            yield scheduler
        finally:
            await scheduler.shutdown()

    return lifespan_context()
