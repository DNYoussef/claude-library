"""
Library Common Types Module

This module contains all shared types used across library components.
All components MUST import shared types from here - never define locally.

Usage:
    from library.common.types import Severity, Money, Violation, ValidationResult
"""

from .types import (
    # Enums
    Severity,

    # Money handling (canonical: library.patterns.money_handling)
    Money,
    MoneyError,
    FloatNotAllowedError,
    CurrencyMismatchError,

    # Violations and Results
    Violation,
    ValidationResult,
    QualityResult,

    # Tagging Protocol
    TaggedEntry,
    WhyCategory,

    # Confidence and Contracts
    ConfidenceLevel,
    InputContract,
    OutputContract,

    # Common Protocols
    Validatable,
    Scorable,
)

__all__ = [
    # Enums
    "Severity",

    # Money (canonical: library.patterns.money_handling)
    "Money",
    "MoneyError",
    "FloatNotAllowedError",
    "CurrencyMismatchError",

    # Results
    "Violation",
    "ValidationResult",
    "QualityResult",

    # Tagging
    "TaggedEntry",
    "WhyCategory",

    # Confidence and Contracts
    "ConfidenceLevel",
    "InputContract",
    "OutputContract",

    # Protocols
    "Validatable",
    "Scorable",
]
