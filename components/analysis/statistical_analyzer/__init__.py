"""
Statistical Analyzer Component

A standalone text analysis module for calculating statistical metrics
including entropy, burstiness, lexical diversity, and structural patterns.

Zero external dependencies - uses only Python stdlib (re, math, collections).

Usage:
    from statistical_analyzer import StatisticalAnalyzer, StatisticalMetrics

    analyzer = StatisticalAnalyzer()
    result = analyzer.analyze("Your text here...")

    print(f"Score: {result.score}/{result.max_score}")
    print(f"Entropy: {result.entropy.value}")
    print(f"Burstiness CV: {result.burstiness.value}")
    print(f"TTR: {result.lexical_diversity.value}")
"""

from .statistical_analyzer import (
    # Main analyzer class
    StatisticalAnalyzer,

    # Result dataclasses
    StatisticalMetrics,
    EntropyMetrics,
    BurstinessMetrics,
    LexicalDiversityMetrics,
    HapaxMetrics,
    SentenceStartMetrics,

    # Standalone utility functions
    calculate_shannon_entropy,
    calculate_coefficient_of_variation,
    calculate_type_token_ratio,
    calculate_hapax_ratio,
)

__all__ = [
    # Main class
    'StatisticalAnalyzer',

    # Dataclasses for typed results
    'StatisticalMetrics',
    'EntropyMetrics',
    'BurstinessMetrics',
    'LexicalDiversityMetrics',
    'HapaxMetrics',
    'SentenceStartMetrics',

    # Utility functions
    'calculate_shannon_entropy',
    'calculate_coefficient_of_variation',
    'calculate_type_token_ratio',
    'calculate_hapax_ratio',
]

__version__ = '1.0.0'
__author__ = 'David Youssef'
__source__ = 'Extracted from slop-detector project'
