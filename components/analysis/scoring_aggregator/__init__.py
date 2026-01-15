"""
Scoring Aggregator - Generic weighted score aggregation with configurable grading.

A reusable component for combining multiple analyzer scores into a unified result.

Exports:
    - AnalyzerScore: Dataclass representing a single analyzer's score
    - AggregatedResult: Dataclass for the final aggregated result
    - GradeConfig: Configuration for grade calculation
    - GradeThreshold: Individual grade threshold definition
    - GradeMode: Enum for grading modes (LETTER, PASS_FAIL, NUMERIC, CUSTOM)
    - ConfidenceLevel: Dataclass for confidence information
    - ScoringAggregator: Main aggregator class
    - TextLengthConfidenceCalculator: Confidence based on text/sample length
    - create_quality_gate_aggregator: Factory for quality gate use cases
    - create_content_analysis_aggregator: Factory for content analysis use cases

Example:
    >>> from scoring_aggregator import ScoringAggregator, AnalyzerScore
    >>>
    >>> aggregator = ScoringAggregator()
    >>> scores = {
    ...     'analyzer_a': AnalyzerScore(score=15, max_score=20, weight=1.0),
    ...     'analyzer_b': AnalyzerScore(score=30, max_score=40, weight=1.5),
    ... }
    >>> result = aggregator.aggregate(scores)
    >>> print(f"Score: {result.total_score}, Grade: {result.grade['grade']}")
"""

from .scoring_aggregator import (
    # Core dataclasses
    AnalyzerScore,
    AggregatedResult,
    GradeConfig,
    GradeThreshold,
    GradeMode,
    ConfidenceLevel,

    # Main class
    ScoringAggregator,

    # Utility classes
    TextLengthConfidenceCalculator,

    # Factory functions
    create_quality_gate_aggregator,
    create_content_analysis_aggregator,
)

__all__ = [
    # Core dataclasses
    'AnalyzerScore',
    'AggregatedResult',
    'GradeConfig',
    'GradeThreshold',
    'GradeMode',
    'ConfidenceLevel',

    # Main class
    'ScoringAggregator',

    # Utility classes
    'TextLengthConfidenceCalculator',

    # Factory functions
    'create_quality_gate_aggregator',
    'create_content_analysis_aggregator',
]

__version__ = '1.0.0'
__author__ = 'David Youssef'
__source__ = 'D:\\Projects\\slop-detector\\backend\\scoring.py'
