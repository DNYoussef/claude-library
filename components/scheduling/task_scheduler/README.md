# Task Scheduler Component

Async task scheduling for FastAPI applications with APScheduler.

## Features

- Interval-based jobs (every N seconds/minutes)
- Cron-based jobs (crontab syntax)
- One-time scheduled jobs
- Decorator-based registration
- FastAPI lifespan integration
- Job pause/resume/remove
- **Cron expression validation** (extracted from life-os-dashboard)
- **Job/Task status enums** for persistence layers

## Installation

```bash
pip install apscheduler
```

## Usage

### Basic Setup

```python
from library.components.scheduling.task_scheduler import TaskScheduler

scheduler = TaskScheduler()

# Interval job - every 30 seconds
@scheduler.interval(seconds=30)
async def heartbeat():
    print(f"Heartbeat at {datetime.now()}")

# Interval job - every 5 minutes
@scheduler.interval(minutes=5)
async def check_status():
    await update_service_status()
```

### Cron Jobs

```python
# Daily at 2:00 AM
@scheduler.cron(hour=2, minute=0)
async def daily_backup():
    await backup_database()

# Every Monday at 9:00 AM
@scheduler.cron(day_of_week='mon', hour=9)
async def weekly_report():
    await send_weekly_report()

# First day of each month
@scheduler.cron(day=1, hour=0, minute=0)
async def monthly_cleanup():
    await archive_old_data()
```

### One-Time Jobs

```python
from datetime import datetime

@scheduler.at(datetime(2024, 12, 31, 23, 59))
async def new_years_countdown():
    await broadcast_message("Happy New Year!")
```

### FastAPI Integration

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

scheduler = TaskScheduler()

@scheduler.interval(seconds=60)
async def periodic_task():
    print("Running periodic task...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await scheduler.start()
    yield
    await scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/jobs")
async def list_jobs():
    return await scheduler.get_jobs()
```

### Programmatic Job Management

```python
# Add job programmatically
await scheduler.add_cron_job(
    func=my_async_function,
    job_id="custom-job",
    cron_expression="0 2 * * *",  # 2 AM daily
)

# Or with hour/minute
await scheduler.add_interval_job(
    func=health_check,
    job_id="health-check",
    minutes=5,
)

# Manage jobs
await scheduler.pause_job("custom-job")
await scheduler.resume_job("custom-job")
await scheduler.remove_job("custom-job")
```

## Configuration

```python
from library.components.scheduling.task_scheduler import (
    TaskScheduler,
    SchedulerConfig,
)

config = SchedulerConfig(
    timezone="America/New_York",
    job_defaults={
        "coalesce": True,      # Combine missed runs
        "max_instances": 3,     # Max concurrent instances
        "misfire_grace_time": 60,  # Grace period (seconds)
    },
)

scheduler = TaskScheduler(config)
```

## Cron Expression Reference

| Field | Values |
|-------|--------|
| minute | 0-59 |
| hour | 0-23 |
| day | 1-31 |
| month | 1-12 |
| day_of_week | 0-6 or mon,tue,wed,thu,fri,sat,sun |

## Cron Validation

Validate cron expressions before storing or using them:

```python
from library.components.scheduling.task_scheduler import (
    validate_cron_expression,
    parse_cron_expression,
)

# Validate
is_valid, error = validate_cron_expression("0 2 * * *")
if not is_valid:
    raise ValueError(f"Invalid cron: {error}")

# Parse to APScheduler args
args = parse_cron_expression("0 2 * * *")
# Returns: {'minute': '0', 'hour': '2', 'day': '*', 'month': '*', 'day_of_week': '*'}
```

Supported patterns:
- Plain values: `0`, `15`, `mon`
- Wildcards: `*`
- Steps: `*/5`
- Ranges: `1-5`
- Lists: `0,15,30,45`
- Day names: `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`

## Status Enums

For persistence layers (databases, APIs), use these status enums:

```python
from library.components.scheduling.task_scheduler import JobStatus, TaskStatus

# Job execution status
status = JobStatus.PENDING  # pending, running, completed, failed, paused, disabled

# Kanban workflow status (5-state)
task_status = TaskStatus.IN_PROGRESS  # todo, in_progress, in_review, done, cancelled
```

These enums are derived from the life-os-dashboard ScheduledTask model for consistency.

## Sources

- [APScheduler](https://github.com/agronholm/apscheduler) - Advanced Python Scheduler
- [fastapi-scheduler](https://github.com/amisadmin/fastapi-scheduler) - FastAPI extension
- [APScheduler Examples](https://github.com/agronholm/apscheduler/tree/master/examples)

## Extracted From

- **life-os-dashboard** (`D:\Projects\life-os-dashboard`)
  - `backend/app/models/scheduled_task.py` - Status enums, Kanban workflow
  - `backend/app/crud/scheduled_task.py` - CRUD patterns (not extracted - app-specific)
  - `backend/app/services/node_handlers/trigger_handler.py` - Trigger types
