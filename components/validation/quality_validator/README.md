# Quality Validator Component

Evidence-based quality validation system with theater detection capabilities. Provides threshold-based confidence scoring and pass/fail quality gate logic.

## Features

- **Violation Tracking**: Record and categorize quality violations
- **Quality Gate**: Configurable pass/fail thresholds by severity
- **Score Calculation**: Penalty-based scoring (100 - penalties)
- **Claim Validation**: Evidence-based validation of quality improvement claims
- **Theater Detection**: Detect fake/fraudulent quality improvements
- **Export Formats**: JSON and SARIF output support

## Installation

Copy the component directory to your project:

```
quality-validator/
  __init__.py
  quality_validator.py
  theater_detector.py
  README.md
```

Zero external dependencies - uses Python stdlib only.

## Quick Start

### Basic Violation Tracking

```python
from quality_validator import QualityValidator

validator = QualityValidator()

# Add violations
validator.add_violation(
    rule_id="QUAL001",
    message="Function exceeds complexity threshold",
    file="src/main.py",
    line=42,
    severity="high",
    category="complexity",
    fix_suggestion="Split into smaller functions",
)

validator.add_violation(
    rule_id="QUAL002",
    message="Missing type hints",
    file="src/utils.py",
    line=15,
    severity="low",
)

# Check quality gate
result = validator.analyze(fail_on="high")
print(f"Gate passed: {result.quality_gate_passed}")
print(f"Score: {result.overall_score}/100")
print(f"Violations: {result.metrics['total_violations']}")
```

### Quality Claim Validation

```python
from quality_validator import QualityValidator, QualityClaim
import time

validator = QualityValidator()

claim = QualityClaim(
    claim_id="refactor_001",
    description="Refactored authentication module for improved maintainability",
    metric_name="cyclomatic_complexity",
    baseline_value=25.0,
    improved_value=12.0,
    improvement_percent=52.0,
    measurement_method="Analyzed all auth module files using radon complexity analyzer before and after refactoring",
    evidence_files=["reports/before_complexity.json", "reports/after_complexity.json"],
    timestamp=time.time(),
)

result = validator.validate_claim(claim)

print(f"Valid: {result.is_valid}")
print(f"Confidence: {result.confidence_score:.2%}")
print(f"Evidence Quality: {result.evidence_quality}")
print(f"Risk Level: {result.risk_level}")
print(f"Recommendation: {result.recommendation}")

if result.theater_indicators:
    print(f"Theater Indicators: {', '.join(result.theater_indicators)}")
if result.genuine_indicators:
    print(f"Genuine Indicators: {', '.join(result.genuine_indicators)}")
```

### Theater Detection

```python
from quality_validator import TheaterDetector, detect_theater, is_theater

# Full detection
detector = TheaterDetector()

result = detector.detect(
    claim_id="perf_001",
    metric_name="test_coverage",
    improvement_percent=100.0,  # Suspicious!
    baseline_value=0.0,
    improved_value=100.0,
    measurement_method="Ran tests",  # Vague methodology
    description="Added comprehensive test coverage",
)

print(f"Is Theater: {result.is_theater}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Patterns: {', '.join(result.detected_patterns)}")
print(f"Risk: {result.risk_assessment}")

# Quick check function
quick_result = detect_theater(
    metric_name="code_quality",
    improvement_percent=90.0,
    measurement_method="selected best files",
)
print(f"Quick check - Theater: {quick_result.is_theater}")

# Simple boolean check
if is_theater(improvement_percent=100.0, evidence_count=0):
    print("Likely theater - no evidence provided")
```

### Systemic Theater Detection

```python
from quality_validator import TheaterDetector

detector = TheaterDetector()

# Multiple claims from same source
claims = [
    {"claim_id": "c1", "improvement_percent": 50.0, "timestamp": 1000, "evidence_files": ["e1.json"]},
    {"claim_id": "c2", "improvement_percent": 50.0, "timestamp": 1060, "evidence_files": ["e2.json"]},
    {"claim_id": "c3", "improvement_percent": 50.0, "timestamp": 1120, "evidence_files": ["e3.json"]},
]

result = detector.detect_systemic_theater(claims)

print(f"Systemic Indicators: {', '.join(result.systemic_indicators)}")
print(f"Risk: {result.risk_assessment}")
print(f"Recommendation: {result.recommendation}")
```

## Configuration

### QualityValidator Config

```python
config = {
    "thresholds": {
        "max_critical": 0,   # Zero tolerance for critical
        "max_high": 5,       # Up to 5 high severity
        "max_medium": 10,    # Up to 10 medium
        "max_low": 20,       # Up to 20 low
    },
    "scoring": {
        "penalties": {
            "critical": 10,  # -10 points per critical
            "high": 5,       # -5 points per high
            "medium": 2,     # -2 points per medium
            "low": 1,        # -1 point per low
            "info": 0,       # No penalty
        },
        "base_score": 100.0,
    },
    "validation": {
        "minimum_improvement": 1.0,     # Min believable improvement %
        "maximum_believable": 95.0,     # Max believable improvement %
        "confidence_threshold": 0.65,   # Required confidence
    },
}

validator = QualityValidator(config=config)
```

### TheaterDetector Custom Patterns

```python
from quality_validator import TheaterDetector, TheaterPattern

detector = TheaterDetector()

# Add custom pattern
detector.add_pattern(TheaterPattern(
    pattern_name="instant_optimization",
    description="Claims instant performance gains without profiling",
    indicators=[
        "no profiling data",
        "immediate 50%+ gains",
        "no benchmark methodology",
    ],
    severity="high",
    detection_method="performance_analysis",
    applies_to=["performance"],
))
```

## Theater Patterns Detected

| Pattern | Severity | Description |
|---------|----------|-------------|
| `perfect_metrics` | critical | Claims 100% or zero values without evidence |
| `vanity_metrics` | high | Focus on easily gamed metrics (lines, comments) |
| `cherry_picked_results` | high | Selective reporting, excluding failures |
| `fake_refactoring` | high | Cosmetic changes claimed as structural |
| `measurement_gaming` | medium | Manipulated measurement conditions |
| `false_automation` | medium | Manual fixes claimed as automated |
| `complexity_hiding` | high | Moving complexity rather than reducing |
| `test_theater` | high | Meaningless test improvements |

## Export Formats

### JSON Export

```python
validator.export_json("quality_report.json")
```

### SARIF Export (for GitHub Code Scanning)

```python
validator.export_sarif("quality_report.sarif")
```

### Theater Detection Report

```python
detector.export_report("theater_report.json", include_history=True)
```

## API Reference

### Classes

| Class | Description |
|-------|-------------|
| `QualityValidator` | Main validation orchestrator |
| `QualityClaim` | Quality improvement claim dataclass |
| `ValidationResult` | Validation outcome dataclass |
| `Violation` | Quality violation dataclass |
| `AnalysisResult` | Analysis results container |
| `TheaterDetector` | Fake quality pattern detector |
| `TheaterPattern` | Theater pattern definition |
| `TheaterDetectionResult` | Detection outcome |
| `SystemicTheaterResult` | Multi-claim analysis |

### Enums

| Enum | Values |
|------|--------|
| `Severity` | CRITICAL, HIGH, MEDIUM, LOW, INFO |
| `EvidenceQuality` | EXCELLENT, GOOD, FAIR, POOR, INSUFFICIENT |
| `RiskLevel` | LOW, MEDIUM, HIGH |

### Functions

| Function | Description |
|----------|-------------|
| `detect_theater()` | Quick single-claim detection |
| `is_theater()` | Simple boolean check |

## Sources

Extracted from:
- `D:\Projects\connascence\analyzer\theater_detection\detector.py`
- `D:\Projects\connascence\analyzer\quality_gates\unified_quality_gate.py`

## License

Internal component - part of Context Cascade ecosystem.
