"""
Scoring Aggregator - Generic weighted score aggregation with configurable grading.

A reusable component for combining multiple analyzer scores into a unified result
with support for weighted aggregation, configurable grade thresholds, and confidence
calculation.

Extracted from: D:/Projects/slop-detector/backend/scoring.py
Generalized for: Multi-analyzer scoring systems (quality gates, content analysis, etc.)

Usage:
    from scoring_aggregator import ScoringAggregator, AnalyzerScore, GradeConfig

    # Create aggregator with default A-F grading
    aggregator = ScoringAggregator()

    # Add analyzer scores
    scores = {
        'lexical': AnalyzerScore(score=18.5, max_score=25, weight=1.0),
        'structural': AnalyzerScore(score=12.0, max_score=20, weight=1.0),
        'statistical': AnalyzerScore(score=28.0, max_score=40, weight=1.0),
    }

    # Get aggregated result
    result = aggregator.aggregate(scores)
    print(result.total_score, result.grade, result.confidence)
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Callable
from enum import Enum


class GradeMode(Enum):
    """Grading mode selection."""
    LETTER = "letter"      # A, B, C, D, F
    PASS_FAIL = "pass_fail"  # PASS, FAIL
    NUMERIC = "numeric"    # 1-5 or 1-10 scale
    CUSTOM = "custom"      # User-defined grades


@dataclass
class AnalyzerScore:
    """
    Represents a single analyzer's score contribution.

    Attributes:
        score: The raw score from the analyzer (0 to max_score)
        max_score: Maximum possible score for this analyzer (must be > 0)
        weight: Weight multiplier for aggregation (default 1.0, must be >= 0)
        name: Optional name for identification
        metadata: Optional additional data from the analyzer
    """
    score: float
    max_score: float
    weight: float = 1.0
    name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate score constraints after initialization."""
        if self.max_score <= 0:
            raise ValueError(f"max_score must be positive, got {self.max_score}")
        if self.score < 0:
            raise ValueError(f"score must be non-negative, got {self.score}")
        if self.weight < 0:
            raise ValueError(f"weight must be non-negative, got {self.weight}")
        if self.score > self.max_score:
            raise ValueError(
                f"score ({self.score}) cannot exceed max_score ({self.max_score})"
            )

    @property
    def percentage(self) -> float:
        """Calculate percentage of max score achieved."""
        # max_score is guaranteed > 0 by __post_init__ validation
        return round((self.score / self.max_score) * 100, 1)

    @property
    def weighted_score(self) -> float:
        """Calculate weighted score contribution."""
        return self.score * self.weight

    @property
    def weighted_max(self) -> float:
        """Calculate weighted maximum score."""
        return self.max_score * self.weight

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'score': round(self.score, 2),
            'max_score': self.max_score,
            'weight': self.weight,
            'percentage': self.percentage,
            'weighted_score': round(self.weighted_score, 2),
            'name': self.name,
            'metadata': self.metadata
        }


@dataclass
class GradeThreshold:
    """
    Defines a grade threshold boundary.

    Attributes:
        max_value: Upper bound for this grade (inclusive)
        grade: Grade identifier (e.g., 'A', 'PASS', 5)
        label: Human-readable label
        description: Detailed description of what this grade means
    """
    max_value: float
    grade: str
    label: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'grade': self.grade,
            'label': self.label,
            'description': self.description
        }


@dataclass
class GradeConfig:
    """
    Configuration for grade calculation.

    Attributes:
        mode: Grading mode (letter, pass_fail, numeric, custom)
        thresholds: List of grade thresholds (ordered by max_value ascending)
        invert: If True, lower scores are better (default False)
    """
    mode: GradeMode
    thresholds: list[GradeThreshold]
    invert: bool = False

    @classmethod
    def letter_grades(cls, invert: bool = False) -> 'GradeConfig':
        """
        Create standard A-F letter grade configuration.

        Args:
            invert: If True, lower scores get better grades (e.g., for defect scoring)
        """
        thresholds = [
            GradeThreshold(20, 'A', 'Excellent', 'Outstanding performance'),
            GradeThreshold(40, 'B', 'Good', 'Above average performance'),
            GradeThreshold(60, 'C', 'Fair', 'Average performance'),
            GradeThreshold(80, 'D', 'Poor', 'Below average performance'),
            GradeThreshold(100, 'F', 'Failing', 'Unsatisfactory performance'),
        ]
        return cls(mode=GradeMode.LETTER, thresholds=thresholds, invert=invert)

    @classmethod
    def pass_fail(cls, threshold: float = 50.0, invert: bool = False) -> 'GradeConfig':
        """
        Create PASS/FAIL grade configuration.

        Args:
            threshold: Score threshold for passing (default 50)
            invert: If True, scores below threshold pass (e.g., for defect scoring)
        """
        thresholds = [
            GradeThreshold(threshold, 'PASS', 'Passed', 'Meets requirements'),
            GradeThreshold(100, 'FAIL', 'Failed', 'Does not meet requirements'),
        ]
        return cls(mode=GradeMode.PASS_FAIL, thresholds=thresholds, invert=invert)

    @classmethod
    def numeric_scale(cls, scale: int = 5, invert: bool = False) -> 'GradeConfig':
        """
        Create numeric scale grade configuration (1-N scale).

        Args:
            scale: Maximum grade value (default 5)
            invert: If True, lower scores get higher grades

        Note:
            Uses floating-point division for step calculation. For applications
            requiring precise threshold boundaries (e.g., financial grading),
            consider using decimal.Decimal or custom threshold values.
        """
        step = 100 / scale
        thresholds = []
        for i in range(1, scale + 1):
            thresholds.append(GradeThreshold(
                i * step,
                str(scale - i + 1) if not invert else str(i),
                f'Level {scale - i + 1}' if not invert else f'Level {i}',
                ''
            ))
        return cls(mode=GradeMode.NUMERIC, thresholds=thresholds, invert=invert)


@dataclass
class ConfidenceLevel:
    """
    Represents confidence in the aggregated result.

    Attributes:
        level: Confidence level name (Low, Medium, High, Very High)
        percentage: Numeric confidence (0-100)
        reason: Explanation for the confidence level
    """
    level: str
    percentage: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'level': self.level,
            'percentage': self.percentage,
            'reason': self.reason
        }


@dataclass
class AggregatedResult:
    """
    The final aggregated scoring result.

    Attributes:
        total_score: Combined weighted score (0-100 normalized)
        raw_score: Sum of weighted scores before normalization
        max_possible: Maximum possible score
        grade: Grade information dict
        confidence: Confidence level information
        breakdown: Per-analyzer score breakdown
        summary: Human-readable summary
    """
    total_score: float
    raw_score: float
    max_possible: float
    grade: dict[str, Any]
    confidence: ConfidenceLevel
    breakdown: dict[str, dict[str, Any]]
    summary: str = ""

    @property
    def normalized_percentage(self) -> float:
        """Get score as percentage of max possible."""
        if self.max_possible == 0:
            return 0.0
        return round((self.raw_score / self.max_possible) * 100, 1)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'total_score': round(self.total_score, 1),
            'raw_score': round(self.raw_score, 2),
            'max_possible': self.max_possible,
            'normalized_percentage': self.normalized_percentage,
            'grade': self.grade,
            'confidence': self.confidence.to_dict(),
            'breakdown': self.breakdown,
            'summary': self.summary
        }


class ScoringAggregator:
    """
    Generic weighted score aggregator with configurable grading.

    Combines multiple analyzer scores into a unified result using weighted
    aggregation with support for different grading schemes and confidence
    calculation.

    Attributes:
        grade_config: Configuration for grade calculation
        confidence_calculator: Optional custom confidence calculator
        summary_generator: Optional custom summary generator
        max_total: Maximum total score (for capping, default 100)
    """

    def __init__(
        self,
        grade_config: Optional[GradeConfig] = None,
        confidence_calculator: Optional[Callable[[dict[str, AnalyzerScore], Optional[dict[str, Any]]], ConfidenceLevel]] = None,
        summary_generator: Optional[Callable[[float, dict[str, AnalyzerScore], dict[str, Any]], str]] = None,
        max_total: float = 100.0
    ):
        """
        Initialize the scoring aggregator.

        Args:
            grade_config: Grade configuration (defaults to A-F letter grades)
            confidence_calculator: Custom function to calculate confidence
            summary_generator: Custom function to generate summary text
            max_total: Maximum total score cap (default 100)
        """
        self.grade_config = grade_config or GradeConfig.letter_grades()
        self.confidence_calculator = confidence_calculator or self._default_confidence
        self.summary_generator = summary_generator
        self.max_total = max_total

    def aggregate(
        self,
        scores: dict[str, AnalyzerScore],
        context: Optional[dict[str, Any]] = None
    ) -> AggregatedResult:
        """
        Aggregate multiple analyzer scores into a unified result.

        Args:
            scores: Dictionary mapping analyzer names to AnalyzerScore objects
            context: Optional context dict for confidence/summary calculation

        Returns:
            AggregatedResult with total score, grade, confidence, and breakdown
        """
        context = context or {}

        # Calculate raw weighted sum
        raw_score = sum(s.weighted_score for s in scores.values())
        max_possible = sum(s.weighted_max for s in scores.values())

        # Normalize to percentage scale
        if max_possible > 0:
            normalized_score = (raw_score / max_possible) * 100
        else:
            normalized_score = 0.0

        # Cap at max_total
        total_score = min(normalized_score, self.max_total)

        # Calculate grade
        grade = self._calculate_grade(total_score)

        # Calculate confidence (pass context for custom calculators)
        confidence = self.confidence_calculator(scores, context)

        # Build breakdown
        breakdown = {}
        for name, analyzer_score in scores.items():
            breakdown[name] = analyzer_score.to_dict()

        # Generate summary
        summary = ""
        if self.summary_generator:
            summary = self.summary_generator(total_score, scores, grade)

        return AggregatedResult(
            total_score=total_score,
            raw_score=raw_score,
            max_possible=max_possible,
            grade=grade,
            confidence=confidence,
            breakdown=breakdown,
            summary=summary
        )

    def aggregate_simple(
        self,
        scores: list[tuple],
        context: Optional[dict[str, Any]] = None
    ) -> AggregatedResult:
        """
        Simplified aggregation with tuples.

        Args:
            scores: List of (name, score, max_score) or (name, score, max_score, weight) tuples
            context: Optional context for confidence calculation

        Returns:
            AggregatedResult

        Raises:
            ValueError: If tuple length is not 3 or 4
        """
        score_dict = {}
        for item in scores:
            item_len = len(item)
            if item_len == 3:
                name, score, max_score = item
                weight = 1.0
            elif item_len == 4:
                name, score, max_score, weight = item
            else:
                raise ValueError(
                    f"Score tuple must have 3 or 4 elements (name, score, max_score[, weight]), "
                    f"got {item_len} elements: {item!r}"
                )
            score_dict[name] = AnalyzerScore(
                score=score,
                max_score=max_score,
                weight=weight,
                name=name
            )
        return self.aggregate(score_dict, context)

    def _calculate_grade(self, score: float) -> dict[str, Any]:
        """
        Calculate grade from score using configured thresholds.

        Args:
            score: Normalized score (0-100)

        Returns:
            Grade information dictionary
        """
        effective_score = score
        if self.grade_config.invert:
            effective_score = 100 - score

        for threshold in self.grade_config.thresholds:
            if effective_score <= threshold.max_value:
                return threshold.to_dict()

        # Fallback to last threshold
        return self.grade_config.thresholds[-1].to_dict()

    def _default_confidence(
        self,
        scores: dict[str, AnalyzerScore],
        context: Optional[dict[str, Any]] = None
    ) -> ConfidenceLevel:
        """
        Default confidence calculator based on number of analyzers and score variance.

        More analyzers and lower variance = higher confidence.

        Args:
            scores: Dictionary of analyzer scores
            context: Optional context (unused in default implementation)
        """
        # context parameter accepted for API consistency but unused in default impl
        _ = context
        num_analyzers = len(scores)

        if num_analyzers == 0:
            return ConfidenceLevel('None', 0, 'No analyzers provided')

        if num_analyzers == 1:
            return ConfidenceLevel('Low', 60, 'Single analyzer - limited perspective')

        if num_analyzers == 2:
            return ConfidenceLevel('Medium', 75, 'Two analyzers - moderate confidence')

        if num_analyzers <= 4:
            return ConfidenceLevel('High', 85, 'Multiple analyzers provide good coverage')

        return ConfidenceLevel('Very High', 95, 'Comprehensive multi-analyzer coverage')


class TextLengthConfidenceCalculator:
    """
    Confidence calculator based on text/sample length.

    Useful for content analysis where longer samples provide more reliable results.
    """

    def __init__(
        self,
        thresholds: Optional[list[tuple]] = None,
        length_key: str = 'word_count'
    ):
        """
        Initialize with custom thresholds.

        Args:
            thresholds: List of (min_length, level, percentage, reason) tuples
            length_key: Key in context dict containing the length value
        """
        self.thresholds = thresholds or [
            (0, 'Low', 60, 'Text too short for reliable analysis'),
            (50, 'Medium', 75, 'Moderate text length'),
            (150, 'High', 85, 'Good text length for analysis'),
            (500, 'Very High', 95, 'Excellent sample size'),
        ]
        self.length_key = length_key

    def __call__(
        self,
        scores: dict[str, AnalyzerScore],
        context: Optional[dict[str, Any]] = None
    ) -> ConfidenceLevel:
        """Calculate confidence based on text length from context."""
        context = context or {}
        length = context.get(self.length_key, 0)

        # Also check metadata in scores for length info
        if length == 0:
            for score in scores.values():
                if self.length_key in score.metadata:
                    length = score.metadata[self.length_key]
                    break

        result = self.thresholds[0]
        for min_length, level, percentage, reason in self.thresholds:
            if length < min_length:
                continue
            result = (min_length, level, percentage, reason)

        return ConfidenceLevel(result[1], result[2], result[3])


def create_quality_gate_aggregator(
    pass_threshold: float = 70.0,
    invert: bool = True
) -> ScoringAggregator:
    """
    Factory function to create a quality gate aggregator.

    For quality gates, lower scores typically mean better quality (fewer issues),
    so invert=True makes lower scores pass.

    Args:
        pass_threshold: Score threshold for passing (default 70)
        invert: If True, lower scores pass (default True for quality gates)

    Returns:
        Configured ScoringAggregator
    """
    config = GradeConfig.pass_fail(threshold=pass_threshold, invert=invert)
    return ScoringAggregator(grade_config=config)


def create_content_analysis_aggregator() -> ScoringAggregator:
    """
    Factory function for content analysis (like slop detection).

    Uses inverted letter grades where lower scores are better.

    Returns:
        Configured ScoringAggregator for content analysis
    """
    config = GradeConfig.letter_grades(invert=True)
    confidence_calc = TextLengthConfidenceCalculator()

    def summary_generator(score: float, scores: dict[str, AnalyzerScore], grade: dict[str, Any]) -> str:
        """Generate content analysis summary."""
        letter = grade.get('grade', 'C')
        if letter == 'A':
            return "Content appears authentically human-written."
        elif letter == 'B':
            return "Content shows minor AI-like patterns but largely reads naturally."
        elif letter == 'C':
            return "Content has notable AI writing characteristics."
        elif letter == 'D':
            return "Content shows strong AI writing patterns."
        else:
            return "Content exhibits significant AI characteristics throughout."

    return ScoringAggregator(
        grade_config=config,
        confidence_calculator=lambda s, ctx=None: confidence_calc(s, ctx),
        summary_generator=summary_generator
    )
