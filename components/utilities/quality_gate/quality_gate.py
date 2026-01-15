"""
Async Quality Gate with Threshold Validation

A generic, reusable quality gate component for pipeline orchestration.
Supports threshold validation, sync gates, dependency gates, and compile gates.

LEGO Component: Imports shared types from library.common.types

Usage:
    from library.components.utilities.quality_gate import (
        QualityGate, GateConfig, GateType, GateManager
    )
    from library.common.types import QualityResult, Severity

    # Create a quality gate
    gate = QualityGate(
        gate_id="slop_check",
        threshold=0.7,
        metric_fn=calculate_slop_score
    )

    # Check the gate
    result = await gate.check()
    if result.passed:
        print("Quality gate passed!")
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

# LEGO Import: Shared types from library.common.types
from library.common.types import QualityResult, Severity, Violation

logger = logging.getLogger(__name__)


class GateType(Enum):
    """Types of gates for pipeline orchestration."""
    SYNC = "SYNC_GATE"           # Wait for all parallel operations
    QUALITY = "QUALITY_GATE"     # Output must pass threshold
    DEPENDENCY = "DEPENDENCY_GATE"  # Wait for upstream completion
    COMPILE = "COMPILE_GATE"     # Final validation before publish


class GateStatus(Enum):
    """Status of a gate check."""
    PENDING = "pending"
    WAITING = "waiting"
    PASSED = "passed"
    FAILED = "failed"
    BYPASSED = "bypassed"


@dataclass
class GateResult:
    """
    Result of a gate check operation.

    Attributes:
        gate_id: Unique identifier for this gate
        gate_type: Type of gate that was checked
        status: Current status of the gate
        passed: Whether the gate check passed
        message: Human-readable result message
        details: Additional details about the check
        timestamp: When the check was performed
        wait_time_seconds: How long the check took
    """
    gate_id: str
    gate_type: GateType
    status: GateStatus
    passed: bool
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    wait_time_seconds: float = 0.0

    def to_quality_result(self) -> QualityResult:
        """Convert to QualityResult for compatibility with other components."""
        violations = []
        if not self.passed:
            violations.append(
                Violation(
                    severity=Severity.HIGH,
                    message=self.message,
                    rule_id=f"gate_{self.gate_id}",
                    rule_name=f"Gate: {self.gate_id}",
                    metadata=self.details
                )
            )
        score = 1.0 if self.passed else 0.0
        if "score" in self.details:
            score = float(self.details["score"])
        return QualityResult(
            passed=self.passed,
            score=score,
            violations=violations,
            metadata={
                "gate_id": self.gate_id,
                "gate_type": self.gate_type.value,
                "status": self.status.value,
                "wait_time_seconds": self.wait_time_seconds
            }
        )


class RichMetricResult:
    """
    A metric result that behaves like a float but carries additional feedback.
    Allows quality gates to pass rich feedback to refinement loops.

    Usage:
        result = RichMetricResult(0.85, "Style score acceptable, minor issues found")
        if result >= 0.7:
            print("Passed!")
        print(result.feedback)  # Access explanation
    """

    def __init__(self, score: float, feedback: str):
        """
        Initialize rich metric result.

        Args:
            score: Numeric score (0.0 to 1.0)
            feedback: Human-readable explanation of the score
        """
        self.score = score
        self.feedback = feedback

    def __float__(self) -> float:
        return float(self.score)

    def __ge__(self, other: Any) -> bool:
        return self.score >= float(other)

    def __gt__(self, other: Any) -> bool:
        return self.score > float(other)

    def __le__(self, other: Any) -> bool:
        return self.score <= float(other)

    def __lt__(self, other: Any) -> bool:
        return self.score < float(other)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RichMetricResult):
            return self.score == other.score
        return self.score == float(other)

    def __str__(self) -> str:
        return f"{self.score:.2f}"

    def __repr__(self) -> str:
        feedback_preview = self.feedback[:30] + "..." if len(self.feedback) > 30 else self.feedback
        return f"RichMetricResult(score={self.score}, feedback='{feedback_preview}')"


@dataclass
class GateConfig:
    """
    Configuration for a gate.

    Attributes:
        id: Unique identifier for this gate
        gate_type: Type of gate (SYNC, QUALITY, DEPENDENCY, COMPILE)
        description: Human-readable description
        wait_for: Task IDs to wait for (SYNC_GATE)
        threshold: Quality threshold (QUALITY_GATE)
        metric_fn: Async function returning score (QUALITY_GATE)
        requires: Required upstream gates (DEPENDENCY_GATE)
        checks: Validation functions (COMPILE_GATE)
        timeout_seconds: Maximum wait time
        on_fail: Action on failure ("block", "warn", "ralph_wiggum_loop")
    """
    id: str
    gate_type: GateType
    description: str = ""

    # For SYNC_GATE
    wait_for: List[str] = field(default_factory=list)

    # For QUALITY_GATE
    threshold: float = 0.7
    metric_fn: Optional[Callable[[], Union[float, RichMetricResult]]] = None

    # For DEPENDENCY_GATE
    requires: List[str] = field(default_factory=list)

    # For COMPILE_GATE
    checks: List[Callable[[], bool]] = field(default_factory=list)

    # Common
    timeout_seconds: float = 300.0
    on_fail: str = "block"  # "block", "warn", "ralph_wiggum_loop"


class GateFailedError(Exception):
    """Raised when a blocking gate fails."""

    def __init__(self, gate_id: str, result: GateResult):
        self.gate_id = gate_id
        self.result = result
        super().__init__(f"Gate {gate_id} failed: {result.message}")


class GateManager:
    """
    Manages pipeline gates and their execution.

    Provides centralized gate registration, task tracking, and gate checking.

    Usage:
        manager = GateManager()

        # Register gates
        manager.register_gate(create_quality_gate("style", style_metric, 0.7))
        manager.register_gate(create_sync_gate("parallel_complete", ["task_a", "task_b"]))

        # Mark tasks complete
        manager.mark_task_complete("task_a", {"result": "done"})

        # Check gates
        result = await manager.check_gate("style")
        if result.passed:
            print("Proceed to next phase")
    """

    def __init__(self):
        """Initialize gate manager."""
        self.gates: Dict[str, GateConfig] = {}
        self.results: Dict[str, GateResult] = {}
        self.completed_tasks: Dict[str, Any] = {}

    def register_gate(self, config: GateConfig) -> None:
        """
        Register a gate configuration.

        Args:
            config: Gate configuration to register
        """
        self.gates[config.id] = config
        logger.info(f"Registered gate: {config.id} ({config.gate_type.value})")

    def mark_task_complete(self, task_id: str, result: Any = None) -> None:
        """
        Mark a task as complete for SYNC/DEPENDENCY gates.

        Args:
            task_id: Identifier of the completed task
            result: Optional result data from the task
        """
        self.completed_tasks[task_id] = {
            "result": result,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Task marked complete: {task_id}")

    async def check_gate(self, gate_id: str) -> GateResult:
        """
        Check if a gate passes.

        Args:
            gate_id: ID of the gate to check

        Returns:
            GateResult with pass/fail status and details
        """
        if gate_id not in self.gates:
            return GateResult(
                gate_id=gate_id,
                gate_type=GateType.SYNC,
                status=GateStatus.FAILED,
                passed=False,
                message=f"Unknown gate: {gate_id}"
            )

        config = self.gates[gate_id]
        start_time = datetime.now(timezone.utc)

        logger.info(f"Checking gate: {gate_id} ({config.gate_type.value})")

        if config.gate_type == GateType.SYNC:
            result = await self._check_sync_gate(config)
        elif config.gate_type == GateType.QUALITY:
            result = await self._check_quality_gate(config)
        elif config.gate_type == GateType.DEPENDENCY:
            result = await self._check_dependency_gate(config)
        elif config.gate_type == GateType.COMPILE:
            result = await self._check_compile_gate(config)
        else:
            result = GateResult(
                gate_id=gate_id,
                gate_type=config.gate_type,
                status=GateStatus.FAILED,
                passed=False,
                message=f"Unknown gate type: {config.gate_type}"
            )

        result.wait_time_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        self.results[gate_id] = result

        status_str = "PASSED" if result.passed else "FAILED"
        logger.info(f"Gate {gate_id}: {status_str} ({result.wait_time_seconds:.1f}s)")

        return result

    async def _check_sync_gate(self, config: GateConfig) -> GateResult:
        """Check SYNC_GATE: Wait for all specified tasks to complete."""
        pending = [t for t in config.wait_for if t not in self.completed_tasks]

        if not pending:
            return GateResult(
                gate_id=config.id,
                gate_type=GateType.SYNC,
                status=GateStatus.PASSED,
                passed=True,
                message=f"All {len(config.wait_for)} tasks complete",
                details={"completed": list(config.wait_for)}
            )

        # Wait with timeout
        start = datetime.now(timezone.utc)
        while pending and (datetime.now(timezone.utc) - start).total_seconds() < config.timeout_seconds:
            await asyncio.sleep(0.5)
            pending = [t for t in config.wait_for if t not in self.completed_tasks]

        if pending:
            return GateResult(
                gate_id=config.id,
                gate_type=GateType.SYNC,
                status=GateStatus.FAILED,
                passed=False,
                message=f"Timeout waiting for: {pending}",
                details={
                    "pending": pending,
                    "completed": [t for t in config.wait_for if t in self.completed_tasks]
                }
            )

        return GateResult(
            gate_id=config.id,
            gate_type=GateType.SYNC,
            status=GateStatus.PASSED,
            passed=True,
            message=f"All {len(config.wait_for)} tasks complete"
        )

    async def _check_quality_gate(self, config: GateConfig) -> GateResult:
        """Check QUALITY_GATE: Metric must pass threshold."""
        if not config.metric_fn:
            return GateResult(
                gate_id=config.id,
                gate_type=GateType.QUALITY,
                status=GateStatus.FAILED,
                passed=False,
                message="No metric function configured"
            )

        try:
            if asyncio.iscoroutinefunction(config.metric_fn):
                score = await config.metric_fn()
            else:
                score = config.metric_fn()

            passed = score >= config.threshold

            # Extract feedback if RichMetricResult
            feedback = ""
            score_value = float(score)
            if isinstance(score, RichMetricResult):
                feedback = score.feedback

            return GateResult(
                gate_id=config.id,
                gate_type=GateType.QUALITY,
                status=GateStatus.PASSED if passed else GateStatus.FAILED,
                passed=passed,
                message=f"Score: {score_value:.2f} (threshold: {config.threshold})",
                details={
                    "score": score_value,
                    "threshold": config.threshold,
                    "feedback": feedback
                }
            )

        except Exception as e:
            logger.error(f"Metric evaluation failed for gate {config.id}: {e}")
            return GateResult(
                gate_id=config.id,
                gate_type=GateType.QUALITY,
                status=GateStatus.FAILED,
                passed=False,
                message=f"Metric evaluation failed: {e}"
            )

    async def _check_dependency_gate(self, config: GateConfig) -> GateResult:
        """Check DEPENDENCY_GATE: All required tasks must be complete."""
        missing = [r for r in config.requires if r not in self.completed_tasks]

        if missing:
            return GateResult(
                gate_id=config.id,
                gate_type=GateType.DEPENDENCY,
                status=GateStatus.FAILED,
                passed=False,
                message=f"Missing dependencies: {missing}",
                details={
                    "missing": missing,
                    "available": list(self.completed_tasks.keys())
                }
            )

        return GateResult(
            gate_id=config.id,
            gate_type=GateType.DEPENDENCY,
            status=GateStatus.PASSED,
            passed=True,
            message=f"All {len(config.requires)} dependencies satisfied",
            details={"dependencies": config.requires}
        )

    async def _check_compile_gate(self, config: GateConfig) -> GateResult:
        """Check COMPILE_GATE: Run all validation checks."""
        if not config.checks:
            return GateResult(
                gate_id=config.id,
                gate_type=GateType.COMPILE,
                status=GateStatus.PASSED,
                passed=True,
                message="No checks configured"
            )

        failed_checks = []
        passed_checks = []

        for check in config.checks:
            try:
                if asyncio.iscoroutinefunction(check):
                    result = await check()
                else:
                    result = check()
                if not result:
                    failed_checks.append(check.__name__)
                    continue
                passed_checks.append(check.__name__)
            except Exception as e:
                failed_checks.append(f"{check.__name__}: {e}")

        passed = len(failed_checks) == 0

        return GateResult(
            gate_id=config.id,
            gate_type=GateType.COMPILE,
            status=GateStatus.PASSED if passed else GateStatus.FAILED,
            passed=passed,
            message=f"Passed: {len(passed_checks)}, Failed: {len(failed_checks)}",
            details={"passed": passed_checks, "failed": failed_checks}
        )

    async def wait_for_gate(self, gate_id: str) -> GateResult:
        """
        Wait for a gate to pass, with timeout and retry.

        Args:
            gate_id: ID of the gate to wait for

        Returns:
            GateResult with pass/fail status

        Raises:
            ValueError: If gate is unknown
            GateFailedError: If gate fails and on_fail is "block"
        """
        config = self.gates.get(gate_id)
        if not config:
            raise ValueError(f"Unknown gate: {gate_id}")

        result = await self.check_gate(gate_id)

        if not result.passed and config.on_fail == "block":
            raise GateFailedError(gate_id, result)

        return result

    def get_all_results(self) -> Dict[str, GateResult]:
        """Get all gate check results."""
        return self.results.copy()

    def reset(self) -> None:
        """Reset manager state, clearing all results and completed tasks."""
        self.results.clear()
        self.completed_tasks.clear()
        logger.info("Gate manager reset")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_sync_gate(
    gate_id: str,
    wait_for: List[str],
    timeout: float = 300.0
) -> GateConfig:
    """
    Create a synchronization gate.

    Args:
        gate_id: Unique identifier for the gate
        wait_for: List of task IDs to wait for
        timeout: Maximum wait time in seconds

    Returns:
        GateConfig configured for sync gate
    """
    return GateConfig(
        id=gate_id,
        gate_type=GateType.SYNC,
        description=f"Wait for: {', '.join(wait_for)}",
        wait_for=wait_for,
        timeout_seconds=timeout
    )


def create_quality_gate(
    gate_id: str,
    metric_fn: Callable[[], Union[float, RichMetricResult]],
    threshold: float = 0.7
) -> GateConfig:
    """
    Create a quality gate.

    Args:
        gate_id: Unique identifier for the gate
        metric_fn: Function returning score (sync or async)
        threshold: Minimum score to pass (0.0 to 1.0)

    Returns:
        GateConfig configured for quality gate
    """
    return GateConfig(
        id=gate_id,
        gate_type=GateType.QUALITY,
        description=f"Quality threshold: {threshold}",
        threshold=threshold,
        metric_fn=metric_fn
    )


def create_dependency_gate(
    gate_id: str,
    requires: List[str]
) -> GateConfig:
    """
    Create a dependency gate.

    Args:
        gate_id: Unique identifier for the gate
        requires: List of required task IDs

    Returns:
        GateConfig configured for dependency gate
    """
    return GateConfig(
        id=gate_id,
        gate_type=GateType.DEPENDENCY,
        description=f"Requires: {', '.join(requires)}",
        requires=requires
    )


def create_compile_gate(
    gate_id: str,
    checks: List[Callable[[], bool]]
) -> GateConfig:
    """
    Create a compile gate.

    Args:
        gate_id: Unique identifier for the gate
        checks: List of validation functions

    Returns:
        GateConfig configured for compile gate
    """
    return GateConfig(
        id=gate_id,
        gate_type=GateType.COMPILE,
        description=f"Validation checks: {len(checks)}",
        checks=checks
    )
