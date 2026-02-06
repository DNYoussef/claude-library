"""
Constraints for Dual MOO Optimization

Implements constraints from DUAL-MOO-CONTROL-SPEC.md Section 3:
- Immutable safety bounds
- Anti-cancer constraints
- Quality gate constraints
- Baseline preservation constraints
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

try:
    from .objectives import ObjectiveVector
except ImportError:
    from objectives import ObjectiveVector


class ConstraintType(Enum):
    """Type of constraint."""
    IMMUTABLE = "immutable"      # Cannot be violated ever
    ANTI_CANCER = "anti_cancer"  # Anti-Goodhart constraints
    QUALITY_GATE = "quality_gate"  # Hard pass/fail checks
    BASELINE = "baseline"        # Baseline preservation


class ConstraintResult(Enum):
    """Result of constraint check."""
    SATISFIED = "satisfied"
    VIOLATED = "violated"
    WARNING = "warning"


@dataclass
class Constraint:
    """Definition of a single constraint."""
    name: str
    constraint_type: ConstraintType
    description: str
    threshold: float
    operator: str  # ">=", "<=", "==", "<", ">"
    metric_name: str
    is_hard: bool = True  # Hard constraints reject candidates

    def check(self, value: float) -> ConstraintResult:
        """Check if constraint is satisfied."""
        if self.operator == ">=":
            satisfied = value >= self.threshold
        elif self.operator == "<=":
            satisfied = value <= self.threshold
        elif self.operator == "==":
            satisfied = abs(value - self.threshold) < 1e-6
        elif self.operator == ">":
            satisfied = value > self.threshold
        elif self.operator == "<":
            satisfied = value < self.threshold
        else:
            raise ValueError(f"Unknown operator: {self.operator}")

        return ConstraintResult.SATISFIED if satisfied else ConstraintResult.VIOLATED


@dataclass
class ConstraintViolation:
    """Record of a constraint violation."""
    constraint_name: str
    constraint_type: ConstraintType
    expected: str
    actual: float
    is_hard: bool


@dataclass
class ConstraintCheckResult:
    """Result of checking all constraints."""
    all_satisfied: bool
    hard_violations: List[ConstraintViolation]
    soft_violations: List[ConstraintViolation]
    warnings: List[str]


# ===========================================
# IMMUTABLE SAFETY BOUNDS (Section 3.1)
# ===========================================

IMMUTABLE_CONSTRAINTS = [
    Constraint(
        name="evidential_frame_min",
        constraint_type=ConstraintType.IMMUTABLE,
        description="Evidential frame weight cannot go below 0.30",
        threshold=0.30,
        operator=">=",
        metric_name="evidential_frame_weight",
        is_hard=True,
    ),
    Constraint(
        name="aspectual_frame_min",
        constraint_type=ConstraintType.IMMUTABLE,
        description="Aspectual frame weight cannot go below 0.10",
        threshold=0.10,
        operator=">=",
        metric_name="aspectual_frame_weight",
        is_hard=True,
    ),
]


# ===========================================
# ANTI-CANCER CONSTRAINTS (Section 3.2)
# ===========================================

def get_anti_cancer_constraints(
    R_max: float = 0.03,
    C_max: float = 0.15,
    Cov_min: float = 0.80,
) -> List[Constraint]:
    """
    Get anti-Goodhart constraints.

    Args:
        R_max: Maximum regression rate (default: 0.03)
        C_max: Maximum calibration error (default: 0.15)
        Cov_min: Minimum coverage (default: 0.80)

    Returns:
        List of anti-cancer constraints
    """
    return [
        Constraint(
            name="regression_ceiling",
            constraint_type=ConstraintType.ANTI_CANCER,
            description=f"Regression rate must stay <= {R_max}",
            threshold=R_max,
            operator="<=",
            metric_name="D_regress",
            is_hard=True,
        ),
        Constraint(
            name="calibration_ceiling",
            constraint_type=ConstraintType.ANTI_CANCER,
            description=f"Calibration error must stay <= {C_max}",
            threshold=C_max,
            operator="<=",
            metric_name="E_calib",
            is_hard=True,
        ),
        Constraint(
            name="coverage_floor",
            constraint_type=ConstraintType.ANTI_CANCER,
            description=f"Coverage must stay >= {Cov_min}",
            threshold=Cov_min,
            operator=">=",
            metric_name="G_coverage",
            is_hard=True,
        ),
    ]


# ===========================================
# QUALITY GATE CONSTRAINTS (Section 3.3)
# ===========================================

QUALITY_GATE_CONSTRAINTS = [
    Constraint(
        name="sigma_level",
        constraint_type=ConstraintType.QUALITY_GATE,
        description="Six Sigma quality level >= 4.0",
        threshold=4.0,
        operator=">=",
        metric_name="sigma_level",
        is_hard=True,
    ),
    Constraint(
        name="dpmo",
        constraint_type=ConstraintType.QUALITY_GATE,
        description="Defects per million opportunities <= 6210",
        threshold=6210,
        operator="<=",
        metric_name="dpmo",
        is_hard=True,
    ),
    Constraint(
        name="theater_risk",
        constraint_type=ConstraintType.QUALITY_GATE,
        description="Theater detection risk < 20%",
        threshold=0.20,
        operator="<",
        metric_name="theater_risk",
        is_hard=True,
    ),
    Constraint(
        name="security_critical",
        constraint_type=ConstraintType.QUALITY_GATE,
        description="Zero critical security vulnerabilities",
        threshold=0,
        operator="==",
        metric_name="security_critical_count",
        is_hard=True,
    ),
    Constraint(
        name="nasa_compliance",
        constraint_type=ConstraintType.QUALITY_GATE,
        description="NASA Power of 10 compliance >= 95%",
        threshold=0.95,
        operator=">=",
        metric_name="nasa_compliance",
        is_hard=True,
    ),
]


# ===========================================
# BASELINE PRESERVATION CONSTRAINTS (Section 3.4)
# ===========================================

def get_baseline_constraints(
    baseline: ObjectiveVector,
    tau: float = 0.95,
) -> List[Constraint]:
    """
    Get baseline preservation constraints.

    Args:
        baseline: Baseline objective vector to preserve
        tau: Preservation threshold (default: 0.95 = no more than 5% regression)

    Returns:
        List of baseline preservation constraints
    """
    return [
        Constraint(
            name="Q_task_preservation",
            constraint_type=ConstraintType.BASELINE,
            description=f"Q_task >= baseline * {tau}",
            threshold=baseline.Q_task * tau,
            operator=">=",
            metric_name="Q_task",
            is_hard=True,
        ),
        Constraint(
            name="Q_quality_preservation",
            constraint_type=ConstraintType.BASELINE,
            description=f"Q_quality >= baseline * {tau}",
            threshold=baseline.Q_quality * tau,
            operator=">=",
            metric_name="Q_quality",
            is_hard=True,
        ),
    ]


class ConstraintChecker:
    """
    Checks constraints on objective vectors and decision variables.
    """

    def __init__(
        self,
        baseline: Optional[ObjectiveVector] = None,
        tau: float = 0.95,
        R_max: float = 0.03,
        C_max: float = 0.15,
        Cov_min: float = 0.80,
    ):
        """
        Initialize constraint checker.

        Args:
            baseline: Baseline objective vector (None if no baseline)
            tau: Baseline preservation threshold
            R_max: Maximum regression rate
            C_max: Maximum calibration error
            Cov_min: Minimum coverage
        """
        self.baseline = baseline
        self.tau = tau

        # Collect all constraints
        self.constraints: List[Constraint] = []

        # Immutable constraints (always active)
        self.constraints.extend(IMMUTABLE_CONSTRAINTS)

        # Anti-cancer constraints
        self.constraints.extend(get_anti_cancer_constraints(R_max, C_max, Cov_min))

        # Quality gate constraints
        self.constraints.extend(QUALITY_GATE_CONSTRAINTS)

        # Baseline preservation (if baseline provided)
        if baseline is not None:
            self.constraints.extend(get_baseline_constraints(baseline, tau))

    def check(
        self,
        objectives: ObjectiveVector,
        decision_vars: Dict[str, float],
        quality_metrics: Dict[str, Any],
    ) -> ConstraintCheckResult:
        """
        Check all constraints.

        Args:
            objectives: Current objective vector
            decision_vars: Decision variables (frame weights, etc.)
            quality_metrics: Quality gate metrics

        Returns:
            ConstraintCheckResult with violations
        """
        hard_violations: List[ConstraintViolation] = []
        soft_violations: List[ConstraintViolation] = []
        warnings: List[str] = []

        # Combine all metrics for checking
        all_metrics = {
            **objectives.to_dict(),
            **decision_vars,
            **quality_metrics,
        }

        for constraint in self.constraints:
            metric_name = constraint.metric_name
            if metric_name not in all_metrics:
                warnings.append(f"Metric '{metric_name}' not found for constraint '{constraint.name}'")
                continue

            value = all_metrics[metric_name]
            result = constraint.check(value)

            if result == ConstraintResult.VIOLATED:
                violation = ConstraintViolation(
                    constraint_name=constraint.name,
                    constraint_type=constraint.constraint_type,
                    expected=f"{constraint.metric_name} {constraint.operator} {constraint.threshold}",
                    actual=value,
                    is_hard=constraint.is_hard,
                )

                if constraint.is_hard:
                    hard_violations.append(violation)
                else:
                    soft_violations.append(violation)

        return ConstraintCheckResult(
            all_satisfied=len(hard_violations) == 0,
            hard_violations=hard_violations,
            soft_violations=soft_violations,
            warnings=warnings,
        )

    def is_feasible(
        self,
        objectives: ObjectiveVector,
        decision_vars: Dict[str, float],
        quality_metrics: Dict[str, Any],
    ) -> bool:
        """
        Quick check if candidate is feasible (no hard violations).

        Args:
            objectives: Current objective vector
            decision_vars: Decision variables
            quality_metrics: Quality gate metrics

        Returns:
            True if all hard constraints are satisfied
        """
        result = self.check(objectives, decision_vars, quality_metrics)
        return result.all_satisfied


__all__ = [
    "ConstraintType",
    "ConstraintResult",
    "Constraint",
    "ConstraintViolation",
    "ConstraintCheckResult",
    "IMMUTABLE_CONSTRAINTS",
    "QUALITY_GATE_CONSTRAINTS",
    "get_anti_cancer_constraints",
    "get_baseline_constraints",
    "ConstraintChecker",
]
