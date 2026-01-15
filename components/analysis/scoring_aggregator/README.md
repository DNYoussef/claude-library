# Scoring Aggregator

Generic weighted score aggregation with configurable grading.

## Overview

A reusable component for combining multiple analyzer scores into a unified result with support for:

- **Weighted Aggregation**: Combine scores with configurable weights
- **Configurable Grading**: A-F letters, PASS/FAIL, numeric scales, or custom
- **Confidence Calculation**: Built-in or custom confidence calculators
- **Summary Generation**: Optional human-readable summaries

## Installation

Copy to your project or import from the library:

```python
from scoring_aggregator import ScoringAggregator, AnalyzerScore
```

## Requirements

- Python 3.7+
- Standard library only (no external dependencies)

## Quick Start

### Basic Usage

```python
from scoring_aggregator import ScoringAggregator, AnalyzerScore

# Create aggregator with default A-F grading
aggregator = ScoringAggregator()

# Add analyzer scores
scores = {
    'lexical': AnalyzerScore(score=18.5, max_score=25, weight=1.0),
    'structural': AnalyzerScore(score=12.0, max_score=20, weight=1.0),
    'statistical': AnalyzerScore(score=28.0, max_score=40, weight=1.0),
    'tonal': AnalyzerScore(score=8.0, max_score=15, weight=1.0),
}

# Get aggregated result
result = aggregator.aggregate(scores)

print(f"Total Score: {result.total_score}")
print(f"Grade: {result.grade['grade']} ({result.grade['label']})")
print(f"Confidence: {result.confidence.level} ({result.confidence.percentage}%)")
```

### Simplified Tuple Interface

```python
result = aggregator.aggregate_simple([
    ('lexical', 18.5, 25),
    ('structural', 12.0, 20),
    ('statistical', 28.0, 40, 1.5),  # Optional weight
])
```

## Grading Configurations

### Letter Grades (A-F)

```python
from scoring_aggregator import ScoringAggregator, GradeConfig

# Default: Higher scores = worse grades (for defect/issue scoring)
config = GradeConfig.letter_grades(invert=True)

# Alternative: Higher scores = better grades (for quality scoring)
config = GradeConfig.letter_grades(invert=False)

aggregator = ScoringAggregator(grade_config=config)
```

**Default Thresholds:**
| Score Range | Grade | Label |
|-------------|-------|-------|
| 0-20 | A | Excellent |
| 21-40 | B | Good |
| 41-60 | C | Fair |
| 61-80 | D | Poor |
| 81-100 | F | Failing |

### Pass/Fail

```python
# Pass if score <= 30 (for defect scoring)
config = GradeConfig.pass_fail(threshold=30, invert=True)

# Pass if score >= 70 (for quality scoring)
config = GradeConfig.pass_fail(threshold=70, invert=False)

aggregator = ScoringAggregator(grade_config=config)
```

### Numeric Scale (1-5, 1-10, etc.)

```python
# 5-star rating scale
config = GradeConfig.numeric_scale(scale=5)

# 10-point scale
config = GradeConfig.numeric_scale(scale=10)

aggregator = ScoringAggregator(grade_config=config)
```

### Custom Thresholds

```python
from scoring_aggregator import GradeConfig, GradeThreshold, GradeMode

config = GradeConfig(
    mode=GradeMode.CUSTOM,
    thresholds=[
        GradeThreshold(10, 'PERFECT', 'Perfect', 'No issues detected'),
        GradeThreshold(25, 'GOOD', 'Good', 'Minor issues'),
        GradeThreshold(50, 'ACCEPTABLE', 'Acceptable', 'Some issues'),
        GradeThreshold(100, 'NEEDS_WORK', 'Needs Work', 'Significant issues'),
    ],
    invert=True  # Lower scores are better
)
```

## Confidence Calculation

### Default (Analyzer Count Based)

The default confidence calculator uses the number of analyzers:

| Analyzers | Confidence | Percentage |
|-----------|------------|------------|
| 0 | None | 0% |
| 1 | Low | 60% |
| 2 | Medium | 75% |
| 3-4 | High | 85% |
| 5+ | Very High | 95% |

### Text Length Based

For content analysis where sample size matters:

```python
from scoring_aggregator import ScoringAggregator, TextLengthConfidenceCalculator

confidence_calc = TextLengthConfidenceCalculator(
    thresholds=[
        (0, 'Low', 60, 'Text too short'),
        (100, 'Medium', 75, 'Moderate length'),
        (300, 'High', 85, 'Good length'),
        (1000, 'Very High', 95, 'Excellent sample'),
    ],
    length_key='word_count'
)

aggregator = ScoringAggregator(
    confidence_calculator=lambda scores: confidence_calc(scores, {'word_count': 500})
)
```

### Custom Confidence Calculator

```python
def my_confidence(scores):
    from scoring_aggregator import ConfidenceLevel

    # Your custom logic
    avg_percentage = sum(s.percentage for s in scores.values()) / len(scores)

    if avg_percentage > 80:
        return ConfidenceLevel('High', 90, 'Strong signal from all analyzers')
    else:
        return ConfidenceLevel('Medium', 70, 'Mixed signals')

aggregator = ScoringAggregator(confidence_calculator=my_confidence)
```

## Summary Generation

Add custom summary generation:

```python
def my_summary(score, scores, grade):
    if grade['grade'] == 'A':
        return "Excellent quality - no issues detected."
    elif grade['grade'] in ['B', 'C']:
        return f"Acceptable quality with {score:.0f}% issue rate."
    else:
        return f"Quality issues detected. Score: {score:.0f}%"

aggregator = ScoringAggregator(summary_generator=my_summary)
```

## Factory Functions

### Quality Gate Aggregator

For CI/CD quality gates where lower scores are better:

```python
from scoring_aggregator import create_quality_gate_aggregator

aggregator = create_quality_gate_aggregator(
    pass_threshold=70,  # Pass if score <= 30 (inverted)
    invert=True
)

result = aggregator.aggregate(scores)
if result.grade['grade'] == 'PASS':
    print("Quality gate passed!")
```

### Content Analysis Aggregator

For content analysis (like slop detection):

```python
from scoring_aggregator import create_content_analysis_aggregator

aggregator = create_content_analysis_aggregator()
# Pre-configured with:
# - Inverted letter grades (lower = better)
# - Text length confidence calculator
# - Content-specific summary generator
```

## Data Classes

### AnalyzerScore

```python
@dataclass
class AnalyzerScore:
    score: float       # Raw score (0 to max_score)
    max_score: float   # Maximum possible
    weight: float      # Weight multiplier (default 1.0)
    name: str          # Optional identifier
    metadata: dict     # Optional extra data

    # Properties
    .percentage        # Score as percentage of max
    .weighted_score    # score * weight
    .weighted_max      # max_score * weight
    .to_dict()         # Dictionary representation
```

### AggregatedResult

```python
@dataclass
class AggregatedResult:
    total_score: float              # Normalized score (0-100)
    raw_score: float                # Sum of weighted scores
    max_possible: float             # Maximum possible weighted sum
    grade: Dict[str, Any]           # Grade info dict
    confidence: ConfidenceLevel     # Confidence details
    breakdown: Dict[str, Dict]      # Per-analyzer breakdown
    summary: str                    # Optional summary text

    # Properties
    .normalized_percentage          # raw_score / max_possible * 100
    .to_dict()                      # Dictionary representation
```

### ConfidenceLevel

```python
@dataclass
class ConfidenceLevel:
    level: str         # 'Low', 'Medium', 'High', 'Very High'
    percentage: float  # 0-100
    reason: str        # Explanation
```

## Output Format

The `to_dict()` method returns:

```python
{
    'total_score': 66.5,
    'raw_score': 66.5,
    'max_possible': 100.0,
    'normalized_percentage': 66.5,
    'grade': {
        'grade': 'C',
        'label': 'Fair',
        'description': 'Average performance'
    },
    'confidence': {
        'level': 'High',
        'percentage': 85,
        'reason': 'Multiple analyzers provide good coverage'
    },
    'breakdown': {
        'lexical': {
            'score': 18.5,
            'max_score': 25,
            'weight': 1.0,
            'percentage': 74.0,
            'weighted_score': 18.5,
            'name': 'lexical',
            'metadata': {}
        },
        # ... other analyzers
    },
    'summary': ''
}
```

## Use Cases

1. **Content Quality Analysis**: Slop detection, AI text detection, readability scoring
2. **Code Quality Gates**: Connascence analysis, linting aggregation, test coverage
3. **Security Scoring**: Vulnerability aggregation, risk assessment
4. **Performance Metrics**: Multi-dimensional performance scoring
5. **Review Aggregation**: Combining multiple reviewer scores

## Source

Extracted and generalized from: `D:\Projects\slop-detector\backend\scoring.py`

## License

MIT License - Free to use and modify.
