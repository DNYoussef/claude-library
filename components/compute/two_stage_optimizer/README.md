# Two-Stage Multi-Objective Optimizer

Implements the **Dual MOO** (Multi-Objective Optimization) system from `DUAL-MOO-CONTROL-SPEC.md`.

## Overview

This component provides:
- **8-Objective Vector**: Complete fitness metrics for Pareto optimization
- **Constraint System**: Immutable safety bounds, anti-cancer constraints, quality gates
- **Two-Stage Optimization**: GlobalMOO 5D exploration + PyMOO NSGA-II 14D refinement
- **Named Modes**: Pre-distilled configurations (audit, speed, research, robust, balanced)

## 8-Objective Vector

| # | Metric | Direction | Description |
|---|--------|-----------|-------------|
| 1 | `Q_task` | MAXIMIZE | Task success / rubric score |
| 2 | `Q_quality` | MAXIMIZE | Quality-gate composite (sigma >= 4.0) |
| 3 | `G_coverage` | MAXIMIZE | Edge-case coverage (anti-Goodhart) |
| 4 | `R_diversity` | MAXIMIZE | Output entropy (anti-overfit) |
| 5 | `C_cost` | MINIMIZE | Tokens/run or $/run |
| 6 | `T_latency` | MINIMIZE | Wall-clock latency (ms) |
| 7 | `E_calib` | MINIMIZE | Calibration error |
| 8 | `D_regress` | MINIMIZE | Regression rate |

## Usage

### Basic Optimization

```python
from two_stage_optimizer import TwoStageOptimizer, ObjectiveVector

# Create optimizer with baseline
baseline = ObjectiveVector(
    Q_task=0.85,
    Q_quality=0.80,
    G_coverage=0.75,
    R_diversity=0.70,
    C_cost=1500.0,
    T_latency=500.0,
    E_calib=0.10,
    D_regress=0.02,
)

optimizer = TwoStageOptimizer(
    baseline=baseline,
    population_size=50,
    max_generations=100,
)

result = optimizer.optimize()

if result.success:
    print(f"Pareto front: {len(result.pareto_front)} candidates")
    print(f"Best Q_task: {result.best_candidate.objectives.Q_task:.3f}")
    print(f"Named modes: {list(result.named_modes.keys())}")
```

### Computing Objectives

```python
from two_stage_optimizer import create_objective_vector

objectives = create_objective_vector(
    task_results=[{"score": 0.9, "weight": 1.0}],
    quality_metrics={"sigma_level": 4.5, "dpmo": 3000},
    coverage_data={"total_cases": 100, "covered_cases": 85},
    outputs=["response 1", "response 2", "response 3"],
    token_count=5000,
    latency_samples=[450.0, 480.0, 520.0],
    calibration_data=[(0.9, True), (0.8, True), (0.7, False)],
    baseline_scores={"coding": 0.85},
    current_scores={"coding": 0.87},
)
```

### Using Named Modes

```python
from two_stage_optimizer import NAMED_MODES

# Get pre-defined mode
audit_mode = NAMED_MODES["audit"]
print(f"Audit mode: {audit_mode.expected_accuracy:.3f} accuracy")

# Apply mode settings
settings = audit_mode.decision_vars.to_dict()
```

### Checking Constraints

```python
from two_stage_optimizer import ConstraintChecker, ObjectiveVector

checker = ConstraintChecker(baseline=baseline)

objectives = ObjectiveVector(Q_task=0.90, Q_quality=0.85, ...)
decision_vars = {"evidential_frame_weight": 0.95, ...}
quality_metrics = {"sigma_level": 4.5, "dpmo": 3000, ...}

result = checker.check(objectives, decision_vars, quality_metrics)

if not result.all_satisfied:
    for violation in result.hard_violations:
        print(f"Violation: {violation.constraint_name}")
```

## Constraints

### Immutable Safety Bounds
- `evidential_frame_weight >= 0.30` (CRITICAL)
- `aspectual_frame_weight >= 0.10`

### Quality Gates
- Six Sigma: `sigma_level >= 4.0`
- DPMO: `dpmo <= 6210`
- Theater Risk: `theater_risk < 0.20`
- Security: `security_critical_count == 0`
- NASA Compliance: `nasa_compliance >= 0.95`

### Anti-Cancer Constraints
- `D_regress <= R_max` (default 0.03)
- `E_calib <= C_max` (default 0.15)
- `G_coverage >= Cov_min` (default 0.80)

### Baseline Preservation
- `Q_task >= baseline.Q_task * tau` (default tau=0.95)
- `Q_quality >= baseline.Q_quality * tau`

## Named Modes

| Mode | Accuracy | Efficiency | Use Case |
|------|----------|------------|----------|
| `audit` | 0.960 | 0.763 | Code review, compliance |
| `speed` | 0.734 | 0.950 | Quick tasks, prototyping |
| `research` | 0.980 | 0.824 | Content analysis, deep work |
| `robust` | 0.960 | 0.769 | Production code, critical paths |
| `balanced` | 0.882 | 0.928 | General purpose |

## Integration

### Memory MCP Namespace
```yaml
memory_mcp_writes:
  namespace: "loop3/dual-moo/{timestamp}"
  tags:
    WHO: "dual-moo-optimizer:1.0.0"
    WHEN: "{ISO8601}"
    PROJECT: "meta-optimization"
    WHY: "loop3-pareto-convergence"
```

### Cascade Update Flow
```
Named Modes -> templates -> prompt-architect -> commands -> agents -> skills -> playbooks -> hooks
```

## References

- [DUAL-MOO-CONTROL-SPEC.md](../../../2026-AI-EXOSKELETON/2026-DUAL-MOO-CONTROL-SPEC.md)
- [ORGAN-MAP](../../../2026-AI-EXOSKELETON/2026-EXOSKELETON-ORGAN-MAP.md)
- [GlobalMOO API](https://app.globalmoo.com/api)
- [PyMOO](https://pymoo.org/)
