"""
Pattern Matcher - Generic text pattern detection engine.

A reusable component for detecting patterns in text using both literal
string matching and regex patterns. Originally extracted from Slop Detector.

Example usage:
    from pattern_matcher import (
        PatternMatcher,
        PatternDatabase,
        PatternConfig,
        SignalLevel
    )

    # Create pattern database
    db = PatternDatabase()
    db.add_word("delve", weight=3.0, signal_level=SignalLevel.HIGH)
    db.add_word("leverage", weight=2.0, signal_level=SignalLevel.HIGH)
    db.add_regex(r"In today's .+? world", weight=2.5, description="AI opener")

    # Create matcher with configuration
    config = PatternConfig(max_score=25.0)
    matcher = PatternMatcher(db, config)

    # Analyze text
    result = matcher.analyze("Let's delve into today's digital world...")
    print(f"Score: {result.score}")
    print(f"Summary: {result.summary}")

    # Access individual matches
    for match in result.matches:
        print(f"  {match.pattern}: {match.count}x (score: {match.score})")
"""

from .pattern_matcher import (
    # Core classes
    PatternMatcher,
    PatternDatabase,
    PatternConfig,

    # Data classes
    PatternDefinition,
    PatternMatch,
    MatchResult,

    # Enums
    SignalLevel,
    PatternType,

    # Factory functions
    create_matcher_from_wordlist,
)

__all__ = [
    # Core classes
    "PatternMatcher",
    "PatternDatabase",
    "PatternConfig",

    # Data classes
    "PatternDefinition",
    "PatternMatch",
    "MatchResult",

    # Enums
    "SignalLevel",
    "PatternType",

    # Factory functions
    "create_matcher_from_wordlist",
]

__version__ = "1.0.0"
__author__ = "Extracted from Slop Detector"
__source__ = "D:\\Projects\\slop-detector\\backend\\analyzers\\lexical.py"
