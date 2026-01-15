"""
Pattern Matcher - Generic text pattern detection engine.

A reusable component for detecting patterns in text using both literal
string matching and regex patterns. Originally extracted from Slop Detector.

Zero external dependencies - uses only Python standard library.
"""

from __future__ import annotations

import logging
import re
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterator, TypedDict

# Configure module logger
logger = logging.getLogger(__name__)


class PatternMetadata(TypedDict, total=False):
    """TypedDict for pattern metadata fields."""
    source: str
    version: str
    author: str
    tags: list[str]
    examples: list[str]
    false_positive_rate: float
    last_updated: str


class SignalLevelStats(TypedDict):
    """TypedDict for signal level statistics."""
    count: int
    total_occurrences: int
    total_score: float


class MatchStatistics(TypedDict):
    """TypedDict for match statistics."""
    pattern_count: int
    total_occurrences: int
    text_word_count: int
    match_density: float
    by_signal_level: dict[str, SignalLevelStats]


class SignalLevel(Enum):
    """Signal strength levels for pattern matches."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class PatternType(Enum):
    """Type of pattern matching to use."""
    LITERAL = "literal"
    REGEX = "regex"
    WORD_BOUNDARY = "word_boundary"


@dataclass
class PatternDefinition:
    """
    Definition of a single pattern to match.

    Attributes:
        pattern: The pattern string (literal text or regex)
        weight: Base score/weight when pattern is matched
        signal_level: Severity/importance level
        pattern_type: How to interpret the pattern
        description: Human-readable description of what this pattern indicates
        case_sensitive: Whether matching should be case-sensitive
        max_multiplier: Maximum multiplier for repeated matches (caps scoring)
        category: Optional category for grouping patterns
        metadata: Optional additional metadata
    """
    pattern: str
    weight: float = 1.0
    signal_level: SignalLevel = SignalLevel.MEDIUM
    pattern_type: PatternType = PatternType.WORD_BOUNDARY
    description: str = ""
    case_sensitive: bool = False
    max_multiplier: float = 2.0
    category: str = ""
    metadata: PatternMetadata = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize default values after dataclass creation.

        Sets a default description based on the pattern if none was provided.
        """
        if not self.description:
            self.description = f"Pattern: {self.pattern}"


@dataclass
class PatternMatch:
    """
    Result of a single pattern match.

    Attributes:
        pattern: The pattern that was matched
        matched_text: The actual text that matched
        count: Number of times the pattern matched
        positions: Character positions where matches occurred
        signal_level: Severity level of this match
        score: Calculated score contribution
        description: Description of what this pattern indicates
        category: Category of the pattern
    """
    pattern: str
    matched_text: str
    count: int
    positions: list[int]
    signal_level: SignalLevel
    score: float
    description: str
    category: str = ""

    def to_dict(self) -> dict[str, str | int | float | list[int]]:
        """Convert to dictionary representation."""
        return {
            'pattern': self.pattern,
            'matched_text': self.matched_text,
            'count': self.count,
            'positions': self.positions,
            'signal_level': self.signal_level.value,
            'score': round(self.score, 2),
            'description': self.description,
            'category': self.category
        }


@dataclass
class PatternConfig:
    """
    Configuration for the pattern matcher.

    Attributes:
        max_score: Maximum total score (caps the result)
        score_precision: Decimal places for score rounding
        include_positions: Whether to track match positions
        merge_overlapping: Whether to merge overlapping matches
        summary_generator: Optional custom summary generator function
    """
    max_score: float | None = None
    score_precision: int = 1
    include_positions: bool = True
    merge_overlapping: bool = False
    summary_generator: Callable[[list[PatternMatch], float], str] | None = None


@dataclass
class MatchResult:
    """
    Complete result of pattern matching analysis.

    Attributes:
        score: Total calculated score
        max_score: Maximum possible score (if configured)
        matches: List of individual pattern matches
        summary: Human-readable summary
        categories: Matches grouped by category
        statistics: Additional statistics about the matches
    """
    score: float
    max_score: float | None
    matches: list[PatternMatch]
    summary: str
    categories: dict[str, list[PatternMatch]]
    statistics: MatchStatistics

    def to_dict(self) -> dict[str, float | None | list[dict] | str | dict]:
        """Convert to dictionary representation."""
        return {
            'score': self.score,
            'max_score': self.max_score,
            'matches': [m.to_dict() for m in self.matches],
            'summary': self.summary,
            'categories': {
                k: [m.to_dict() for m in v]
                for k, v in self.categories.items()
            },
            'statistics': self.statistics
        }


class LRUCache(OrderedDict):
    """Simple LRU cache implementation with maximum size limit."""

    def __init__(self, maxsize: int = 1024):
        """Initialize LRU cache with maximum size.

        Args:
            maxsize: Maximum number of items to store (default: 1024)
        """
        super().__init__()
        self.maxsize = maxsize

    def __getitem__(self, key: str) -> re.Pattern:
        """Get item and move to end (most recently used)."""
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key: str, value: re.Pattern) -> None:
        """Set item and evict oldest if at capacity."""
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self.maxsize:
            oldest = next(iter(self))
            del self[oldest]


class PatternDatabase:
    """
    Injectable database of patterns to match.

    Supports adding patterns individually, in bulk, or loading from
    dictionary format for easy serialization.
    """

    # Default maximum cache size for compiled regex patterns
    DEFAULT_CACHE_SIZE = 1024

    def __init__(self, cache_maxsize: int = DEFAULT_CACHE_SIZE):
        """Initialize pattern database.

        Args:
            cache_maxsize: Maximum number of compiled regex patterns to cache
        """
        self._patterns: list[PatternDefinition] = []
        self._compiled_cache: LRUCache = LRUCache(maxsize=cache_maxsize)

    def add_pattern(self, pattern: PatternDefinition) -> PatternDatabase:
        """Add a single pattern definition. Returns self for chaining."""
        self._patterns.append(pattern)
        return self

    def add_patterns(self, patterns: list[PatternDefinition]) -> PatternDatabase:
        """Add multiple pattern definitions. Returns self for chaining."""
        self._patterns.extend(patterns)
        return self

    def add_literal(
        self,
        text: str,
        weight: float = 1.0,
        signal_level: SignalLevel = SignalLevel.MEDIUM,
        description: str = "",
        case_sensitive: bool = False,
        category: str = ""
    ) -> PatternDatabase:
        """Convenience method to add a literal pattern. Returns self for chaining."""
        self._patterns.append(PatternDefinition(
            pattern=text,
            weight=weight,
            signal_level=signal_level,
            pattern_type=PatternType.LITERAL,
            description=description or f"Literal match: {text}",
            case_sensitive=case_sensitive,
            category=category
        ))
        return self

    def add_word(
        self,
        word: str,
        weight: float = 1.0,
        signal_level: SignalLevel = SignalLevel.MEDIUM,
        description: str = "",
        case_sensitive: bool = False,
        category: str = ""
    ) -> PatternDatabase:
        """Convenience method to add a word-boundary pattern. Returns self for chaining."""
        self._patterns.append(PatternDefinition(
            pattern=word,
            weight=weight,
            signal_level=signal_level,
            pattern_type=PatternType.WORD_BOUNDARY,
            description=description or f"Word: {word}",
            case_sensitive=case_sensitive,
            category=category
        ))
        return self

    def add_regex(
        self,
        regex: str,
        weight: float = 1.0,
        signal_level: SignalLevel = SignalLevel.MEDIUM,
        description: str = "",
        case_sensitive: bool = False,
        category: str = ""
    ) -> PatternDatabase:
        """Convenience method to add a regex pattern. Returns self for chaining."""
        self._patterns.append(PatternDefinition(
            pattern=regex,
            weight=weight,
            signal_level=signal_level,
            pattern_type=PatternType.REGEX,
            description=description or f"Regex: {regex}",
            case_sensitive=case_sensitive,
            category=category
        ))
        return self

    def load_from_dict(self, data: dict[str, list | dict]) -> PatternDatabase:
        """
        Load patterns from dictionary format.

        Expected format:
        {
            "patterns": [
                {
                    "pattern": "string",
                    "weight": 1.0,
                    "signal_level": "HIGH",
                    "pattern_type": "word_boundary",
                    "description": "...",
                    "case_sensitive": false,
                    "category": "..."
                },
                ...
            ]
        }

        Or simple format:
        {
            "words": {"word": weight, ...},
            "phrases": [{"pattern": "...", "weight": 1.0, "description": "..."}, ...]
        }
        """
        if "patterns" in data:
            for p in data["patterns"]:
                self._patterns.append(PatternDefinition(
                    pattern=p["pattern"],
                    weight=p.get("weight", 1.0),
                    signal_level=SignalLevel(p.get("signal_level", "MEDIUM")),
                    pattern_type=PatternType(p.get("pattern_type", "word_boundary")),
                    description=p.get("description", ""),
                    case_sensitive=p.get("case_sensitive", False),
                    max_multiplier=p.get("max_multiplier", 2.0),
                    category=p.get("category", ""),
                    metadata=p.get("metadata", {})
                ))

        if "words" in data:
            for word, weight in data["words"].items():
                self.add_word(word, weight=weight, category="words")

        if "phrases" in data:
            for phrase in data["phrases"]:
                if isinstance(phrase, dict):
                    self.add_regex(
                        phrase["pattern"],
                        weight=phrase.get("weight", 1.0),
                        description=phrase.get("description", ""),
                        category="phrases"
                    )
                else:
                    self.add_regex(phrase, category="phrases")

        return self

    def to_dict(self) -> dict[str, list[dict]]:
        """Export patterns to dictionary format."""
        return {
            "patterns": [
                {
                    "pattern": p.pattern,
                    "weight": p.weight,
                    "signal_level": p.signal_level.value,
                    "pattern_type": p.pattern_type.value,
                    "description": p.description,
                    "case_sensitive": p.case_sensitive,
                    "max_multiplier": p.max_multiplier,
                    "category": p.category,
                    "metadata": p.metadata
                }
                for p in self._patterns
            ]
        }

    def __iter__(self) -> Iterator[PatternDefinition]:
        """Iterate over patterns."""
        return iter(self._patterns)

    def __len__(self) -> int:
        """Return number of patterns."""
        return len(self._patterns)

    def clear(self) -> PatternDatabase:
        """Remove all patterns. Returns self for chaining."""
        self._patterns.clear()
        self._compiled_cache.clear()
        return self

    def get_compiled_regex(self, pattern_def: PatternDefinition) -> re.Pattern | None:
        """Get compiled regex for a pattern, with caching.

        Args:
            pattern_def: The pattern definition to compile

        Returns:
            Compiled regex pattern, or None if the pattern is invalid
        """
        cache_key = f"{pattern_def.pattern}:{pattern_def.pattern_type.value}:{pattern_def.case_sensitive}"

        if cache_key not in self._compiled_cache:
            flags = 0 if pattern_def.case_sensitive else re.IGNORECASE

            if pattern_def.pattern_type == PatternType.LITERAL:
                regex = re.escape(pattern_def.pattern)
            elif pattern_def.pattern_type == PatternType.WORD_BOUNDARY:
                regex = rf'\b{re.escape(pattern_def.pattern)}\b'
            else:  # REGEX
                regex = pattern_def.pattern

            try:
                self._compiled_cache[cache_key] = re.compile(regex, flags)
            except re.error as e:
                logger.warning(
                    "Invalid regex pattern '%s': %s. Skipping pattern.",
                    pattern_def.pattern,
                    e
                )
                return None

        return self._compiled_cache[cache_key]


class PatternMatcher:
    """
    Main pattern matching engine.

    Analyzes text against a database of patterns and returns detailed
    match results with scoring and categorization.

    Example:
        db = PatternDatabase()
        db.add_word("delve", weight=3.0, signal_level=SignalLevel.HIGH)
        db.add_regex(r"In today's .+? world", weight=2.5, description="AI opener")

        matcher = PatternMatcher(db)
        result = matcher.analyze("Let's delve into today's digital world...")
        print(result.score, result.summary)
    """

    def __init__(
        self,
        database: PatternDatabase,
        config: PatternConfig | None = None
    ):
        """
        Initialize pattern matcher.

        Args:
            database: PatternDatabase containing patterns to match
            config: Optional configuration settings
        """
        self.database = database
        self.config = config or PatternConfig()

    def analyze(self, text: str) -> MatchResult:
        """
        Analyze text for pattern matches.

        Args:
            text: The text to analyze

        Returns:
            MatchResult with all matches, scores, and summary
        """
        matches: list[PatternMatch] = []
        total_score = 0.0

        for pattern_def in self.database:
            match_result = self._match_pattern(text, pattern_def)
            if match_result:
                matches.append(match_result)
                total_score += match_result.score

        # Apply max score cap if configured
        if self.config.max_score is not None:
            total_score = min(total_score, self.config.max_score)

        # Round score
        total_score = round(total_score, self.config.score_precision)

        # Sort matches by score (highest first)
        matches.sort(key=lambda m: m.score, reverse=True)

        # Group by category
        categories: dict[str, list[PatternMatch]] = {}
        for match in matches:
            cat = match.category or "uncategorized"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(match)

        # Generate statistics
        statistics = self._compute_statistics(matches, text)

        # Generate summary
        if self.config.summary_generator:
            summary = self.config.summary_generator(matches, total_score)
        else:
            summary = self._default_summary(matches, total_score)

        return MatchResult(
            score=total_score,
            max_score=self.config.max_score,
            matches=matches,
            summary=summary,
            categories=categories,
            statistics=statistics
        )

    def _match_pattern(
        self,
        text: str,
        pattern_def: PatternDefinition
    ) -> PatternMatch | None:
        """Match a single pattern against text."""
        compiled = self.database.get_compiled_regex(pattern_def)

        # Skip if pattern failed to compile (invalid regex)
        if compiled is None:
            return None

        matches = list(compiled.finditer(text))

        if not matches:
            return None

        count = len(matches)
        positions = [m.start() for m in matches] if self.config.include_positions else []
        matched_texts = [m.group() for m in matches]

        # Calculate score with multiplier cap
        base_score = pattern_def.weight * count
        capped_score = min(base_score, pattern_def.weight * pattern_def.max_multiplier)

        return PatternMatch(
            pattern=pattern_def.pattern,
            matched_text=matched_texts[0] if len(set(matched_texts)) == 1 else str(matched_texts),
            count=count,
            positions=positions,
            signal_level=pattern_def.signal_level,
            score=capped_score,
            description=pattern_def.description,
            category=pattern_def.category
        )

    def _compute_statistics(
        self,
        matches: list[PatternMatch],
        text: str
    ) -> MatchStatistics:
        """Compute statistics about the matches."""
        total_matches = sum(m.count for m in matches)
        word_count = len(re.findall(r'\b\w+\b', text))

        by_signal: dict[str, SignalLevelStats] = {}
        for level in SignalLevel:
            level_matches = [m for m in matches if m.signal_level == level]
            if not level_matches:
                continue
            by_signal[level.value] = {
                'count': len(level_matches),
                'total_occurrences': sum(m.count for m in level_matches),
                'total_score': round(sum(m.score for m in level_matches), 2)
            }

        return {
            'pattern_count': len(matches),
            'total_occurrences': total_matches,
            'text_word_count': word_count,
            'match_density': round(total_matches / max(word_count, 1), 4),
            'by_signal_level': by_signal
        }

    def _default_summary(
        self,
        matches: list[PatternMatch],
        score: float
    ) -> str:
        """Generate default human-readable summary."""
        if not matches:
            return "No patterns detected."

        if score < 5:
            return "Minimal pattern matches detected."

        parts = []

        # Group by signal level
        critical = [m for m in matches if m.signal_level == SignalLevel.CRITICAL]
        high = [m for m in matches if m.signal_level == SignalLevel.HIGH]
        medium = [m for m in matches if m.signal_level == SignalLevel.MEDIUM]

        if critical:
            patterns = ', '.join([f'"{m.pattern}" ({m.count}x)' for m in critical[:3]])
            parts.append(f"Critical patterns found: {patterns}")

        if high:
            patterns = ', '.join([f'"{m.pattern}" ({m.count}x)' for m in high[:5]])
            parts.append(f"High-signal patterns: {patterns}")

        if medium and not (critical or high):
            patterns = ', '.join([f'"{m.pattern}" ({m.count}x)' for m in medium[:5]])
            parts.append(f"Medium-signal patterns: {patterns}")

        if not parts:
            parts.append(f"{len(matches)} pattern(s) detected")

        return '. '.join(parts) + '.'


def create_matcher_from_wordlist(
    words: dict[str, float],
    signal_level: SignalLevel = SignalLevel.MEDIUM,
    config: PatternConfig | None = None
) -> PatternMatcher:
    """
    Convenience factory to create a matcher from a simple word->weight dictionary.

    Args:
        words: Dictionary mapping words to their weights
        signal_level: Default signal level for all words
        config: Optional configuration

    Returns:
        Configured PatternMatcher instance
    """
    db = PatternDatabase()
    for word, weight in words.items():
        db.add_word(word, weight=weight, signal_level=signal_level)
    return PatternMatcher(db, config)
