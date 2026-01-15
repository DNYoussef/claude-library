"""
Pipeline Executor Component

Lightweight async pipeline executor for orchestrating multi-step workflows.
Inspired by Prefect, Luigi, and other workflow engines but much simpler.

References:
- https://github.com/PrefectHQ/prefect
- https://github.com/pditommaso/awesome-pipeline
- https://github.com/spotify/luigi

Features:
- Async step execution
- Dependency resolution (DAG)
- Retry with backoff
- Step result caching
- Error handling and rollback
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Awaitable, TypeVar
from enum import Enum
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class StepStatus(Enum):
    """Pipeline step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class StepResult:
    """Result of a pipeline step execution."""
    step_name: str
    status: StepStatus
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    retries: int = 0


@dataclass
class StepConfig:
    """Configuration for a pipeline step."""
    name: str
    func: Callable[..., Awaitable[Any]]
    depends_on: List[str] = field(default_factory=list)
    retries: int = 0
    retry_delay: float = 1.0  # seconds
    timeout: Optional[float] = None  # seconds
    skip_on_error: bool = False  # Skip if dependency fails
    on_failure: Optional[Callable[[Exception], Awaitable[None]]] = None


@dataclass
class PipelineConfig:
    """Pipeline configuration."""
    name: str = "pipeline"
    max_concurrent: int = 5
    stop_on_first_failure: bool = False


class PipelineExecutor:
    """
    Async pipeline executor with DAG-based dependency resolution.

    Example:
        executor = PipelineExecutor()

        @executor.step("extract")
        async def extract_data():
            return await fetch_data()

        @executor.step("transform", depends_on=["extract"])
        async def transform_data(extract):
            return process(extract)

        @executor.step("load", depends_on=["transform"])
        async def load_data(transform):
            await save_to_db(transform)

        results = await executor.run()
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self._steps: Dict[str, StepConfig] = {}
        self._results: Dict[str, StepResult] = {}
        self._running = False

    def step(
        self,
        name: str,
        depends_on: Optional[List[str]] = None,
        retries: int = 0,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        skip_on_error: bool = False,
    ):
        """
        Decorator to register a pipeline step.

        Args:
            name: Unique step name
            depends_on: List of step names this depends on
            retries: Number of retries on failure
            retry_delay: Delay between retries (seconds)
            timeout: Step timeout (seconds)
            skip_on_error: Skip if dependency failed

        Example:
            @executor.step("process", depends_on=["fetch"], retries=3)
            async def process_data(fetch):
                return transform(fetch)
        """
        def decorator(func: Callable[..., Awaitable[Any]]):
            step_config = StepConfig(
                name=name,
                func=func,
                depends_on=depends_on or [],
                retries=retries,
                retry_delay=retry_delay,
                timeout=timeout,
                skip_on_error=skip_on_error,
            )
            self._steps[name] = step_config
            return func
        return decorator

    def add_step(
        self,
        name: str,
        func: Callable[..., Awaitable[Any]],
        depends_on: Optional[List[str]] = None,
        **kwargs,
    ):
        """Programmatically add a step."""
        step_config = StepConfig(
            name=name,
            func=func,
            depends_on=depends_on or [],
            **kwargs,
        )
        self._steps[name] = step_config

    def _topological_sort(self) -> List[str]:
        """
        Sort steps in dependency order (topological sort).

        Raises:
            ValueError: If circular dependency detected
        """
        # Build adjacency list
        graph: Dict[str, Set[str]] = {name: set() for name in self._steps}
        in_degree: Dict[str, int] = {name: 0 for name in self._steps}

        for name, step in self._steps.items():
            for dep in step.depends_on:
                if dep not in self._steps:
                    raise ValueError(f"Step '{name}' depends on unknown step '{dep}'")
                graph[dep].add(name)
                in_degree[name] += 1

        # Kahn's algorithm
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self._steps):
            raise ValueError("Circular dependency detected in pipeline")

        return result

    async def _execute_step(
        self,
        step: StepConfig,
    ) -> StepResult:
        """Execute a single step with retries."""
        result = StepResult(
            step_name=step.name,
            status=StepStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        # Check dependencies
        for dep_name in step.depends_on:
            dep_result = self._results.get(dep_name)
            if dep_result is None:
                result.status = StepStatus.FAILED
                result.error = f"Dependency '{dep_name}' not executed"
                return result

            if dep_result.status != StepStatus.FAILED:
                continue
            if step.skip_on_error:
                result.status = StepStatus.SKIPPED
                result.error = f"Skipped due to failed dependency '{dep_name}'"
                return result
            result.status = StepStatus.FAILED
            result.error = f"Dependency '{dep_name}' failed"
            return result

        # Build kwargs from dependency outputs
        kwargs = {}
        for dep_name in step.depends_on:
            dep_result = self._results[dep_name]
            kwargs[dep_name] = dep_result.output

        # Execute with retries
        last_error = None
        for attempt in range(step.retries + 1):
            try:
                if attempt > 0:
                    result.status = StepStatus.RETRYING
                    result.retries = attempt
                    await asyncio.sleep(step.retry_delay * (2 ** (attempt - 1)))

                # Execute with optional timeout
                if step.timeout:
                    output = await asyncio.wait_for(
                        step.func(**kwargs),
                        timeout=step.timeout,
                    )
                else:
                    output = await step.func(**kwargs)

                result.status = StepStatus.SUCCESS
                result.output = output
                break

            except asyncio.TimeoutError:
                last_error = f"Step timed out after {step.timeout}s"
                logger.warning(f"Step '{step.name}' timeout (attempt {attempt + 1})")

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Step '{step.name}' failed (attempt {attempt + 1}): {e}"
                )

                if step.on_failure:
                    try:
                        await step.on_failure(e)
                    except Exception:
                        pass

        if result.status != StepStatus.SUCCESS:
            result.status = StepStatus.FAILED
            result.error = last_error

        result.finished_at = datetime.utcnow()
        if result.started_at:
            result.duration_ms = (
                result.finished_at - result.started_at
            ).total_seconds() * 1000

        return result

    async def run(
        self,
        steps: Optional[List[str]] = None,
    ) -> Dict[str, StepResult]:
        """
        Execute the pipeline.

        Args:
            steps: Optional list of specific steps to run (with dependencies)

        Returns:
            Dict mapping step names to results
        """
        if self._running:
            raise RuntimeError("Pipeline is already running")

        self._running = True
        self._results = {}

        try:
            # Get execution order
            ordered_steps = self._topological_sort()

            # Filter to requested steps if specified
            if steps:
                # Include dependencies
                needed = set(steps)
                for step_name in steps:
                    self._collect_dependencies(step_name, needed)
                ordered_steps = [s for s in ordered_steps if s in needed]

            # Group steps by level (for parallel execution)
            levels = self._group_by_level(ordered_steps)

            for level in levels:
                # Execute steps in this level concurrently (up to max_concurrent)
                semaphore = asyncio.Semaphore(self.config.max_concurrent)

                async def run_with_semaphore(step_name: str):
                    async with semaphore:
                        step = self._steps[step_name]
                        result = await self._execute_step(step)
                        self._results[step_name] = result
                        return result

                tasks = [run_with_semaphore(name) for name in level]
                await asyncio.gather(*tasks)

                # Check for failures if stop_on_first_failure
                if self.config.stop_on_first_failure:
                    for name in level:
                        if self._results[name].status == StepStatus.FAILED:
                            logger.error(f"Pipeline stopped due to failure in '{name}'")
                            return self._results

            return self._results

        finally:
            self._running = False

    def _collect_dependencies(self, step_name: str, needed: Set[str]):
        """Recursively collect all dependencies for a step."""
        step = self._steps.get(step_name)
        if step:
            for dep in step.depends_on:
                if dep not in needed:
                    needed.add(dep)
                    self._collect_dependencies(dep, needed)

    def _group_by_level(self, ordered_steps: List[str]) -> List[List[str]]:
        """Group steps into execution levels (steps at same level can run in parallel)."""
        levels: List[List[str]] = []
        step_level: Dict[str, int] = {}

        for step_name in ordered_steps:
            step = self._steps[step_name]

            # Level is max level of dependencies + 1
            if step.depends_on:
                level = max(step_level.get(dep, 0) for dep in step.depends_on) + 1
            else:
                level = 0

            step_level[step_name] = level

            # Expand levels list if needed
            while len(levels) <= level:
                levels.append([])

            levels[level].append(step_name)

        return levels

    def get_results(self) -> Dict[str, StepResult]:
        """Get current results."""
        return self._results.copy()

    def reset(self):
        """Reset pipeline state."""
        self._results = {}

    def visualize(self) -> str:
        """Generate ASCII visualization of the pipeline."""
        lines = [f"Pipeline: {self.config.name}", "=" * 40]

        try:
            ordered = self._topological_sort()
            levels = self._group_by_level(ordered)

            for i, level in enumerate(levels):
                lines.append(f"Level {i}:")
                for step_name in level:
                    step = self._steps[step_name]
                    deps = f" <- [{', '.join(step.depends_on)}]" if step.depends_on else ""
                    status = ""
                    if step_name in self._results:
                        result = self._results[step_name]
                        status = f" [{result.status.value}]"
                    lines.append(f"  - {step_name}{deps}{status}")

        except ValueError as e:
            lines.append(f"Error: {e}")

        return "\n".join(lines)
