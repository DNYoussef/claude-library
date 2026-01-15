"""
FrozenHarness Telemetry Integration

Collects and exposes metrics from FrozenHarness and DecisionAuthority
for integration with META-006 Sleep System telemetry.

Metrics:
- grades_issued: count per period
- veto_rate: vetoes / total decisions
- override_rate: human overrides / vetoes
- convergence_iterations: avg iterations to fixpoint
- grade_distribution: histogram of grade values
- decision_latency: avg grading time

VERIX Example:
    [assert|confident] Telemetry captures all harness operations
    [ground:architecture-spec] [conf:0.95] [state:confirmed]

Usage:
    from cognitive_architecture.loopctl.telemetry import (
        HarnessTelemetry,
        TelemetryPacket,
    )

    telemetry = HarnessTelemetry(harness, authority)
    packet = telemetry.collect()
    print(f"Grades issued: {packet.grades_issued}")
    print(f"Veto rate: {packet.veto_rate:.2%}")
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .core import FrozenHarness
    from .authority import DecisionAuthority

logger = logging.getLogger(__name__)


@dataclass
class TelemetryPacket:
    """
    Telemetry data packet for FrozenHarness metrics.

    All rates are in range [0.0, 1.0].
    Counts are for the current collection period.

    Attributes:
        timestamp: When this packet was collected
        period_seconds: Collection period duration
        grades_issued: Number of grades in period
        veto_rate: vetoes / total decisions
        override_rate: human overrides / vetoes
        convergence_iterations: avg iterations to fixpoint (if applicable)
        avg_grade: average overall grade score
        grade_distribution: histogram buckets (0-0.2, 0.2-0.4, etc.)
        decision_count: total decisions in period
        harness_version: version of harness
        harness_hash: integrity hash of harness
        evaluation_mode: current evaluation mode
        metadata: additional context
    """
    timestamp: datetime
    period_seconds: float
    grades_issued: int = 0
    veto_rate: float = 0.0
    override_rate: float = 0.0
    convergence_iterations: float = 0.0
    avg_grade: float = 0.0
    grade_distribution: Dict[str, int] = field(default_factory=dict)
    decision_count: int = 0
    harness_version: str = ""
    harness_hash: str = ""
    evaluation_mode: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "period_seconds": self.period_seconds,
            "grades_issued": self.grades_issued,
            "veto_rate": self.veto_rate,
            "override_rate": self.override_rate,
            "convergence_iterations": self.convergence_iterations,
            "avg_grade": self.avg_grade,
            "grade_distribution": self.grade_distribution,
            "decision_count": self.decision_count,
            "harness_version": self.harness_version,
            "harness_hash": self.harness_hash,
            "evaluation_mode": self.evaluation_mode,
            "metadata": self.metadata,
        }

    def to_prometheus_format(self) -> str:
        """Convert to Prometheus exposition format."""
        lines = []
        prefix = "frozen_harness"

        # Counters
        lines.append(f"{prefix}_grades_issued_total {self.grades_issued}")
        lines.append(f"{prefix}_decisions_total {self.decision_count}")

        # Gauges
        lines.append(f"{prefix}_veto_rate {self.veto_rate}")
        lines.append(f"{prefix}_override_rate {self.override_rate}")
        lines.append(f"{prefix}_avg_grade {self.avg_grade}")
        lines.append(f"{prefix}_convergence_iterations {self.convergence_iterations}")

        # Histogram buckets
        for bucket, count in self.grade_distribution.items():
            safe_bucket = bucket.replace("-", "_")
            lines.append(f'{prefix}_grade_bucket{{le="{safe_bucket}"}} {count}')

        # Info
        lines.append(
            f'{prefix}_info{{version="{self.harness_version}",'
            f'hash="{self.harness_hash}",'
            f'mode="{self.evaluation_mode}"}} 1'
        )

        return "\n".join(lines)


@dataclass
class GradeEvent:
    """A single grading event for tracking."""
    timestamp: datetime
    overall_grade: float
    latency_ms: float
    artifact_path: str


@dataclass
class ConvergenceEvent:
    """A convergence event (for fixpoint/helix loops)."""
    timestamp: datetime
    iterations: int
    final_grade: float
    converged: bool


class HarnessTelemetry:
    """
    Telemetry collector for FrozenHarness metrics.

    Collects metrics from FrozenHarness grading operations and
    DecisionAuthority decisions for reporting to telemetry systems.

    Usage:
        from cognitive_architecture.loopctl import FrozenHarness
        from cognitive_architecture.loopctl.authority import DecisionAuthority
        from cognitive_architecture.loopctl.telemetry import HarnessTelemetry

        harness = FrozenHarness()
        authority = DecisionAuthority()
        telemetry = HarnessTelemetry(harness, authority)

        # After some grading operations...
        packet = telemetry.collect()
        print(f"Grades: {packet.grades_issued}, Veto rate: {packet.veto_rate:.2%}")

        # Export to Prometheus
        print(packet.to_prometheus_format())
    """

    # Grade distribution buckets
    GRADE_BUCKETS = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]

    def __init__(
        self,
        harness: Optional["FrozenHarness"] = None,
        authority: Optional["DecisionAuthority"] = None,
        collection_period_seconds: float = 300.0,  # 5 minutes
        max_events: int = 1000,
    ):
        """
        Initialize telemetry collector.

        Args:
            harness: FrozenHarness instance to monitor
            authority: DecisionAuthority instance to monitor
            collection_period_seconds: Period for rate calculations
            max_events: Maximum events to keep in memory
        """
        self._harness = harness
        self._authority = authority
        self._period = collection_period_seconds
        self._max_events = max_events

        # Event tracking
        self._grade_events: deque = deque(maxlen=max_events)
        self._convergence_events: deque = deque(maxlen=max_events)
        self._last_collection: datetime = datetime.now()

        # Callbacks
        self._export_callbacks: List[Callable[[TelemetryPacket], None]] = []

        logger.info("HarnessTelemetry initialized")

    def record_grade(
        self,
        overall_grade: float,
        latency_ms: float,
        artifact_path: str = ""
    ) -> None:
        """
        Record a grading event.

        Args:
            overall_grade: The overall grade (0.0-1.0)
            latency_ms: Time to compute grade in milliseconds
            artifact_path: Path to graded artifact
        """
        event = GradeEvent(
            timestamp=datetime.now(),
            overall_grade=overall_grade,
            latency_ms=latency_ms,
            artifact_path=artifact_path,
        )
        self._grade_events.append(event)

    def record_convergence(
        self,
        iterations: int,
        final_grade: float,
        converged: bool = True
    ) -> None:
        """
        Record a convergence event (for fixpoint/helix loops).

        Args:
            iterations: Number of iterations to convergence
            final_grade: Final grade at convergence
            converged: Whether it actually converged
        """
        event = ConvergenceEvent(
            timestamp=datetime.now(),
            iterations=iterations,
            final_grade=final_grade,
            converged=converged,
        )
        self._convergence_events.append(event)

    def _get_events_in_period(self, events: deque, period_start: datetime) -> List:
        """Get events within the collection period."""
        return [e for e in events if e.timestamp >= period_start]

    def _compute_grade_distribution(
        self,
        events: List[GradeEvent]
    ) -> Dict[str, int]:
        """Compute histogram of grade values."""
        distribution = {bucket: 0 for bucket in self.GRADE_BUCKETS}

        for event in events:
            grade = event.overall_grade
            if grade < 0.2:
                distribution["0.0-0.2"] += 1
            elif grade < 0.4:
                distribution["0.2-0.4"] += 1
            elif grade < 0.6:
                distribution["0.4-0.6"] += 1
            elif grade < 0.8:
                distribution["0.6-0.8"] += 1
            else:
                distribution["0.8-1.0"] += 1

        return distribution

    def collect(self) -> TelemetryPacket:
        """
        Collect current telemetry metrics.

        Returns:
            TelemetryPacket with current metrics
        """
        now = datetime.now()
        period_start = now - timedelta(seconds=self._period)

        # Get events in period
        period_grades = self._get_events_in_period(self._grade_events, period_start)
        period_convergence = self._get_events_in_period(
            self._convergence_events, period_start
        )

        # Compute metrics
        grades_issued = len(period_grades)
        avg_grade = 0.0
        if period_grades:
            avg_grade = sum(e.overall_grade for e in period_grades) / grades_issued

        # Convergence iterations
        convergence_iterations = 0.0
        if period_convergence:
            convergence_iterations = (
                sum(e.iterations for e in period_convergence) / len(period_convergence)
            )

        # Get authority metrics
        veto_rate = 0.0
        override_rate = 0.0
        decision_count = 0
        if self._authority:
            stats = self._authority.get_statistics()
            veto_rate = stats.get("veto_rate", 0.0)
            override_rate = stats.get("override_rate", 0.0)
            decision_count = stats.get("total_decisions", 0)

        # Get harness info
        harness_version = ""
        harness_hash = ""
        evaluation_mode = ""
        if self._harness:
            harness_version = self._harness.harness_version
            harness_hash = self._harness.current_hash
            evaluation_mode = self._harness.evaluation_mode

        packet = TelemetryPacket(
            timestamp=now,
            period_seconds=self._period,
            grades_issued=grades_issued,
            veto_rate=veto_rate,
            override_rate=override_rate,
            convergence_iterations=convergence_iterations,
            avg_grade=avg_grade,
            grade_distribution=self._compute_grade_distribution(period_grades),
            decision_count=decision_count,
            harness_version=harness_version,
            harness_hash=harness_hash,
            evaluation_mode=evaluation_mode,
            metadata={
                "collection_period_seconds": self._period,
                "total_grades_tracked": len(self._grade_events),
                "total_convergence_tracked": len(self._convergence_events),
            },
        )

        self._last_collection = now

        # Execute export callbacks
        for callback in self._export_callbacks:
            try:
                callback(packet)
            except Exception as e:
                logger.error(f"Telemetry export callback error: {e}")

        return packet

    def register_export_callback(
        self,
        callback: Callable[[TelemetryPacket], None]
    ) -> None:
        """
        Register callback for telemetry export.

        Args:
            callback: Function called with TelemetryPacket on each collection
        """
        self._export_callbacks.append(callback)

    def export_to_file(self, output_path: Path) -> Path:
        """
        Export current telemetry to JSON file.

        Args:
            output_path: Path for output file

        Returns:
            Path to exported file
        """
        packet = self.collect()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(packet.to_dict(), f, indent=2)

        logger.info(f"Telemetry exported to {output_path}")
        return output_path

    def export_prometheus(self, output_path: Path) -> Path:
        """
        Export current telemetry in Prometheus format.

        Args:
            output_path: Path for output file

        Returns:
            Path to exported file
        """
        packet = self.collect()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write(packet.to_prometheus_format())

        logger.info(f"Prometheus metrics exported to {output_path}")
        return output_path

    def get_summary(self) -> Dict[str, Any]:
        """Get a quick summary of telemetry state."""
        packet = self.collect()
        return {
            "grades_issued": packet.grades_issued,
            "avg_grade": f"{packet.avg_grade:.3f}",
            "veto_rate": f"{packet.veto_rate:.2%}",
            "override_rate": f"{packet.override_rate:.2%}",
            "convergence_iterations": f"{packet.convergence_iterations:.1f}",
            "harness_version": packet.harness_version,
            "evaluation_mode": packet.evaluation_mode,
        }

    def clear(self) -> None:
        """Clear all tracked events."""
        self._grade_events.clear()
        self._convergence_events.clear()
        logger.info("Telemetry events cleared")


# Helper function for META-006 Sleep System integration
def create_sleep_system_exporter(
    telemetry: HarnessTelemetry,
    sleep_system_url: str = "http://localhost:8081/metrics"
) -> Callable[[TelemetryPacket], None]:
    """
    Create an exporter callback for META-006 Sleep System.

    Args:
        telemetry: HarnessTelemetry instance
        sleep_system_url: URL for sleep system metrics endpoint

    Returns:
        Callback function for telemetry export

    Usage:
        telemetry = HarnessTelemetry(harness, authority)
        exporter = create_sleep_system_exporter(telemetry)
        telemetry.register_export_callback(exporter)
    """
    try:
        import httpx
    except ImportError:
        logger.warning("httpx not available for sleep system export")
        return lambda packet: None

    def export_to_sleep_system(packet: TelemetryPacket) -> None:
        """Export telemetry packet to sleep system."""
        try:
            with httpx.Client(timeout=5) as client:
                response = client.post(
                    sleep_system_url,
                    json={
                        "source": "frozen_harness",
                        "metrics": packet.to_dict(),
                    }
                )
                if response.status_code != 200:
                    logger.warning(
                        f"Sleep system export failed: {response.status_code}"
                    )
        except Exception as e:
            logger.warning(f"Sleep system export error: {e}")

    return export_to_sleep_system
