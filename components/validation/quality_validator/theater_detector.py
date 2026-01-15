"""
Theater Detector - Fake Quality Pattern Detection

Detects fraudulent or misleading quality improvement claims through
pattern recognition, statistical analysis, and evidence validation.

Zero external dependencies - stdlib only.
"""

from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import statistics
from typing import Any, Dict, List, Optional, Union


@dataclass
class TheaterPattern:
    """Pattern that indicates quality theater"""
    pattern_name: str
    description: str
    indicators: List[str]
    severity: str  # low, medium, high, critical
    detection_method: str
    applies_to: List[str]  # claim types this pattern applies to

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "pattern_name": self.pattern_name,
            "description": self.description,
            "indicators": self.indicators,
            "severity": self.severity,
            "detection_method": self.detection_method,
            "applies_to": self.applies_to,
        }


@dataclass
class TheaterDetectionResult:
    """Result of theater detection analysis"""
    claim_id: str
    is_theater: bool
    confidence: float
    detected_patterns: List[str]
    pattern_details: List[TheaterPattern]
    risk_assessment: str  # low, medium, high
    recommendation: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "claim_id": self.claim_id,
            "is_theater": self.is_theater,
            "confidence": self.confidence,
            "detected_patterns": self.detected_patterns,
            "pattern_details": [p.to_dict() for p in self.pattern_details],
            "risk_assessment": self.risk_assessment,
            "recommendation": self.recommendation,
            "metadata": self.metadata,
        }


@dataclass
class SystemicTheaterResult:
    """Result of systemic theater analysis across multiple claims"""
    systemic_indicators: List[str]
    risk_assessment: str
    recommendation: str
    claim_count: int
    suspicious_patterns: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "systemic_indicators": self.systemic_indicators,
            "risk_assessment": self.risk_assessment,
            "recommendation": self.recommendation,
            "claim_count": self.claim_count,
            "suspicious_patterns": self.suspicious_patterns,
            "metadata": self.metadata,
        }


class TheaterDetector:
    """
    Advanced theater detection system for quality analysis.

    Validates quality claims through evidence analysis, statistical validation,
    and pattern recognition to detect fake quality improvements.

    Theater Patterns Detected:
    - perfect_metrics: Suspiciously perfect or 100% improvements
    - vanity_metrics: Focus on meaningless or easily gamed metrics
    - cherry_picked_results: Selective reporting of favorable results
    - fake_refactoring: Cosmetic changes presented as improvements
    - measurement_gaming: Manipulating measurement conditions
    - false_automation: Manual fixes claimed as automated
    - complexity_hiding: Moving complexity rather than reducing
    - test_theater: Fake or meaningless test improvements
    """

    DEFAULT_PATTERNS = [
        TheaterPattern(
            pattern_name="perfect_metrics",
            description="Claims perfect or near-perfect quality metrics",
            indicators=[
                "zero violations claimed without evidence",
                "100% improvement with no methodology",
                "perfect maintainability index",
                "all metrics improved by exact same percentage",
            ],
            severity="critical",
            detection_method="statistical_analysis",
            applies_to=["quality", "maintainability"],
        ),
        TheaterPattern(
            pattern_name="vanity_metrics",
            description="Focus on meaningless or easily gamed metrics",
            indicators=[
                "only line count metrics reported",
                "comment ratio as primary metric",
                "file count reduction without context",
                "formatting changes counted as improvements",
            ],
            severity="high",
            detection_method="metric_analysis",
            applies_to=["quality", "performance"],
        ),
        TheaterPattern(
            pattern_name="cherry_picked_results",
            description="Selective reporting of favorable results only",
            indicators=[
                "only best files analyzed",
                "ignoring test failures",
                "excluding problematic modules",
                "time window manipulation",
            ],
            severity="high",
            detection_method="completeness_analysis",
            applies_to=["quality", "security", "performance"],
        ),
        TheaterPattern(
            pattern_name="fake_refactoring",
            description="Cosmetic changes presented as structural improvements",
            indicators=[
                "only whitespace changes",
                "variable renaming without logic changes",
                "comment additions without code changes",
                "import reordering as optimization",
            ],
            severity="high",
            detection_method="diff_analysis",
            applies_to=["quality", "maintainability"],
        ),
        TheaterPattern(
            pattern_name="measurement_gaming",
            description="Manipulating measurement conditions for better results",
            indicators=[
                "excluding initialization from timing",
                "measuring empty test cases",
                "baseline from debug mode",
                "optimized build vs unoptimized baseline",
            ],
            severity="medium",
            detection_method="methodology_review",
            applies_to=["performance"],
        ),
        TheaterPattern(
            pattern_name="false_automation",
            description="Manual fixes claimed as automated improvements",
            indicators=[
                "instant fix claims for complex issues",
                "no automation code provided",
                "fixes that require human judgment",
                "pattern fixes without pattern detection",
            ],
            severity="medium",
            detection_method="automation_analysis",
            applies_to=["quality"],
        ),
        TheaterPattern(
            pattern_name="complexity_hiding",
            description="Moving complexity rather than reducing it",
            indicators=[
                "complexity moved to external files",
                "logic hidden in configuration",
                "problems moved to dependencies",
                "issues reclassified rather than fixed",
            ],
            severity="high",
            detection_method="structural_analysis",
            applies_to=["quality", "maintainability"],
        ),
        TheaterPattern(
            pattern_name="test_theater",
            description="Fake or meaningless test improvements",
            indicators=[
                "test coverage without assertions",
                "duplicate tests for coverage",
                "testing getters/setters only",
                "mocked everything tests",
            ],
            severity="high",
            detection_method="test_analysis",
            applies_to=["quality"],
        ),
    ]

    def __init__(
        self,
        patterns: Optional[List[TheaterPattern]] = None,
        thresholds: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize theater detector.

        Args:
            patterns: Optional custom patterns (uses defaults if not provided)
            thresholds: Optional custom thresholds
        """
        self.patterns = patterns or self.DEFAULT_PATTERNS.copy()
        self.thresholds = thresholds or {
            "minimum_improvement": 1.0,
            "maximum_believable": 95.0,
            "theater_threshold": 0.6,  # Above this = likely theater
            "pattern_match_threshold": 0.5,
        }
        self.detection_history: List[TheaterDetectionResult] = []

    def add_pattern(self, pattern: TheaterPattern) -> None:
        """Add a custom theater pattern"""
        self.patterns.append(pattern)

    def detect(
        self,
        claim_id: str,
        metric_name: str,
        improvement_percent: float,
        baseline_value: float,
        improved_value: float,
        measurement_method: str,
        description: str = "",
        claim_type: str = "quality",
        evidence_files: Optional[List[str]] = None,
    ) -> TheaterDetectionResult:
        """
        Detect theater patterns in a quality claim.

        Args:
            claim_id: Unique identifier for the claim
            metric_name: Name of the metric being claimed
            improvement_percent: Claimed improvement percentage
            baseline_value: Starting value
            improved_value: Ending value
            measurement_method: How the measurement was performed
            description: Description of the improvement
            claim_type: Type of claim (quality, performance, etc.)
            evidence_files: List of evidence file paths

        Returns:
            TheaterDetectionResult with detection outcome
        """
        evidence_files = evidence_files or []
        detected_patterns: List[str] = []
        pattern_details: List[TheaterPattern] = []

        # Check each pattern
        for pattern in self.patterns:
            if claim_type not in pattern.applies_to and "quality" not in pattern.applies_to:
                continue
            if not self._check_pattern(
                pattern,
                metric_name,
                improvement_percent,
                baseline_value,
                improved_value,
                measurement_method,
                description,
            ):
                continue
            detected_patterns.append(pattern.pattern_name)
            pattern_details.append(pattern)

        # Calculate theater confidence
        theater_confidence = self._calculate_theater_confidence(
            improvement_percent,
            measurement_method,
            evidence_files,
            detected_patterns,
        )

        # Determine if this is theater
        is_theater = (
            theater_confidence >= self.thresholds["theater_threshold"]
            or len(detected_patterns) >= 2
        )

        # Assess risk
        risk = self._assess_risk(theater_confidence, detected_patterns)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            is_theater, theater_confidence, detected_patterns
        )

        result = TheaterDetectionResult(
            claim_id=claim_id,
            is_theater=is_theater,
            confidence=theater_confidence,
            detected_patterns=detected_patterns,
            pattern_details=pattern_details,
            risk_assessment=risk,
            recommendation=recommendation,
            metadata={
                "metric_name": metric_name,
                "improvement_percent": improvement_percent,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )

        self.detection_history.append(result)
        return result

    def _check_pattern(
        self,
        pattern: TheaterPattern,
        metric_name: str,
        improvement_percent: float,
        baseline_value: float,
        improved_value: float,
        measurement_method: str,
        description: str,
    ) -> bool:
        """Check if a specific theater pattern is present"""

        if pattern.pattern_name == "perfect_metrics":
            return (
                improved_value == 0
                or improvement_percent in {100.0, 0.0}
                or (improvement_percent > 95.0 and not measurement_method)
            )

        elif pattern.pattern_name == "vanity_metrics":
            metric_lower = metric_name.lower()
            vanity_keywords = ["lines", "files", "comments", "whitespace", "format", "loc"]
            return any(kw in metric_lower for kw in vanity_keywords)

        elif pattern.pattern_name == "cherry_picked_results":
            method_lower = measurement_method.lower()
            gaming_keywords = ["selected", "best", "excluding", "only", "subset", "sample"]
            return any(kw in method_lower for kw in gaming_keywords)

        elif pattern.pattern_name == "fake_refactoring":
            if "refactor" in description.lower():
                return improvement_percent < 5.0
            return False

        elif pattern.pattern_name == "measurement_gaming":
            method_lower = measurement_method.lower()
            gaming_keywords = ["excluding", "without", "ignoring", "skipping"]
            return any(kw in method_lower for kw in gaming_keywords)

        elif pattern.pattern_name == "false_automation":
            method_lower = measurement_method.lower()
            if "automatic" in method_lower or "automated" in method_lower:
                # If claiming automation but instant results on complex issues
                return improvement_percent > 80.0 and len(measurement_method) < 50
            return False

        elif pattern.pattern_name == "complexity_hiding":
            desc_lower = description.lower()
            hiding_keywords = ["moved", "relocated", "transferred", "delegated"]
            return any(kw in desc_lower for kw in hiding_keywords)

        elif pattern.pattern_name == "test_theater":
            metric_lower = metric_name.lower()
            if "coverage" in metric_lower or "test" in metric_lower:
                # Suspicious if 100% coverage or huge jump
                # Use epsilon comparison for float equality (avoids float precision issues)
                return improvement_percent > 50.0 or abs(improved_value - 100.0) < 0.01
            return False

        return False

    def _calculate_theater_confidence(
        self,
        improvement_percent: float,
        measurement_method: str,
        evidence_files: List[str],
        detected_patterns: List[str],
    ) -> float:
        """Calculate confidence that this is theater"""
        confidence = 0.0

        # Suspicious improvement magnitude
        if improvement_percent > 90.0:
            confidence += 0.3
        elif improvement_percent > 70.0:
            confidence += 0.15

        # Round number suspicion
        if improvement_percent in [10.0, 20.0, 25.0, 50.0, 75.0, 90.0, 100.0]:
            confidence += 0.15

        # Lack of methodology detail
        if len(measurement_method) < 30:
            confidence += 0.2

        # No evidence files
        if not evidence_files:
            confidence += 0.25
        elif len(evidence_files) < 2:
            confidence += 0.1

        # Pattern detection
        confidence += len(detected_patterns) * 0.15

        return min(1.0, confidence)

    def _assess_risk(
        self,
        confidence: float,
        detected_patterns: List[str],
    ) -> str:
        """Assess risk level"""
        if confidence >= 0.8 or len(detected_patterns) >= 3:
            return "high"
        elif confidence >= 0.5 or len(detected_patterns) >= 1:
            return "medium"
        else:
            return "low"

    def _generate_recommendation(
        self,
        is_theater: bool,
        confidence: float,
        detected_patterns: List[str],
    ) -> str:
        """Generate recommendation based on detection"""
        if is_theater and confidence >= 0.8:
            return (
                f"REJECT: High confidence theater detected. "
                f"Patterns: {', '.join(detected_patterns)}. "
                f"Require genuine evidence and reproducible methodology."
            )
        elif is_theater:
            return (
                f"SUSPICIOUS: Theater patterns detected ({', '.join(detected_patterns)}). "
                f"Request additional verification and independent review."
            )
        elif detected_patterns:
            return (
                f"CAUTION: Some theater indicators present ({', '.join(detected_patterns)}). "
                f"Consider additional scrutiny."
            )
        else:
            return "ACCEPTABLE: No significant theater patterns detected."

    def detect_systemic_theater(
        self,
        claims: List[Dict[str, Any]],
    ) -> SystemicTheaterResult:
        """
        Detect systemic patterns across multiple claims.

        Args:
            claims: List of claim dictionaries with keys:
                   - claim_id, improvement_percent, timestamp, evidence_files

        Returns:
            SystemicTheaterResult with systemic analysis
        """
        if len(claims) < 2:
            return SystemicTheaterResult(
                systemic_indicators=[],
                risk_assessment="low",
                recommendation="Need at least 2 claims for systemic analysis",
                claim_count=len(claims),
                suspicious_patterns={},
            )

        systemic_indicators: List[str] = []
        suspicious_patterns: Dict[str, int] = {}

        improvements = [c.get("improvement_percent", 0) for c in claims]

        # Check for uniform improvements (low variance)
        if len(improvements) >= 2:
            try:
                stdev = statistics.stdev(improvements)
                if stdev < 3.0:
                    systemic_indicators.append("uniform_improvements_across_claims")
                    suspicious_patterns["uniform_improvements"] = len(claims)
            except statistics.StatisticsError:
                pass

        # Check for escalating claims
        if all(improvements[i] < improvements[i + 1] for i in range(len(improvements) - 1)):
            systemic_indicators.append("escalating_improvement_pattern")
            suspicious_patterns["escalating_pattern"] = len(claims)

        # Check for identical evidence patterns
        evidence_counts = [len(c.get("evidence_files", [])) for c in claims]
        if len(set(evidence_counts)) == 1:
            systemic_indicators.append("identical_evidence_structure")
            suspicious_patterns["identical_evidence"] = len(claims)

        # Check for timing patterns (with type conversion for timestamp comparison)
        timestamps = []
        for c in claims:
            ts = c.get("timestamp")
            if ts is not None:
                # Handle both numeric timestamps and datetime objects
                if isinstance(ts, (int, float)):
                    timestamps.append(float(ts))
                elif hasattr(ts, "timestamp"):
                    # datetime object - convert to Unix timestamp
                    timestamps.append(ts.timestamp())
        if len(timestamps) > 2:
            intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
            if all(abs(interval - intervals[0]) < 60 for interval in intervals):
                systemic_indicators.append("suspiciously_regular_timing")
                suspicious_patterns["regular_timing"] = len(claims)

        # Check for round number clustering (handle float comparisons properly)
        round_numbers = {10, 20, 25, 50, 75, 90, 100}
        round_count = sum(
            1 for imp in improvements
            if imp == int(imp) and int(imp) in round_numbers
        )
        if round_count >= len(claims) * 0.5:
            systemic_indicators.append("clustered_round_numbers")
            suspicious_patterns["round_numbers"] = round_count

        # Determine risk
        if len(systemic_indicators) >= 3:
            risk = "high"
            recommendation = "CRITICAL: Multiple systemic theater patterns. Full audit required."
        elif len(systemic_indicators) >= 2:
            risk = "high"
            recommendation = "WARNING: Systemic patterns suggest coordinated theater. Independent validation required."
        elif systemic_indicators:
            risk = "medium"
            recommendation = "CAUTION: Some systemic patterns detected. Additional scrutiny recommended."
        else:
            risk = "low"
            recommendation = "No systemic theater patterns detected."

        return SystemicTheaterResult(
            systemic_indicators=systemic_indicators,
            risk_assessment=risk,
            recommendation=recommendation,
            claim_count=len(claims),
            suspicious_patterns=suspicious_patterns,
            metadata={
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "improvements_analyzed": improvements,
            },
        )

    def export_report(
        self,
        output_path: Union[str, Path],
        include_history: bool = True,
    ) -> None:
        """
        Export detection report to JSON.

        Args:
            output_path: Path for output file
            include_history: Whether to include full detection history
        """
        report = {
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "detector_version": "1.0.0",
                "patterns_configured": len(self.patterns),
                "thresholds": self.thresholds,
            },
            "summary": {
                "total_detections": len(self.detection_history),
                "theater_detected": sum(1 for d in self.detection_history if d.is_theater),
                "high_risk": sum(1 for d in self.detection_history if d.risk_assessment == "high"),
            },
            "patterns": [p.to_dict() for p in self.patterns],
        }

        if include_history:
            report["detection_history"] = [d.to_dict() for d in self.detection_history]

        Path(output_path).write_text(json.dumps(report, indent=2))

    def clear_history(self) -> None:
        """Clear detection history"""
        self.detection_history.clear()


# Convenience functions for simple usage
def detect_theater(
    metric_name: str,
    improvement_percent: float,
    measurement_method: str = "",
    claim_id: str = "claim_001",
) -> TheaterDetectionResult:
    """
    Quick theater detection for a single claim.

    Args:
        metric_name: Name of the metric
        improvement_percent: Claimed improvement percentage
        measurement_method: How measurement was performed
        claim_id: Optional claim identifier

    Returns:
        TheaterDetectionResult
    """
    detector = TheaterDetector()
    return detector.detect(
        claim_id=claim_id,
        metric_name=metric_name,
        improvement_percent=improvement_percent,
        baseline_value=100.0,
        improved_value=100.0 - improvement_percent,
        measurement_method=measurement_method,
    )


def is_theater(
    improvement_percent: float,
    evidence_count: int = 0,
) -> bool:
    """
    Simple theater check based on improvement and evidence.

    Args:
        improvement_percent: Claimed improvement percentage
        evidence_count: Number of evidence files

    Returns:
        True if likely theater, False otherwise
    """
    # Quick heuristics
    if improvement_percent >= 95.0:
        return True
    if improvement_percent in [50.0, 75.0, 90.0, 100.0] and evidence_count < 2:
        return True
    if improvement_percent > 70.0 and evidence_count == 0:
        return True
    return False
