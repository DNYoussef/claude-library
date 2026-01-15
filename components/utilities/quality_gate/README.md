# Quality Gate Component

Async quality gates with threshold validation for pipeline orchestration.

## Features

- **SYNC_GATE**: Wait for parallel operations to complete
- **QUALITY_GATE**: Validate output passes quality threshold
- **DEPENDENCY_GATE**: Wait for upstream tasks
- **COMPILE_GATE**: Final validation before publish
- **RichMetricResult**: Scores with feedback for refinement loops

## LEGO Integration

This component imports shared types from `library.common.types`:

```python
from library.common.types import QualityResult, Severity, Violation
```

## Installation

```python
from library.components.utilities.quality_gate import (
    GateManager,
    create_quality_gate,
    create_sync_gate,
    RichMetricResult
)
```

## Usage

### Basic Quality Gate

```python
import asyncio
from library.components.utilities.quality_gate import (
    GateManager,
    create_quality_gate
)

async def style_score():
    # Your scoring logic
    return 0.85

async def main():
    manager = GateManager()

    # Register a quality gate
    gate = create_quality_gate("style_check", style_score, threshold=0.7)
    manager.register_gate(gate)

    # Check the gate
    result = await manager.check_gate("style_check")
    print(f"Passed: {result.passed}, Score: {result.details['score']}")

asyncio.run(main())
```

### Sync Gate (Wait for Parallel Tasks)

```python
manager = GateManager()

# Create gate waiting for multiple tasks
gate = create_sync_gate("parallel_complete", ["task_a", "task_b", "task_c"])
manager.register_gate(gate)

# Mark tasks as they complete
manager.mark_task_complete("task_a", {"result": "done"})
manager.mark_task_complete("task_b", {"result": "done"})
manager.mark_task_complete("task_c", {"result": "done"})

# Now the gate will pass
result = await manager.check_gate("parallel_complete")
```

### Rich Metric Results

```python
from library.components.utilities.quality_gate import RichMetricResult

async def advanced_metric():
    score = 0.85
    feedback = "Good overall structure, minor style issues in paragraphs 3 and 7"
    return RichMetricResult(score, feedback)

# The result carries both score and explanation
gate = create_quality_gate("detailed_check", advanced_metric, 0.7)
manager.register_gate(gate)
result = await manager.check_gate("detailed_check")
print(result.details["feedback"])  # Access the explanation
```

### Dependency Gate

```python
# Wait for upstream tasks before proceeding
gate = create_dependency_gate("ready_for_deploy", ["tests_passed", "review_approved"])
manager.register_gate(gate)

manager.mark_task_complete("tests_passed")
manager.mark_task_complete("review_approved")

result = await manager.check_gate("ready_for_deploy")
```

### Compile Gate (Multiple Validation Checks)

```python
def check_file_exists():
    return os.path.exists("output/blog.md")

def check_images_generated():
    return os.path.exists("output/images/")

async def check_slop_score():
    score = await calculate_slop()
    return score < 0.3  # Less than 30% slop

gate = create_compile_gate("ready_to_publish", [
    check_file_exists,
    check_images_generated,
    check_slop_score
])
manager.register_gate(gate)

result = await manager.check_gate("ready_to_publish")
print(f"Passed checks: {result.details['passed']}")
print(f"Failed checks: {result.details['failed']}")
```

### Converting to QualityResult

```python
from library.common.types import QualityResult

result = await manager.check_gate("style_check")
quality_result: QualityResult = result.to_quality_result()
print(f"Score: {quality_result.score}")
print(f"Violations: {len(quality_result.violations)}")
```

## API Reference

### GateType

```python
class GateType(Enum):
    SYNC = "SYNC_GATE"           # Wait for parallel operations
    QUALITY = "QUALITY_GATE"     # Score must pass threshold
    DEPENDENCY = "DEPENDENCY_GATE"  # Wait for upstream completion
    COMPILE = "COMPILE_GATE"     # Multiple validation checks
```

### GateConfig

```python
@dataclass
class GateConfig:
    id: str                      # Unique identifier
    gate_type: GateType          # Type of gate
    description: str = ""        # Human-readable description
    wait_for: List[str]          # Task IDs (SYNC_GATE)
    threshold: float = 0.7       # Quality threshold (QUALITY_GATE)
    metric_fn: Callable          # Score function (QUALITY_GATE)
    requires: List[str]          # Dependencies (DEPENDENCY_GATE)
    checks: List[Callable]       # Validators (COMPILE_GATE)
    timeout_seconds: float = 300.0
    on_fail: str = "block"       # "block", "warn", "ralph_wiggum_loop"
```

### GateResult

```python
@dataclass
class GateResult:
    gate_id: str
    gate_type: GateType
    status: GateStatus
    passed: bool
    message: str
    details: Dict[str, Any]
    timestamp: str
    wait_time_seconds: float
```

### GateManager

```python
class GateManager:
    def register_gate(config: GateConfig) -> None
    def mark_task_complete(task_id: str, result: Any = None) -> None
    async def check_gate(gate_id: str) -> GateResult
    async def wait_for_gate(gate_id: str) -> GateResult  # Raises on failure
    def get_all_results() -> Dict[str, GateResult]
    def reset() -> None
```

## Integration with Content Pipeline

```python
# Create all gates for content pipeline
manager = GateManager()

# Phase gates
manager.register_gate(create_sync_gate(
    "transcription_complete",
    ["video_1", "video_2", "video_3"]
))

manager.register_gate(create_sync_gate(
    "analysis_complete",
    ["gemini_analysis", "codex_analysis", "claude_analysis"]
))

manager.register_gate(create_quality_gate(
    "style_gate",
    style_metric,
    threshold=0.7
))

manager.register_gate(create_quality_gate(
    "slop_gate",
    lambda: 1.0 - slop_detector.analyze(content),  # Invert: lower slop = higher score
    threshold=0.7  # Equivalent to <30% slop
))

manager.register_gate(create_compile_gate(
    "publish_ready",
    [blog_exists, images_exist, slop_passed, git_clean]
))
```

## Error Handling

```python
from library.components.utilities.quality_gate import GateFailedError

try:
    result = await manager.wait_for_gate("critical_gate")
except GateFailedError as e:
    print(f"Gate {e.gate_id} failed: {e.result.message}")
    # Handle failure - maybe trigger Ralph Wiggum loop
```

## Source

Extracted and generalized from `scripts/content-pipeline/gates.py`
