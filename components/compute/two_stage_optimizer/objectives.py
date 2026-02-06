"""
8-Objective Vector for Dual MOO Optimization

Implements the objective vector from DUAL-MOO-CONTROL-SPEC.md Section 2.

Primary Pareto Objectives:
1. Q_task     - Task success / rubric score (MAXIMIZE)
2. Q_quality  - Quality-gate composite (MAXIMIZE)
3. G_coverage - Edge-case coverage (MAXIMIZE)
4. R_diversity - Output entropy (MAXIMIZE)
5. C_cost     - Tokens/run or $/run (MINIMIZE)
6. T_latency  - Wall-clock latency (MINIMIZE)
7. E_calib    - Calibration error (MINIMIZE)
8. D_regress  - Regression rate (MINIMIZE)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import math


class OptimizationDirection(Enum):
    """Direction for optimization."""
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


@dataclass
class ObjectiveDefinition:
    """Definition of a single objective in the vector."""
    name: str
    direction: OptimizationDirection
    description: str
    compute_fn: Optional[Callable[..., float]] = None
    weight: float = 1.0

    # Thresholds for constraints
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None


@dataclass
class ObjectiveResult:
    """Result of computing a single objective."""
    name: str
    value: float
    direction: OptimizationDirection
    normalized_value: float = 0.0  # Normalized to [0, 1] for Pareto comparison

    def is_better_than(self, other: "ObjectiveResult") -> bool:
        """Check if this result is better than another."""
        if self.direction == OptimizationDirection.MAXIMIZE:
            return self.value > other.value
        return self.value < other.value


@dataclass
class ObjectiveVector:
    """The complete 8-objective vector for Dual MOO."""

    # Primary objectives (MAXIMIZE)
    Q_task: float = 0.0       # Task success / rubric score
    Q_quality: float = 0.0    # Quality-gate composite (sigma >= 4.0)
    G_coverage: float = 0.0   # Edge-case coverage
    R_diversity: float = 0.0  # Output entropy

    # Secondary objectives (MINIMIZE)
    C_cost: float = 0.0       # Tokens/run or $/run
    T_latency: float = 0.0    # Wall-clock latency (ms)
    E_calib: float = 0.0      # Calibration error
    D_regress: float = 0.0    # Regression rate

    # Metadata
    timestamp: str = ""
    source: str = ""

    def to_list(self) -> List[float]:
        """Convert to list for optimization libraries."""
        return [
            self.Q_task,
            self.Q_quality,
            self.G_coverage,
            self.R_diversity,
            self.C_cost,
            self.T_latency,
            self.E_calib,
            self.D_regress,
        ]

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "Q_task": self.Q_task,
            "Q_quality": self.Q_quality,
            "G_coverage": self.G_coverage,
            "R_diversity": self.R_diversity,
            "C_cost": self.C_cost,
            "T_latency": self.T_latency,
            "E_calib": self.E_calib,
            "D_regress": self.D_regress,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "ObjectiveVector":
        """Create from dictionary."""
        return cls(
            Q_task=data.get("Q_task", 0.0),
            Q_quality=data.get("Q_quality", 0.0),
            G_coverage=data.get("G_coverage", 0.0),
            R_diversity=data.get("R_diversity", 0.0),
            C_cost=data.get("C_cost", 0.0),
            T_latency=data.get("T_latency", 0.0),
            E_calib=data.get("E_calib", 0.0),
            D_regress=data.get("D_regress", 0.0),
        )

    def dominates(self, other: "ObjectiveVector") -> bool:
        """
        Check if this vector Pareto-dominates another.

        Domination: at least as good on ALL objectives,
        strictly better on at least ONE.
        """
        # Objectives to maximize (higher is better)
        maximize = ["Q_task", "Q_quality", "G_coverage", "R_diversity"]
        # Objectives to minimize (lower is better)
        minimize = ["C_cost", "T_latency", "E_calib", "D_regress"]

        self_dict = self.to_dict()
        other_dict = other.to_dict()

        at_least_as_good = True
        strictly_better = False

        for obj in maximize:
            if self_dict[obj] < other_dict[obj]:
                at_least_as_good = False
                break
            if self_dict[obj] > other_dict[obj]:
                strictly_better = True

        if not at_least_as_good:
            return False

        for obj in minimize:
            if self_dict[obj] > other_dict[obj]:
                at_least_as_good = False
                break
            if self_dict[obj] < other_dict[obj]:
                strictly_better = True

        return at_least_as_good and strictly_better


# Standard objective definitions
OBJECTIVE_DEFINITIONS = {
    "Q_task": ObjectiveDefinition(
        name="Q_task",
        direction=OptimizationDirection.MAXIMIZE,
        description="Task success / rubric score",
        min_threshold=0.0,
        max_threshold=1.0,
    ),
    "Q_quality": ObjectiveDefinition(
        name="Q_quality",
        direction=OptimizationDirection.MAXIMIZE,
        description="Quality-gate composite (Connascence suite, sigma >= 4.0)",
        min_threshold=0.0,
        max_threshold=1.0,
    ),
    "G_coverage": ObjectiveDefinition(
        name="G_coverage",
        direction=OptimizationDirection.MAXIMIZE,
        description="Edge-case coverage (anti-Goodhart)",
        min_threshold=0.0,
        max_threshold=1.0,
    ),
    "R_diversity": ObjectiveDefinition(
        name="R_diversity",
        direction=OptimizationDirection.MAXIMIZE,
        description="Output entropy (anti-overfit)",
        min_threshold=0.0,
        max_threshold=1.0,
    ),
    "C_cost": ObjectiveDefinition(
        name="C_cost",
        direction=OptimizationDirection.MINIMIZE,
        description="Estimated cost ($/run or tokens/run)",
        min_threshold=0.0,
    ),
    "T_latency": ObjectiveDefinition(
        name="T_latency",
        direction=OptimizationDirection.MINIMIZE,
        description="Wall-clock latency (ms)",
        min_threshold=0.0,
    ),
    "E_calib": ObjectiveDefinition(
        name="E_calib",
        direction=OptimizationDirection.MINIMIZE,
        description="Calibration error (confidence accuracy)",
        min_threshold=0.0,
        max_threshold=1.0,
    ),
    "D_regress": ObjectiveDefinition(
        name="D_regress",
        direction=OptimizationDirection.MINIMIZE,
        description="Regression rate (capability preservation)",
        min_threshold=0.0,
        max_threshold=1.0,
    ),
}


def compute_Q_task(task_results: List[Dict[str, Any]]) -> float:
    """
    Compute task success / rubric score.

    Args:
        task_results: List of task evaluation results with 'passed' and 'score' fields

    Returns:
        Aggregate task success score [0, 1]
    """
    if not task_results:
        return 0.0

    total_score = 0.0
    total_weight = 0.0

    for result in task_results:
        weight = result.get("weight", 1.0)
        score = result.get("score", 0.0)
        total_score += score * weight
        total_weight += weight

    return total_score / total_weight if total_weight > 0 else 0.0


def compute_Q_quality(quality_metrics: Dict[str, Any]) -> float:
    """
    Compute quality-gate composite from Connascence suite.

    Args:
        quality_metrics: Dict with keys like 'sigma_level', 'dpmo', 'theater_risk', etc.

    Returns:
        Quality composite score [0, 1]
    """
    # Extract metrics with defaults
    sigma_level = quality_metrics.get("sigma_level", 0.0)
    dpmo = quality_metrics.get("dpmo", 1000000)
    theater_risk = quality_metrics.get("theater_risk", 1.0)
    nasa_compliance = quality_metrics.get("nasa_compliance", 0.0)
    mece_score = quality_metrics.get("mece_score", 0.0)

    # Normalize each metric to [0, 1]
    # Sigma level: 4.0 is target, 6.0 is excellent
    sigma_normalized = min(sigma_level / 6.0, 1.0)

    # DPMO: 6210 is 4-sigma, 0 is perfect
    dpmo_normalized = max(0.0, 1.0 - (dpmo / 6210.0))

    # Theater risk: lower is better
    theater_normalized = max(0.0, 1.0 - theater_risk)

    # NASA compliance: already [0, 1]
    nasa_normalized = min(nasa_compliance, 1.0)

    # MECE score: already [0, 1]
    mece_normalized = min(mece_score, 1.0)

    # Weighted average
    weights = {
        "sigma": 0.25,
        "dpmo": 0.25,
        "theater": 0.15,
        "nasa": 0.20,
        "mece": 0.15,
    }

    composite = (
        sigma_normalized * weights["sigma"]
        + dpmo_normalized * weights["dpmo"]
        + theater_normalized * weights["theater"]
        + nasa_normalized * weights["nasa"]
        + mece_normalized * weights["mece"]
    )

    return composite


def compute_G_coverage(coverage_data: Dict[str, Any]) -> float:
    """
    Compute edge-case coverage (anti-Goodhart).

    Args:
        coverage_data: Dict with 'total_cases', 'covered_cases', 'edge_cases_covered'

    Returns:
        Coverage breadth score [0, 1]
    """
    total = coverage_data.get("total_cases", 1)
    covered = coverage_data.get("covered_cases", 0)
    edge_covered = coverage_data.get("edge_cases_covered", 0)
    edge_total = coverage_data.get("edge_cases_total", 1)

    # Basic coverage
    basic_coverage = covered / total if total > 0 else 0.0

    # Edge case coverage (weighted more heavily)
    edge_coverage = edge_covered / edge_total if edge_total > 0 else 0.0

    # Combined score with edge cases weighted more
    return 0.4 * basic_coverage + 0.6 * edge_coverage


def compute_R_diversity(outputs: List[str]) -> float:
    """
    Compute output entropy (diversity score).

    Args:
        outputs: List of output strings to measure diversity

    Returns:
        Diversity score [0, 1]
    """
    if not outputs or len(outputs) < 2:
        return 0.0

    # Simple diversity: ratio of unique outputs
    unique_outputs = set(outputs)
    base_diversity = len(unique_outputs) / len(outputs)

    # Entropy-based diversity (optional, more sophisticated)
    # Using simple token-level diversity for now
    all_tokens = []
    for output in outputs:
        all_tokens.extend(output.split())

    if not all_tokens:
        return base_diversity

    # Token frequency distribution
    token_counts = {}
    for token in all_tokens:
        token_counts[token] = token_counts.get(token, 0) + 1

    total_tokens = len(all_tokens)
    entropy = 0.0
    for count in token_counts.values():
        p = count / total_tokens
        if p > 0:
            entropy -= p * math.log2(p)

    # Normalize entropy (max entropy = log2(unique_tokens))
    max_entropy = math.log2(len(token_counts)) if len(token_counts) > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    # Combine both metrics
    return 0.5 * base_diversity + 0.5 * normalized_entropy


def compute_C_cost(token_count: int, price_per_1k: float = 0.003) -> float:
    """
    Compute cost metric.

    Args:
        token_count: Total tokens used
        price_per_1k: Price per 1000 tokens (default: $0.003 for Claude Haiku)

    Returns:
        Cost in dollars
    """
    return (token_count / 1000.0) * price_per_1k


def compute_T_latency(latency_samples: List[float]) -> float:
    """
    Compute average latency.

    Args:
        latency_samples: List of latency measurements in milliseconds

    Returns:
        Average latency in milliseconds
    """
    if not latency_samples:
        return 0.0
    return sum(latency_samples) / len(latency_samples)


def compute_E_calib(
    predictions: List[Tuple[float, bool]]
) -> float:
    """
    Compute calibration error (Expected Calibration Error).

    Args:
        predictions: List of (confidence, was_correct) tuples

    Returns:
        ECE score [0, 1] - lower is better
    """
    if not predictions:
        return 0.0

    # Bin predictions by confidence
    num_bins = 10
    bins = [[] for _ in range(num_bins)]

    for confidence, correct in predictions:
        bin_idx = min(int(confidence * num_bins), num_bins - 1)
        bins[bin_idx].append((confidence, correct))

    # Calculate ECE
    ece = 0.0
    total_samples = len(predictions)

    for bin_predictions in bins:
        if not bin_predictions:
            continue

        avg_confidence = sum(c for c, _ in bin_predictions) / len(bin_predictions)
        accuracy = sum(1 for _, correct in bin_predictions if correct) / len(bin_predictions)

        bin_weight = len(bin_predictions) / total_samples
        ece += bin_weight * abs(avg_confidence - accuracy)

    return ece


def compute_D_regress(
    baseline_scores: Dict[str, float],
    current_scores: Dict[str, float]
) -> float:
    """
    Compute regression rate (capability preservation).

    Args:
        baseline_scores: Previous capability scores by task type
        current_scores: Current capability scores by task type

    Returns:
        Regression rate [0, 1] - lower is better
    """
    if not baseline_scores or not current_scores:
        return 0.0

    regressions = 0
    total_comparisons = 0

    for task_type, baseline in baseline_scores.items():
        if task_type in current_scores:
            current = current_scores[task_type]
            if current < baseline * 0.95:  # 5% tolerance
                regressions += 1
            total_comparisons += 1

    return regressions / total_comparisons if total_comparisons > 0 else 0.0


def create_objective_vector(
    task_results: List[Dict[str, Any]],
    quality_metrics: Dict[str, Any],
    coverage_data: Dict[str, Any],
    outputs: List[str],
    token_count: int,
    latency_samples: List[float],
    calibration_data: List[Tuple[float, bool]],
    baseline_scores: Dict[str, float],
    current_scores: Dict[str, float],
    price_per_1k: float = 0.003,
) -> ObjectiveVector:
    """
    Create a complete 8-objective vector from raw data.

    Returns:
        ObjectiveVector with all 8 objectives computed
    """
    return ObjectiveVector(
        Q_task=compute_Q_task(task_results),
        Q_quality=compute_Q_quality(quality_metrics),
        G_coverage=compute_G_coverage(coverage_data),
        R_diversity=compute_R_diversity(outputs),
        C_cost=compute_C_cost(token_count, price_per_1k),
        T_latency=compute_T_latency(latency_samples),
        E_calib=compute_E_calib(calibration_data),
        D_regress=compute_D_regress(baseline_scores, current_scores),
    )


__all__ = [
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
]
