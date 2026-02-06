"""
Two-Stage Multi-Objective Optimizer

Implements Dual MOO from DUAL-MOO-CONTROL-SPEC.md:
- Stage 1: GlobalMOO (5D coarse exploration)
- Stage 2: PyMOO NSGA-II (14D fine refinement)

Named Modes Output:
- audit: High accuracy (0.960), moderate efficiency
- speed: High efficiency (0.950), moderate accuracy
- research: Highest accuracy (0.980)
- robust: High accuracy with stability
- balanced: General purpose
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import time

try:
    from .objectives import ObjectiveVector, OBJECTIVE_DEFINITIONS, OptimizationDirection
    from .constraints import ConstraintChecker, ConstraintCheckResult
except ImportError:
    from objectives import ObjectiveVector, OBJECTIVE_DEFINITIONS, OptimizationDirection
    from constraints import ConstraintChecker, ConstraintCheckResult


class VerixStrictness(Enum):
    """VERIX notation strictness levels."""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


class CompressionLevel(Enum):
    """Output compression levels."""
    L0 = "L0"  # AI<->AI, maximally compressed
    L1 = "L1"  # Internal, full VERIX notation
    L2 = "L2"  # User-facing, pure English


class ContextWindowStrategy(Enum):
    """Context window management strategies."""
    FULL = "full"
    SUMMARY = "summary"
    SLIDING = "sliding"


@dataclass
class DecisionVariables5D:
    """Stage 1: GlobalMOO 5D decision variables."""
    evidential_frame: float = 0.95  # [0.30, 1.0]
    aspectual_frame: float = 0.80   # [0.10, 1.0]
    verix_strictness: VerixStrictness = VerixStrictness.MODERATE
    compression_level: CompressionLevel = CompressionLevel.L2
    require_ground: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "evidential_frame_weight": self.evidential_frame,
            "aspectual_frame_weight": self.aspectual_frame,
            "verix_strictness": self.verix_strictness.value,
            "compression_level": self.compression_level.value,
            "require_ground": self.require_ground,
        }

    def to_vector(self) -> List[float]:
        """Convert to numeric vector for optimization."""
        return [
            self.evidential_frame,
            self.aspectual_frame,
            {"STRICT": 0.0, "MODERATE": 0.5, "LENIENT": 1.0}[self.verix_strictness.value.upper()],
            {"L0": 0.0, "L1": 0.5, "L2": 1.0}[self.compression_level.value],
            1.0 if self.require_ground else 0.0,
        ]


@dataclass
class DecisionVariables14D(DecisionVariables5D):
    """Stage 2: PyMOO NSGA-II 14D decision variables."""
    # Additional frame weights
    morphological_frame: float = 0.65   # [0.0, 1.0]
    compositional_frame: float = 0.60   # [0.0, 1.0]
    honorific_frame: float = 0.35       # [0.0, 1.0]
    classifier_frame: float = 0.45      # [0.0, 1.0]
    spatial_frame: float = 0.40         # [0.0, 1.0]

    # Runtime knobs
    confidence_floor: float = 0.30      # [0.0, 1.0]
    temperature: float = 0.7            # [0.0, 2.0]
    reasoning_depth: int = 5            # [1, 10]
    context_window_strategy: ContextWindowStrategy = ContextWindowStrategy.FULL

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "morphological_frame": self.morphological_frame,
            "compositional_frame": self.compositional_frame,
            "honorific_frame": self.honorific_frame,
            "classifier_frame": self.classifier_frame,
            "spatial_frame": self.spatial_frame,
            "confidence_floor": self.confidence_floor,
            "temperature": self.temperature,
            "reasoning_depth": self.reasoning_depth,
            "context_window_strategy": self.context_window_strategy.value,
        })
        return base

    def to_vector(self) -> List[float]:
        """Convert to numeric vector for optimization."""
        base = super().to_vector()
        return base + [
            self.morphological_frame,
            self.compositional_frame,
            self.honorific_frame,
            self.classifier_frame,
            self.spatial_frame,
            self.confidence_floor,
            self.temperature,
            self.reasoning_depth / 10.0,  # Normalize to [0, 1]
            {"FULL": 0.0, "SUMMARY": 0.5, "SLIDING": 1.0}[self.context_window_strategy.value.upper()],
        ]


@dataclass
class Candidate:
    """A candidate solution in the Pareto front."""
    decision_vars: DecisionVariables14D
    objectives: ObjectiveVector
    feasible: bool = True
    constraint_result: Optional[ConstraintCheckResult] = None
    generation: int = 0
    rank: int = 0  # Pareto rank (0 = non-dominated)
    crowding_distance: float = 0.0


@dataclass
class NamedMode:
    """A named mode distilled from the Pareto front."""
    name: str
    description: str
    decision_vars: DecisionVariables14D
    expected_accuracy: float
    expected_efficiency: float
    use_cases: List[str]


# Pre-defined named modes from spec
NAMED_MODES = {
    "audit": NamedMode(
        name="audit",
        description="High accuracy for code review and compliance",
        decision_vars=DecisionVariables14D(
            evidential_frame=0.95,
            aspectual_frame=0.85,
            verix_strictness=VerixStrictness.STRICT,
            compression_level=CompressionLevel.L1,
            require_ground=True,
            confidence_floor=0.50,
            temperature=0.3,
            reasoning_depth=8,
        ),
        expected_accuracy=0.960,
        expected_efficiency=0.763,
        use_cases=["code review", "compliance", "security audit"],
    ),
    "speed": NamedMode(
        name="speed",
        description="High efficiency for quick tasks",
        decision_vars=DecisionVariables14D(
            evidential_frame=0.50,
            aspectual_frame=0.40,
            verix_strictness=VerixStrictness.LENIENT,
            compression_level=CompressionLevel.L2,
            require_ground=False,
            confidence_floor=0.20,
            temperature=0.9,
            reasoning_depth=2,
        ),
        expected_accuracy=0.734,
        expected_efficiency=0.950,
        use_cases=["prototyping", "quick answers", "simple tasks"],
    ),
    "research": NamedMode(
        name="research",
        description="Highest accuracy for deep analysis",
        decision_vars=DecisionVariables14D(
            evidential_frame=0.98,
            aspectual_frame=0.90,
            verix_strictness=VerixStrictness.STRICT,
            compression_level=CompressionLevel.L1,
            require_ground=True,
            confidence_floor=0.60,
            temperature=0.2,
            reasoning_depth=10,
        ),
        expected_accuracy=0.980,
        expected_efficiency=0.824,
        use_cases=["content analysis", "deep research", "complex reasoning"],
    ),
    "robust": NamedMode(
        name="robust",
        description="High accuracy with stability for production",
        decision_vars=DecisionVariables14D(
            evidential_frame=0.90,
            aspectual_frame=0.80,
            verix_strictness=VerixStrictness.MODERATE,
            compression_level=CompressionLevel.L2,
            require_ground=True,
            confidence_floor=0.40,
            temperature=0.5,
            reasoning_depth=6,
        ),
        expected_accuracy=0.960,
        expected_efficiency=0.769,
        use_cases=["production code", "critical paths", "reliable operations"],
    ),
    "balanced": NamedMode(
        name="balanced",
        description="General purpose balanced mode",
        decision_vars=DecisionVariables14D(
            evidential_frame=0.75,
            aspectual_frame=0.65,
            verix_strictness=VerixStrictness.MODERATE,
            compression_level=CompressionLevel.L2,
            require_ground=True,
            confidence_floor=0.30,
            temperature=0.7,
            reasoning_depth=5,
        ),
        expected_accuracy=0.882,
        expected_efficiency=0.928,
        use_cases=["general purpose", "most tasks", "default"],
    ),
}


@dataclass
class OptimizationResult:
    """Result of the two-stage optimization."""
    success: bool
    pareto_front: List[Candidate]
    named_modes: Dict[str, NamedMode]
    best_candidate: Optional[Candidate]
    generations: int
    total_evaluations: int
    convergence_achieved: bool
    hypervolume: float
    duration_seconds: float
    error: Optional[str] = None


class TwoStageOptimizer:
    """
    Two-stage multi-objective optimizer for Dual MOO.

    Stage 1: GlobalMOO 5D exploration (coarse global search)
    Stage 2: PyMOO NSGA-II 14D refinement (fine local optimization)
    """

    def __init__(
        self,
        baseline: Optional[ObjectiveVector] = None,
        evaluate_fn: Optional[Callable[[DecisionVariables14D], Tuple[ObjectiveVector, Dict[str, Any]]]] = None,
        population_size: int = 50,
        max_generations: int = 100,
        convergence_threshold: float = 0.001,
        convergence_window: int = 2,
    ):
        """
        Initialize optimizer.

        Args:
            baseline: Baseline objective vector for preservation constraints
            evaluate_fn: Function to evaluate a candidate (returns objectives and quality metrics)
            population_size: Population size for NSGA-II
            max_generations: Maximum generations
            convergence_threshold: Hypervolume gain threshold for convergence
            convergence_window: Rounds with gain < threshold to declare convergence
        """
        self.baseline = baseline
        self.evaluate_fn = evaluate_fn
        self.population_size = population_size
        self.max_generations = max_generations
        self.convergence_threshold = convergence_threshold
        self.convergence_window = convergence_window

        # Constraint checker
        self.constraint_checker = ConstraintChecker(baseline=baseline)

        # Metrics
        self.total_evaluations = 0
        self.hypervolume_history: List[float] = []

    def _evaluate_candidate(
        self,
        decision_vars: DecisionVariables14D,
    ) -> Candidate:
        """
        Evaluate a single candidate.

        Args:
            decision_vars: Decision variables to evaluate

        Returns:
            Candidate with objectives and feasibility
        """
        self.total_evaluations += 1

        # Call evaluation function
        if self.evaluate_fn is not None:
            objectives, quality_metrics = self.evaluate_fn(decision_vars)
        else:
            # Mock evaluation for testing
            objectives = self._mock_evaluate(decision_vars)
            quality_metrics = {
                "sigma_level": 4.5,
                "dpmo": 3000,
                "theater_risk": 0.10,
                "security_critical_count": 0,
                "nasa_compliance": 0.97,
            }

        # Check constraints
        constraint_result = self.constraint_checker.check(
            objectives,
            decision_vars.to_dict(),
            quality_metrics,
        )

        return Candidate(
            decision_vars=decision_vars,
            objectives=objectives,
            feasible=constraint_result.all_satisfied,
            constraint_result=constraint_result,
        )

    def _mock_evaluate(self, decision_vars: DecisionVariables14D) -> ObjectiveVector:
        """Mock evaluation for testing (returns plausible objectives)."""
        # Higher evidential frame -> higher accuracy
        accuracy = 0.5 + 0.4 * decision_vars.evidential_frame
        # Lower temperature -> higher accuracy
        accuracy += 0.1 * (1.0 - decision_vars.temperature / 2.0)

        # Lower reasoning depth -> higher efficiency
        efficiency = 1.0 - 0.05 * decision_vars.reasoning_depth

        return ObjectiveVector(
            Q_task=accuracy * 0.9 + 0.1,
            Q_quality=0.85 + 0.1 * decision_vars.evidential_frame,
            G_coverage=0.75 + 0.15 * (1.0 - decision_vars.temperature / 2.0),
            R_diversity=0.60 + 0.30 * decision_vars.temperature,
            C_cost=1000 * (1.5 - efficiency),
            T_latency=500 * (1.5 - efficiency),
            E_calib=0.15 * (1.0 - accuracy) + 0.05,
            D_regress=0.02 * (1.0 - accuracy) + 0.01,
        )

    def _compute_pareto_rank(self, candidates: List[Candidate]) -> None:
        """Compute Pareto rank for all candidates (in-place)."""
        n = len(candidates)
        domination_count = [0] * n
        dominated_by = [[] for _ in range(n)]

        # Count dominations
        for i in range(n):
            for j in range(i + 1, n):
                if candidates[i].objectives.dominates(candidates[j].objectives):
                    domination_count[j] += 1
                    dominated_by[j].append(i)
                elif candidates[j].objectives.dominates(candidates[i].objectives):
                    domination_count[i] += 1
                    dominated_by[i].append(j)

        # Assign ranks
        current_rank = 0
        remaining = set(range(n))

        while remaining:
            # Find non-dominated in remaining
            front = [i for i in remaining if domination_count[i] == 0]
            if not front:
                # All remaining dominated by each other (shouldn't happen)
                for i in remaining:
                    candidates[i].rank = current_rank
                break

            for i in front:
                candidates[i].rank = current_rank
                remaining.remove(i)
                # Update domination counts
                for j in remaining:
                    if i in dominated_by[j]:
                        domination_count[j] -= 1

            current_rank += 1

    def _compute_hypervolume(self, pareto_front: List[Candidate]) -> float:
        """
        Compute hypervolume indicator for the Pareto front.

        Uses a simple 2D projection (Q_task, efficiency) for demonstration.
        In production, use pymoo's hypervolume indicator.
        """
        if not pareto_front:
            return 0.0

        # Reference point (worst possible)
        ref_point = (0.0, 0.0)

        # Extract 2D points (Q_task, efficiency proxy)
        points = []
        for c in pareto_front:
            q_task = c.objectives.Q_task
            efficiency = 1.0 - c.objectives.C_cost / 10000.0  # Normalize cost to efficiency
            points.append((q_task, efficiency))

        # Sort by first dimension
        points.sort(key=lambda p: p[0], reverse=True)

        # Calculate hypervolume (2D case)
        hv = 0.0
        prev_y = 0.0
        for x, y in points:
            if y > prev_y:
                hv += (x - ref_point[0]) * (y - prev_y)
                prev_y = y

        return hv

    def _distill_named_modes(self, pareto_front: List[Candidate]) -> Dict[str, NamedMode]:
        """
        Distill named modes from the Pareto front.

        Maps closest Pareto-optimal candidates to predefined mode profiles.
        """
        if not pareto_front:
            return NAMED_MODES.copy()

        distilled = {}

        for mode_name, mode_template in NAMED_MODES.items():
            # Find closest candidate in Pareto front
            best_candidate = None
            best_distance = float("inf")

            target_accuracy = mode_template.expected_accuracy
            target_efficiency = mode_template.expected_efficiency

            for candidate in pareto_front:
                accuracy = candidate.objectives.Q_task
                efficiency = 1.0 - candidate.objectives.C_cost / 10000.0

                distance = (
                    (accuracy - target_accuracy) ** 2
                    + (efficiency - target_efficiency) ** 2
                )

                if distance < best_distance:
                    best_distance = distance
                    best_candidate = candidate

            if best_candidate is not None:
                distilled[mode_name] = NamedMode(
                    name=mode_name,
                    description=mode_template.description,
                    decision_vars=best_candidate.decision_vars,
                    expected_accuracy=best_candidate.objectives.Q_task,
                    expected_efficiency=1.0 - best_candidate.objectives.C_cost / 10000.0,
                    use_cases=mode_template.use_cases,
                )
            else:
                distilled[mode_name] = mode_template

        return distilled

    def optimize(self) -> OptimizationResult:
        """
        Run the two-stage optimization.

        Returns:
            OptimizationResult with Pareto front and named modes
        """
        start_time = time.time()
        self.total_evaluations = 0
        self.hypervolume_history = []

        try:
            # Stage 1: GlobalMOO 5D exploration (simplified)
            # In production, call GlobalMOO API
            stage1_candidates = self._stage1_exploration()

            # Stage 2: PyMOO NSGA-II 14D refinement
            pareto_front, generations, converged = self._stage2_refinement(stage1_candidates)

            # Distill named modes
            named_modes = self._distill_named_modes(pareto_front)

            # Find best overall candidate (highest Q_task among feasible)
            feasible = [c for c in pareto_front if c.feasible]
            best_candidate = max(feasible, key=lambda c: c.objectives.Q_task) if feasible else None

            duration = time.time() - start_time

            return OptimizationResult(
                success=True,
                pareto_front=pareto_front,
                named_modes=named_modes,
                best_candidate=best_candidate,
                generations=generations,
                total_evaluations=self.total_evaluations,
                convergence_achieved=converged,
                hypervolume=self.hypervolume_history[-1] if self.hypervolume_history else 0.0,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            return OptimizationResult(
                success=False,
                pareto_front=[],
                named_modes=NAMED_MODES.copy(),
                best_candidate=None,
                generations=0,
                total_evaluations=self.total_evaluations,
                convergence_achieved=False,
                hypervolume=0.0,
                duration_seconds=duration,
                error=str(e),
            )

    def _stage1_exploration(self) -> List[Candidate]:
        """
        Stage 1: GlobalMOO 5D coarse exploration.

        Returns ~40-50 Pareto-optimal candidates.
        """
        candidates = []

        # Grid search over 5D space (simplified)
        evidential_values = [0.30, 0.50, 0.70, 0.90, 0.95]
        aspectual_values = [0.10, 0.40, 0.60, 0.80]
        strictness_values = list(VerixStrictness)
        require_ground_values = [True, False]

        for ev in evidential_values:
            for asp in aspectual_values:
                for strict in strictness_values:
                    for ground in require_ground_values:
                        vars_14d = DecisionVariables14D(
                            evidential_frame=ev,
                            aspectual_frame=asp,
                            verix_strictness=strict,
                            require_ground=ground,
                        )
                        candidate = self._evaluate_candidate(vars_14d)
                        candidates.append(candidate)

        # Compute Pareto ranks
        self._compute_pareto_rank(candidates)

        # Return non-dominated candidates
        return [c for c in candidates if c.rank == 0 and c.feasible]

    def _stage2_refinement(
        self,
        initial_population: List[Candidate],
    ) -> Tuple[List[Candidate], int, bool]:
        """
        Stage 2: PyMOO NSGA-II 14D refinement.

        Returns (pareto_front, generations, converged)
        """
        # Initialize population from Stage 1
        population = list(initial_population)

        # Fill to population_size with random variations
        while len(population) < self.population_size:
            if initial_population:
                base = initial_population[len(population) % len(initial_population)]
                mutated = self._mutate(base.decision_vars)
            else:
                mutated = DecisionVariables14D()
            candidate = self._evaluate_candidate(mutated)
            population.append(candidate)

        converged = False
        stable_rounds = 0

        for gen in range(self.max_generations):
            # Compute Pareto ranks
            self._compute_pareto_rank(population)

            # Get current Pareto front
            pareto_front = [c for c in population if c.rank == 0]

            # Compute hypervolume
            hv = self._compute_hypervolume(pareto_front)
            self.hypervolume_history.append(hv)

            # Check convergence
            if len(self.hypervolume_history) >= 2:
                gain = hv - self.hypervolume_history[-2]
                if gain < self.convergence_threshold:
                    stable_rounds += 1
                    if stable_rounds >= self.convergence_window:
                        converged = True
                        break
                else:
                    stable_rounds = 0

            # Selection, crossover, mutation
            offspring = self._generate_offspring(population)
            population = self._select_next_generation(population + offspring)

        # Final Pareto front
        self._compute_pareto_rank(population)
        pareto_front = [c for c in population if c.rank == 0 and c.feasible]

        return pareto_front, gen + 1, converged

    def _mutate(self, vars: DecisionVariables14D, strength: float = 0.1) -> DecisionVariables14D:
        """Mutate decision variables."""
        import random

        def mutate_val(val: float, min_v: float, max_v: float) -> float:
            delta = random.gauss(0, strength * (max_v - min_v))
            return max(min_v, min(max_v, val + delta))

        return DecisionVariables14D(
            evidential_frame=mutate_val(vars.evidential_frame, 0.30, 1.0),
            aspectual_frame=mutate_val(vars.aspectual_frame, 0.10, 1.0),
            verix_strictness=random.choice(list(VerixStrictness)),
            compression_level=random.choice(list(CompressionLevel)),
            require_ground=random.choice([True, False]),
            morphological_frame=mutate_val(vars.morphological_frame, 0.0, 1.0),
            compositional_frame=mutate_val(vars.compositional_frame, 0.0, 1.0),
            honorific_frame=mutate_val(vars.honorific_frame, 0.0, 1.0),
            classifier_frame=mutate_val(vars.classifier_frame, 0.0, 1.0),
            spatial_frame=mutate_val(vars.spatial_frame, 0.0, 1.0),
            confidence_floor=mutate_val(vars.confidence_floor, 0.0, 1.0),
            temperature=mutate_val(vars.temperature, 0.0, 2.0),
            reasoning_depth=max(1, min(10, vars.reasoning_depth + random.randint(-1, 1))),
            context_window_strategy=random.choice(list(ContextWindowStrategy)),
        )

    def _generate_offspring(self, population: List[Candidate]) -> List[Candidate]:
        """Generate offspring via crossover and mutation."""
        import random

        offspring = []
        n_offspring = self.population_size // 2

        for _ in range(n_offspring):
            # Tournament selection
            parent1 = min(random.sample(population, 3), key=lambda c: c.rank)
            parent2 = min(random.sample(population, 3), key=lambda c: c.rank)

            # Crossover (uniform)
            child_vars = self._crossover(parent1.decision_vars, parent2.decision_vars)

            # Mutation
            child_vars = self._mutate(child_vars, strength=0.1)

            # Evaluate
            child = self._evaluate_candidate(child_vars)
            offspring.append(child)

        return offspring

    def _crossover(
        self,
        vars1: DecisionVariables14D,
        vars2: DecisionVariables14D,
    ) -> DecisionVariables14D:
        """Uniform crossover between two parents."""
        import random

        def pick(v1, v2):
            return v1 if random.random() < 0.5 else v2

        return DecisionVariables14D(
            evidential_frame=pick(vars1.evidential_frame, vars2.evidential_frame),
            aspectual_frame=pick(vars1.aspectual_frame, vars2.aspectual_frame),
            verix_strictness=pick(vars1.verix_strictness, vars2.verix_strictness),
            compression_level=pick(vars1.compression_level, vars2.compression_level),
            require_ground=pick(vars1.require_ground, vars2.require_ground),
            morphological_frame=pick(vars1.morphological_frame, vars2.morphological_frame),
            compositional_frame=pick(vars1.compositional_frame, vars2.compositional_frame),
            honorific_frame=pick(vars1.honorific_frame, vars2.honorific_frame),
            classifier_frame=pick(vars1.classifier_frame, vars2.classifier_frame),
            spatial_frame=pick(vars1.spatial_frame, vars2.spatial_frame),
            confidence_floor=pick(vars1.confidence_floor, vars2.confidence_floor),
            temperature=pick(vars1.temperature, vars2.temperature),
            reasoning_depth=pick(vars1.reasoning_depth, vars2.reasoning_depth),
            context_window_strategy=pick(vars1.context_window_strategy, vars2.context_window_strategy),
        )

    def _select_next_generation(self, combined: List[Candidate]) -> List[Candidate]:
        """Select next generation using NSGA-II selection."""
        self._compute_pareto_rank(combined)

        # Sort by rank, then by crowding distance (desc)
        combined.sort(key=lambda c: (c.rank, -c.crowding_distance))

        return combined[: self.population_size]


__all__ = [
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
