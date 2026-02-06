"""
Two-Stage Multi-Objective Optimizer

Implements Dual MOO from DUAL-MOO-CONTROL-SPEC.md:
- 8-objective vector for Pareto optimization
- Constraints (immutable, anti-cancer, quality gates, baseline)
- Stage 1: GlobalMOO 5D exploration
- Stage 2: PyMOO NSGA-II 14D refinement
- Named modes: audit, speed, research, robust, balanced
"""

try:
    from .objectives import (
        OptimizationDirection,
        ObjectiveDefinition,
        ObjectiveResult,
        ObjectiveVector,
        OBJECTIVE_DEFINITIONS,
        compute_Q_task,
        compute_Q_quality,
        compute_G_coverage,
        compute_R_diversity,
        compute_C_cost,
        compute_T_latency,
        compute_E_calib,
        compute_D_regress,
        create_objective_vector,
    )
except ImportError:
    from objectives import (
        OptimizationDirection,
        ObjectiveDefinition,
        ObjectiveResult,
        ObjectiveVector,
        OBJECTIVE_DEFINITIONS,
        compute_Q_task,
        compute_Q_quality,
        compute_G_coverage,
        compute_R_diversity,
        compute_C_cost,
        compute_T_latency,
        compute_E_calib,
        compute_D_regress,
        create_objective_vector,
    )

try:
    from .constraints import (
        ConstraintType,
        ConstraintResult,
        Constraint,
        ConstraintViolation,
        ConstraintCheckResult,
        IMMUTABLE_CONSTRAINTS,
        QUALITY_GATE_CONSTRAINTS,
        get_anti_cancer_constraints,
        get_baseline_constraints,
        ConstraintChecker,
    )
except ImportError:
    from constraints import (
        ConstraintType,
        ConstraintResult,
        Constraint,
        ConstraintViolation,
        ConstraintCheckResult,
        IMMUTABLE_CONSTRAINTS,
        QUALITY_GATE_CONSTRAINTS,
        get_anti_cancer_constraints,
        get_baseline_constraints,
        ConstraintChecker,
    )

try:
    from .optimizer import (
        VerixStrictness,
        CompressionLevel,
        ContextWindowStrategy,
        DecisionVariables5D,
        DecisionVariables14D,
        Candidate,
        NamedMode,
        NAMED_MODES,
        OptimizationResult,
        TwoStageOptimizer,
    )
except ImportError:
    from optimizer import (
        VerixStrictness,
        CompressionLevel,
        ContextWindowStrategy,
        DecisionVariables5D,
        DecisionVariables14D,
        Candidate,
        NamedMode,
        NAMED_MODES,
        OptimizationResult,
        TwoStageOptimizer,
    )


__all__ = [
    # Objectives
    "OptimizationDirection",
    "ObjectiveDefinition",
    "ObjectiveResult",
    "ObjectiveVector",
    "OBJECTIVE_DEFINITIONS",
    "compute_Q_task",
    "compute_Q_quality",
    "compute_G_coverage",
    "compute_R_diversity",
    "compute_C_cost",
    "compute_T_latency",
    "compute_E_calib",
    "compute_D_regress",
    "create_objective_vector",
    # Constraints
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
    # Optimizer
    "VerixStrictness",
    "CompressionLevel",
    "ContextWindowStrategy",
    "DecisionVariables5D",
    "DecisionVariables14D",
    "Candidate",
    "NamedMode",
    "NAMED_MODES",
    "OptimizationResult",
    "TwoStageOptimizer",
]

__version__ = "1.0.0"
