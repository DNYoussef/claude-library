"""
Pipeline Executor Component

Lightweight async pipeline executor for multi-step workflows.

Features:
- DAG-based dependency resolution
- Parallel execution of independent steps
- Retry with exponential backoff
- Timeout support
- Step result caching

References:
- https://github.com/PrefectHQ/prefect (inspiration)
- https://github.com/spotify/luigi (inspiration)

Example:
    from library.components.orchestration.pipeline_executor import PipelineExecutor

    executor = PipelineExecutor()

    @executor.step("fetch")
    async def fetch_data():
        return await api.get_data()

    @executor.step("process", depends_on=["fetch"], retries=3)
    async def process_data(fetch):
        return transform(fetch)

    @executor.step("save", depends_on=["process"])
    async def save_data(process):
        await db.save(process)

    results = await executor.run()
"""

from .executor import (
    PipelineExecutor,
    PipelineConfig,
    StepConfig,
    StepResult,
    StepStatus,
)

__all__ = [
    "PipelineExecutor",
    "PipelineConfig",
    "StepConfig",
    "StepResult",
    "StepStatus",
]
