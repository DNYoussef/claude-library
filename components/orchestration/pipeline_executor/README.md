# Pipeline Executor Component

Lightweight async pipeline executor for orchestrating multi-step workflows.

## Features

- DAG-based dependency resolution
- Parallel execution of independent steps
- Retry with exponential backoff
- Timeout support
- Step result passing
- Error handling

## Usage

### Basic Pipeline

```python
from library.components.orchestration.pipeline_executor import PipelineExecutor

executor = PipelineExecutor()

@executor.step("extract")
async def extract_data():
    data = await fetch_from_api()
    return data

@executor.step("transform", depends_on=["extract"])
async def transform_data(extract):  # Receives output from "extract"
    return process(extract)

@executor.step("load", depends_on=["transform"])
async def load_data(transform):
    await save_to_database(transform)

# Run pipeline
results = await executor.run()

# Check results
for name, result in results.items():
    print(f"{name}: {result.status} ({result.duration_ms}ms)")
```

### Parallel Execution

Steps without dependencies on each other run in parallel:

```python
@executor.step("fetch_users")
async def fetch_users():
    return await api.get_users()

@executor.step("fetch_orders")
async def fetch_orders():
    return await api.get_orders()

@executor.step("merge", depends_on=["fetch_users", "fetch_orders"])
async def merge_data(fetch_users, fetch_orders):
    # Both fetches run in parallel, merge runs after both complete
    return combine(fetch_users, fetch_orders)
```

### Retry Configuration

```python
@executor.step(
    "unreliable_api",
    retries=3,           # Retry up to 3 times
    retry_delay=2.0,     # Start with 2 second delay
    timeout=30.0,        # 30 second timeout
)
async def call_api():
    return await flaky_api.call()
```

### Error Handling

```python
@executor.step(
    "optional_step",
    depends_on=["main_step"],
    skip_on_error=True,  # Skip if dependency fails
)
async def optional_enhancement(main_step):
    return enhance(main_step)
```

### Programmatic Step Addition

```python
async def my_step(previous_data):
    return process(previous_data)

executor.add_step(
    name="dynamic_step",
    func=my_step,
    depends_on=["source_step"],
    retries=2,
)
```

### Pipeline Visualization

```python
print(executor.visualize())
# Output:
# Pipeline: my-pipeline
# ========================================
# Level 0:
#   - extract
#   - fetch_config
# Level 1:
#   - transform <- [extract, fetch_config]
# Level 2:
#   - load <- [transform]
```

## Configuration

```python
from library.components.orchestration.pipeline_executor import (
    PipelineExecutor,
    PipelineConfig,
)

config = PipelineConfig(
    name="etl-pipeline",
    max_concurrent=5,           # Max parallel steps
    stop_on_first_failure=True, # Stop pipeline on first error
)

executor = PipelineExecutor(config)
```

## StepResult

```python
@dataclass
class StepResult:
    step_name: str
    status: StepStatus  # PENDING, RUNNING, SUCCESS, FAILED, SKIPPED
    output: Any
    error: Optional[str]
    started_at: datetime
    finished_at: datetime
    duration_ms: float
    retries: int
```

## Sources

- [Prefect](https://github.com/PrefectHQ/prefect) - Workflow orchestration
- [Luigi](https://github.com/spotify/luigi) - Pipeline framework
- [awesome-pipeline](https://github.com/pditommaso/awesome-pipeline) - Pipeline toolkit list
