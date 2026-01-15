"""
Quality Validator Component

Evidence-based quality validation with theater detection capabilities.
Provides threshold-based confidence scoring and pass/fail quality gate logic.

Zero external dependencies - stdlib only.

Exported Classes:
    - QualityValidator: Main validation orchestrator
    - QualityClaim: Quality improvement claim dataclass
    - ValidationResult: Validation outcome dataclass
    - Violation: Quality violation dataclass
    - AnalysisResult: Analysis results container
    - TheaterDetector: Fake quality pattern detector
    - TheaterPattern: Theater pattern definition
    - TheaterDetectionResult: Theater detection outcome
    - SystemicTheaterResult: Multi-claim theater analysis

Exported Enums:
    - Severity: Violation severity levels
    - EvidenceQuality: Evidence quality categories
    - RiskLevel: Risk assessment levels

Exported Functions:
    - detect_theater(): Quick single-claim theater detection
    - is_theater(): Simple boolean theater check

Example Usage:
    from quality_validator import QualityValidator, QualityClaim

    # Basic violation tracking
    validator = QualityValidator()
    validator.add_violation(
        rule_id="QUAL001",
        message="Function exceeds complexity threshold",
        file="src/main.py",
        line=42,
        severity="high",
    )

    result = validator.analyze()
    if result.quality_gate_passed:
        print("Quality gate passed!")
    else:
        print(f"Failed: {result.metrics['total_violations']} violations")

    # Claim validation
    claim = QualityClaim(
        claim_id="claim_001",
        description="Refactored auth module",
        metric_name="cyclomatic_complexity",
        baseline_value=25.0,
        improved_value=12.0,
        improvement_percent=52.0,
        measurement_method="Analyzed all files with radon",
        evidence_files=["before.json", "after.json"],
        timestamp=time.time(),
    )
    validation = validator.validate_claim(claim)
    print(f"Claim valid: {validation.is_valid}")

    # Theater detection
    from quality_validator import TheaterDetector

    detector = TheaterDetector()
    result = detector.detect(
        claim_id="claim_002",
        metric_name="test_coverage",
        improvement_percent=100.0,
        baseline_value=0.0,
        improved_value=100.0,
        measurement_method="Ran pytest",
    )
    print(f"Is theater: {result.is_theater}")
"""

from .quality_validator import (
    # Main class
    QualityValidator,
    # Dataclasses
    QualityClaim,
    QualityValidationResult,
    ValidationResult,
    Violation,
    AnalysisResult,
    # Enums
    Severity,
    EvidenceQuality,
    RiskLevel,
)

from .theater_detector import (
    # Main class
    TheaterDetector,
    # Dataclasses
    TheaterPattern,
    TheaterDetectionResult,
    SystemicTheaterResult,
    # Convenience functions
    detect_theater,
    is_theater,
)

__all__ = [
    # quality_validator.py exports
    "QualityValidator",
    "QualityClaim",
    "QualityValidationResult",
    "ValidationResult",
    "Violation",
    "AnalysisResult",
    "Severity",
    "EvidenceQuality",
    "RiskLevel",
    # theater_detector.py exports
    "TheaterDetector",
    "TheaterPattern",
    "TheaterDetectionResult",
    "SystemicTheaterResult",
    "detect_theater",
    "is_theater",
]

__version__ = "1.0.0"
