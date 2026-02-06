"""
Unit tests for Two-Stage Optimizer

Tests:
- ObjectiveVector creation and methods
- Objective computation functions
- Constraint checking
- Optimizer basic functionality
"""

import pytest
import sys
from pathlib import Path

# Add component to path and fix relative imports
component_path = Path(__file__).parent.parent
sys.path.insert(0, str(component_path))

# Import modules directly (not as package)
import importlib.util

def load_module(name, filepath):
    """Load a module from filepath."""
    spec = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Load objectives first (no dependencies)
objectives_mod = load_module("objectives", component_path / "objectives.py")

# Load constraints (depends on objectives)
constraints_mod = load_module("constraints", component_path / "constraints.py")

# Load optimizer (depends on both)
optimizer_mod = load_module("optimizer", component_path / "optimizer.py")

# Now we can import from the loaded modules
# From objectives
ObjectiveVector = objectives_mod.ObjectiveVector
OptimizationDirection = objectives_mod.OptimizationDirection
OBJECTIVE_DEFINITIONS = objectives_mod.OBJECTIVE_DEFINITIONS
compute_Q_task = objectives_mod.compute_Q_task
compute_Q_quality = objectives_mod.compute_Q_quality
compute_G_coverage = objectives_mod.compute_G_coverage
compute_R_diversity = objectives_mod.compute_R_diversity
compute_C_cost = objectives_mod.compute_C_cost
compute_T_latency = objectives_mod.compute_T_latency
compute_E_calib = objectives_mod.compute_E_calib
compute_D_regress = objectives_mod.compute_D_regress
create_objective_vector = objectives_mod.create_objective_vector

# From constraints
IMMUTABLE_CONSTRAINTS = constraints_mod.IMMUTABLE_CONSTRAINTS
QUALITY_GATE_CONSTRAINTS = constraints_mod.QUALITY_GATE_CONSTRAINTS
ConstraintChecker = constraints_mod.ConstraintChecker

# From optimizer
DecisionVariables5D = optimizer_mod.DecisionVariables5D
DecisionVariables14D = optimizer_mod.DecisionVariables14D
VerixStrictness = optimizer_mod.VerixStrictness
NAMED_MODES = optimizer_mod.NAMED_MODES
TwoStageOptimizer = optimizer_mod.TwoStageOptimizer


class TestObjectiveVector:
    """Test ObjectiveVector dataclass."""

    def test_default_values(self):
        """Test default objective values."""
        vec = ObjectiveVector()
        assert vec.Q_task == 0.0
        assert vec.Q_quality == 0.0
        assert vec.C_cost == 0.0
        assert vec.T_latency == 0.0

    def test_to_list(self):
        """Test conversion to list."""
        vec = ObjectiveVector(Q_task=0.9, Q_quality=0.8, C_cost=1000.0)
        lst = vec.to_list()
        assert len(lst) == 8
        assert lst[0] == 0.9
        assert lst[1] == 0.8
        assert lst[4] == 1000.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        vec = ObjectiveVector(Q_task=0.9, E_calib=0.05)
        d = vec.to_dict()
        assert d["Q_task"] == 0.9
        assert d["E_calib"] == 0.05
        assert "G_coverage" in d

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {"Q_task": 0.85, "Q_quality": 0.80, "C_cost": 500.0}
        vec = ObjectiveVector.from_dict(d)
        assert vec.Q_task == 0.85
        assert vec.Q_quality == 0.80
        assert vec.C_cost == 500.0

    def test_dominates_better_on_all(self):
        """Test Pareto dominance when better on all objectives."""
        vec1 = ObjectiveVector(
            Q_task=0.9, Q_quality=0.9, G_coverage=0.9, R_diversity=0.9,
            C_cost=100, T_latency=100, E_calib=0.01, D_regress=0.01
        )
        vec2 = ObjectiveVector(
            Q_task=0.8, Q_quality=0.8, G_coverage=0.8, R_diversity=0.8,
            C_cost=200, T_latency=200, E_calib=0.02, D_regress=0.02
        )
        assert vec1.dominates(vec2)
        assert not vec2.dominates(vec1)

    def test_no_dominance_tradeoff(self):
        """Test no dominance when there's a tradeoff."""
        vec1 = ObjectiveVector(Q_task=0.9, Q_quality=0.7, C_cost=100, T_latency=100)
        vec2 = ObjectiveVector(Q_task=0.7, Q_quality=0.9, C_cost=100, T_latency=100)
        assert not vec1.dominates(vec2)
        assert not vec2.dominates(vec1)


class TestObjectiveDefinitions:
    """Test objective definitions."""

    def test_all_objectives_defined(self):
        """Test all 8 objectives are defined."""
        expected = ["Q_task", "Q_quality", "G_coverage", "R_diversity",
                   "C_cost", "T_latency", "E_calib", "D_regress"]
        for name in expected:
            assert name in OBJECTIVE_DEFINITIONS

    def test_directions_correct(self):
        """Test optimization directions are correct."""
        # MAXIMIZE
        for name in ["Q_task", "Q_quality", "G_coverage", "R_diversity"]:
            assert OBJECTIVE_DEFINITIONS[name].direction == OptimizationDirection.MAXIMIZE
        # MINIMIZE
        for name in ["C_cost", "T_latency", "E_calib", "D_regress"]:
            assert OBJECTIVE_DEFINITIONS[name].direction == OptimizationDirection.MINIMIZE


class TestObjectiveComputation:
    """Test objective computation functions."""

    def test_compute_Q_task(self):
        """Test task score computation."""
        results = [
            {"score": 0.9, "weight": 1.0},
            {"score": 0.8, "weight": 1.0},
        ]
        score = compute_Q_task(results)
        assert score == pytest.approx(0.85, abs=0.01)

    def test_compute_Q_task_weighted(self):
        """Test weighted task score."""
        results = [
            {"score": 1.0, "weight": 2.0},
            {"score": 0.5, "weight": 1.0},
        ]
        score = compute_Q_task(results)
        expected = (1.0 * 2.0 + 0.5 * 1.0) / 3.0
        assert score == pytest.approx(expected, abs=0.01)

    def test_compute_Q_task_empty(self):
        """Test empty task results."""
        assert compute_Q_task([]) == 0.0

    def test_compute_Q_quality(self):
        """Test quality composite computation."""
        metrics = {
            "sigma_level": 4.5,
            "dpmo": 3000,
            "theater_risk": 0.10,
            "nasa_compliance": 0.97,
            "mece_score": 0.85,
        }
        score = compute_Q_quality(metrics)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be decent with these metrics

    def test_compute_G_coverage(self):
        """Test coverage computation."""
        data = {
            "total_cases": 100,
            "covered_cases": 80,
            "edge_cases_total": 20,
            "edge_cases_covered": 15,
        }
        coverage = compute_G_coverage(data)
        # 0.4 * 0.8 + 0.6 * 0.75 = 0.32 + 0.45 = 0.77
        assert coverage == pytest.approx(0.77, abs=0.01)

    def test_compute_R_diversity_identical(self):
        """Test diversity with identical outputs."""
        outputs = ["same", "same", "same"]
        diversity = compute_R_diversity(outputs)
        assert diversity < 0.5  # Low diversity

    def test_compute_R_diversity_unique(self):
        """Test diversity with unique outputs."""
        outputs = ["output one here", "completely different text", "yet another response"]
        diversity = compute_R_diversity(outputs)
        assert diversity > 0.3  # Should have some diversity

    def test_compute_C_cost(self):
        """Test cost computation."""
        cost = compute_C_cost(10000, price_per_1k=0.003)
        assert cost == pytest.approx(0.03, abs=0.001)

    def test_compute_T_latency(self):
        """Test latency computation."""
        samples = [100.0, 150.0, 200.0]
        latency = compute_T_latency(samples)
        assert latency == pytest.approx(150.0, abs=0.01)

    def test_compute_E_calib_perfect(self):
        """Test calibration error with perfect calibration."""
        # 90% confidence, 90% accurate
        predictions = [(0.9, True)] * 9 + [(0.9, False)] * 1
        ece = compute_E_calib(predictions)
        assert ece < 0.1  # Should be low

    def test_compute_D_regress_no_regression(self):
        """Test regression rate with improvement."""
        baseline = {"coding": 0.80, "math": 0.70}
        current = {"coding": 0.85, "math": 0.75}
        regress = compute_D_regress(baseline, current)
        assert regress == 0.0

    def test_compute_D_regress_with_regression(self):
        """Test regression rate with actual regression."""
        baseline = {"coding": 0.80, "math": 0.70}
        current = {"coding": 0.70, "math": 0.75}  # coding regressed
        regress = compute_D_regress(baseline, current)
        assert regress == pytest.approx(0.5, abs=0.01)  # 1/2 tasks regressed


class TestConstraints:
    """Test constraint system."""

    def test_immutable_constraints_exist(self):
        """Test immutable constraints are defined."""
        assert len(IMMUTABLE_CONSTRAINTS) >= 2
        names = [c.name for c in IMMUTABLE_CONSTRAINTS]
        assert "evidential_frame_min" in names
        assert "aspectual_frame_min" in names

    def test_quality_gate_constraints_exist(self):
        """Test quality gate constraints are defined."""
        assert len(QUALITY_GATE_CONSTRAINTS) >= 5
        names = [c.name for c in QUALITY_GATE_CONSTRAINTS]
        assert "sigma_level" in names
        assert "dpmo" in names

    def test_constraint_checker_feasible(self):
        """Test constraint checker with feasible candidate."""
        baseline = ObjectiveVector(Q_task=0.80, Q_quality=0.75)
        checker = ConstraintChecker(baseline=baseline)

        objectives = ObjectiveVector(
            Q_task=0.85, Q_quality=0.80, G_coverage=0.85,
            E_calib=0.10, D_regress=0.02
        )
        decision_vars = {
            "evidential_frame_weight": 0.90,
            "aspectual_frame_weight": 0.70,
        }
        quality_metrics = {
            "sigma_level": 4.5,
            "dpmo": 3000,
            "theater_risk": 0.10,
            "security_critical_count": 0,
            "nasa_compliance": 0.97,
        }

        result = checker.check(objectives, decision_vars, quality_metrics)
        assert result.all_satisfied

    def test_constraint_checker_violation(self):
        """Test constraint checker detects violations."""
        checker = ConstraintChecker()

        objectives = ObjectiveVector(D_regress=0.10)  # Above R_max
        decision_vars = {
            "evidential_frame_weight": 0.20,  # Below 0.30 minimum
        }
        quality_metrics = {
            "sigma_level": 3.0,  # Below 4.0
        }

        result = checker.check(objectives, decision_vars, quality_metrics)
        assert not result.all_satisfied
        assert len(result.hard_violations) > 0


class TestDecisionVariables:
    """Test decision variable classes."""

    def test_5d_defaults(self):
        """Test 5D variable defaults."""
        vars = DecisionVariables5D()
        assert vars.evidential_frame == 0.95
        assert vars.aspectual_frame == 0.80
        assert vars.verix_strictness == VerixStrictness.MODERATE

    def test_5d_to_vector(self):
        """Test 5D to vector conversion."""
        vars = DecisionVariables5D(
            evidential_frame=0.90,
            aspectual_frame=0.70,
            verix_strictness=VerixStrictness.STRICT,
            require_ground=True,
        )
        vec = vars.to_vector()
        assert len(vec) == 5
        assert vec[0] == 0.90
        assert vec[1] == 0.70

    def test_14d_extends_5d(self):
        """Test 14D extends 5D."""
        vars = DecisionVariables14D()
        assert hasattr(vars, "evidential_frame")  # From 5D
        assert hasattr(vars, "morphological_frame")  # 14D only
        assert hasattr(vars, "temperature")

    def test_14d_to_vector(self):
        """Test 14D to vector conversion."""
        vars = DecisionVariables14D()
        vec = vars.to_vector()
        assert len(vec) == 14


class TestNamedModes:
    """Test named modes."""

    def test_all_modes_defined(self):
        """Test all 5 named modes are defined."""
        expected = ["audit", "speed", "research", "robust", "balanced"]
        for name in expected:
            assert name in NAMED_MODES

    def test_mode_accuracy_ordering(self):
        """Test mode accuracy ordering matches spec."""
        assert NAMED_MODES["research"].expected_accuracy >= NAMED_MODES["audit"].expected_accuracy
        assert NAMED_MODES["audit"].expected_accuracy >= NAMED_MODES["balanced"].expected_accuracy
        assert NAMED_MODES["speed"].expected_accuracy < NAMED_MODES["balanced"].expected_accuracy

    def test_mode_efficiency_ordering(self):
        """Test mode efficiency ordering."""
        assert NAMED_MODES["speed"].expected_efficiency >= NAMED_MODES["balanced"].expected_efficiency
        assert NAMED_MODES["balanced"].expected_efficiency >= NAMED_MODES["audit"].expected_efficiency


class TestTwoStageOptimizer:
    """Test TwoStageOptimizer class."""

    def test_initialization(self):
        """Test optimizer initialization."""
        optimizer = TwoStageOptimizer(
            population_size=10,
            max_generations=5,
        )
        assert optimizer.population_size == 10
        assert optimizer.max_generations == 5

    def test_optimizer_runs(self):
        """Test optimizer completes a run."""
        optimizer = TwoStageOptimizer(
            population_size=10,
            max_generations=3,
        )
        result = optimizer.optimize()

        assert result.success
        assert len(result.pareto_front) > 0
        assert result.generations > 0
        assert result.total_evaluations > 0

    def test_optimizer_produces_named_modes(self):
        """Test optimizer produces named modes."""
        optimizer = TwoStageOptimizer(
            population_size=10,
            max_generations=3,
        )
        result = optimizer.optimize()

        assert len(result.named_modes) == 5
        assert "audit" in result.named_modes
        assert "balanced" in result.named_modes


class TestCreateObjectiveVector:
    """Test create_objective_vector function."""

    def test_creates_complete_vector(self):
        """Test full vector creation."""
        vec = create_objective_vector(
            task_results=[{"score": 0.9, "weight": 1.0}],
            quality_metrics={"sigma_level": 4.5, "dpmo": 3000},
            coverage_data={"total_cases": 100, "covered_cases": 85,
                          "edge_cases_total": 20, "edge_cases_covered": 15},
            outputs=["out1", "out2", "out3"],
            token_count=5000,
            latency_samples=[100.0, 150.0, 200.0],
            calibration_data=[(0.9, True), (0.8, True)],
            baseline_scores={"task1": 0.80},
            current_scores={"task1": 0.85},
        )

        assert 0.0 <= vec.Q_task <= 1.0
        assert 0.0 <= vec.Q_quality <= 1.0
        assert 0.0 <= vec.G_coverage <= 1.0
        assert vec.C_cost > 0
        assert vec.T_latency == pytest.approx(150.0, abs=0.01)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
