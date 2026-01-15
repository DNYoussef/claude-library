# loopctl - Loop Control for Cognitive Architecture

Provides the FrozenHarness evaluation system for grading artifacts in the Ralph loop system.

## Overview

The loopctl component implements an immutable evaluation harness that serves as the single source of truth for quality metrics. It is designed to prevent Goodhart's Law issues by keeping evaluation separate from the optimizing system.

## Key Components

### FrozenHarness

The core evaluation class that grades artifacts using either:
1. **CLI Evaluator** (preferred): Real LLM-based evaluation via Claude CLI
2. **Heuristic Fallback**: Pattern-based evaluation when CLI unavailable

```python
from cognitive_architecture.loopctl import FrozenHarness

harness = FrozenHarness(loop_dir=Path(".loop"))
metrics = harness.grade(artifact_path=Path("output.txt"))

print(f"Task Accuracy: {metrics['task_accuracy']:.2f}")
print(f"Token Efficiency: {metrics['token_efficiency']:.2f}")
print(f"Edge Robustness: {metrics['edge_robustness']:.2f}")
print(f"Epistemic Consistency: {metrics['epistemic_consistency']:.2f}")
print(f"Overall: {metrics['overall']:.2f}")
```

### Emergency Stop

Kill switch for halting runaway loops:

```python
from cognitive_architecture.loopctl import check_emergency_stop

should_stop, reason = check_emergency_stop()
if should_stop:
    print(reason)
    exit(1)
```

Trigger methods:
- Create `.meta-loop-stop` file in current or home directory
- Set `META_LOOP_EMERGENCY_STOP=true` environment variable

## Metrics

| Metric | Range | Description |
|--------|-------|-------------|
| task_accuracy | 0.0-1.0 | Did the artifact accomplish its task? |
| token_efficiency | 0.0-1.0 | Is the output concise? |
| edge_robustness | 0.0-1.0 | Does it handle edge cases? |
| epistemic_consistency | 0.0-1.0 | Are claims properly qualified? |
| overall | 0.0-1.0 | Weighted average of all metrics |

Default weights: accuracy=0.4, efficiency=0.2, robustness=0.2, epistemic=0.2

## Integrity Verification

The harness includes hash-based integrity verification:

```python
harness = FrozenHarness()
print(f"Harness Hash: {harness.current_hash}")

# Verify integrity against expected hash
if not harness.verify_integrity(expected_hash):
    print("HALT: Harness integrity check failed")
```

## VERIX Notation

This component follows VERIX epistemic notation:

```
[assert|confident] FrozenHarness grades artifacts immutably
[ground:architecture-spec] [conf:0.95] [state:confirmed]
```

## Dependencies

- Python 3.9+
- Optional: Claude CLI for LLM-based evaluation
