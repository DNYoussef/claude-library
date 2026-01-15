"""
Shared Types for Library Components

This module defines all common types used across library components.
Components MUST import from here - never define their own versions.

LEGO Principle: Components interface through these shared types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from functools import total_ordering
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


# =============================================================================
# SEVERITY ENUM
# =============================================================================
# Used by: analysis, validation, reporting, quality-gates
# =============================================================================

@total_ordering
class Severity(Enum):
    """
    Violation severity levels from most to least severe.

    Supports comparison operators for sorting:
        Severity.CRITICAL > Severity.HIGH  # True

    String values for JSON serialization:
        Severity.CRITICAL.value  # "critical"
    """

    CRITICAL = "critical"  # P0 - Must fix immediately, blocks release
    HIGH = "high"          # P1 - Fix before release
    MEDIUM = "medium"      # P2 - Fix soon, technical debt
    LOW = "low"            # P3 - Nice to have, minor improvement
    INFO = "info"          # Informational only, not a problem

    @property
    def weight(self) -> int:
        """Numeric weight for sorting (higher = more severe)."""
        weights = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        return weights[self.value]

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.weight < other.weight

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Create Severity from string, case-insensitive."""
        normalized = value.lower().strip()
        for severity in cls:
            if severity.value == normalized:
                return severity
        raise ValueError(f"Unknown severity: {value}. Valid: {[s.value for s in cls]}")


# =============================================================================
# MONEY HANDLING
# =============================================================================
# Used by: trading, banking, accounting
# CRITICAL: Rejects float to prevent precision errors
#
# CANONICAL SOURCE: library.patterns.money_handling
# This module re-exports for LEGO compatibility.
# =============================================================================

_money_imported = False

# Try multiple import paths for the canonical Money implementation
try:
    # Path 1: Full library path (when library is installed as package)
    from library.patterns.money_handling.money import (
        Money, MoneyError, FloatNotAllowedError, CurrencyMismatchError,
    )
    _money_imported = True
except ImportError:
    pass

if not _money_imported:
    try:
        # Path 2: Relative from library root (when running from library/)
        from patterns.money_handling.money import (
            Money, MoneyError, FloatNotAllowedError, CurrencyMismatchError,
        )
        _money_imported = True
    except ImportError:
        pass

if not _money_imported:
    # Fallback for standalone usage (copy-paste scenarios)
    class FloatNotAllowedError(TypeError):
        """Raised when float is used instead of Decimal for money."""
        def __init__(self, message: str = "Use Decimal for money, not float"):
            super().__init__(message)

    class MoneyError(Exception):
        """Base exception for money-related errors."""
        pass

    class CurrencyMismatchError(MoneyError):
        """Raised when operating on money with different currencies."""
        pass

    @dataclass(frozen=True)
    class Money:
        """
        Immutable money representation using Decimal.

        CRITICAL: Rejects float values to prevent precision errors.

        For full features (from_string, from_cents, banker's rounding),
        use: from library.patterns.money_handling import Money
        """
        amount: Decimal
        currency: str = "USD"

        def __post_init__(self) -> None:
            if isinstance(self.amount, float):
                raise FloatNotAllowedError(
                    f"Money amount must be Decimal, got float: {self.amount}. "
                    f"Use Decimal('{self.amount}') instead."
                )
            if not isinstance(self.currency, str) or len(self.currency) != 3:
                raise ValueError(f"Currency must be 3-letter ISO code, got: {self.currency}")

        def __add__(self, other: "Money") -> "Money":
            if not isinstance(other, Money):
                return NotImplemented
            if self.currency != other.currency:
                raise CurrencyMismatchError(f"Cannot add {self.currency} and {other.currency}")
            return Money(self.amount + other.amount, self.currency)

        def __sub__(self, other: "Money") -> "Money":
            if not isinstance(other, Money):
                return NotImplemented
            if self.currency != other.currency:
                raise CurrencyMismatchError(f"Cannot subtract {self.currency} and {other.currency}")
            return Money(self.amount - other.amount, self.currency)

        def __mul__(self, multiplier: Decimal) -> "Money":
            if isinstance(multiplier, float):
                raise FloatNotAllowedError("Multiply by Decimal, not float")
            return Money(self.amount * multiplier, self.currency)

        def __neg__(self) -> "Money":
            return Money(-self.amount, self.currency)

        def __abs__(self) -> "Money":
            return Money(abs(self.amount), self.currency)

        def __str__(self) -> str:
            return f"{self.currency} {self.amount:,.2f}"

        def __repr__(self) -> str:
            return f"Money({self.amount!r}, {self.currency!r})"

        def to_dict(self) -> Dict[str, Any]:
            return {"amount": str(self.amount), "currency": self.currency}

        @classmethod
        def from_dict(cls, data: Dict[str, Any]) -> "Money":
            return cls(Decimal(str(data["amount"])), data.get("currency", "USD"))

        @classmethod
        def zero(cls, currency: str = "USD") -> "Money":
            return cls(Decimal("0"), currency)


# =============================================================================
# VIOLATION AND RESULTS
# =============================================================================
# Used by: analysis, validation, quality-gates, reporting
# =============================================================================

@dataclass
class Violation:
    """
    A code quality violation or issue.

    Compatible with SARIF output format.
    """

    severity: Severity
    message: str
    file_path: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Accept string severity and convert
        if isinstance(self.severity, str):
            object.__setattr__(self, "severity", Severity.from_string(self.severity))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSON/SARIF."""
        return {
            "severity": self.severity.value,
            "message": self.message,
            "file_path": self.file_path,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "suggestion": self.suggestion,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Violation":
        """Deserialize from dict."""
        return cls(
            severity=Severity.from_string(data["severity"]),
            message=data["message"],
            file_path=data.get("file_path"),
            line=data.get("line"),
            column=data.get("column"),
            end_line=data.get("end_line"),
            end_column=data.get("end_column"),
            rule_id=data.get("rule_id"),
            rule_name=data.get("rule_name"),
            suggestion=data.get("suggestion"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.valid

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge two validation results."""
        return ValidationResult(
            valid=self.valid and other.valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            metadata={**self.metadata, **other.metadata},
        )


@dataclass
class QualityResult:
    """Result of a quality check with violations."""

    passed: bool
    score: float
    violations: List[Violation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.passed

    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == Severity.LOW)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "violations": [v.to_dict() for v in self.violations],
            "counts": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
            },
            "metadata": self.metadata,
        }


# =============================================================================
# TAGGING PROTOCOL
# =============================================================================
# Used by: memory, observability, audit-logging
# =============================================================================

class WhyCategory(Enum):
    """Standard categories for the WHY field in tagging."""

    IMPLEMENTATION = "implementation"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    RESEARCH = "research"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


@dataclass
class TaggedEntry:
    """
    Standard tagged entry for Memory MCP writes.

    Enforces WHO/WHEN/PROJECT/WHY metadata on all memory operations.
    """

    who: str                                # Agent identifier (e.g., "coder:1.0")
    project: str                            # Project name
    why: str                                # Reason (from WhyCategory or custom)
    content: Any                            # The actual data
    when: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        # Validate WHO format (should be agent:version or similar)
        if not self.who or ":" not in self.who:
            # Allow but warn
            pass
        # Validate PROJECT
        if not self.project:
            raise ValueError("project is required")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for storage."""
        return {
            "WHO": self.who,
            "WHEN": self.when.isoformat(),
            "PROJECT": self.project,
            "WHY": self.why,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaggedEntry":
        """Deserialize from dict."""
        when = data.get("WHEN") or data.get("when")
        if isinstance(when, str):
            when = datetime.fromisoformat(when.replace("Z", "+00:00"))
        elif when is None:
            when = datetime.now(timezone.utc)

        return cls(
            who=data.get("WHO") or data.get("who", "unknown:0.0"),
            project=data.get("PROJECT") or data.get("project", "unknown"),
            why=data.get("WHY") or data.get("why", "unknown"),
            content=data.get("content"),
            when=when,
        )


# =============================================================================
# CONFIDENCE AND CONTRACTS
# =============================================================================
# Used by: skill_base, agent_base, playbook_base
# =============================================================================

class ConfidenceLevel(Enum):
    """
    Confidence thresholds for uncertainty handling.

    Determines action based on confidence in understanding:
        HIGH (0.8+): Proceed with execution, document assumptions
        MEDIUM (0.5-0.8): Present options, ask user to confirm
        LOW (<0.5): Do NOT proceed, ask clarifying questions
    """
    HIGH = 0.8       # Proceed with execution, document assumptions
    MEDIUM = 0.5     # Present options, ask user to confirm
    LOW = 0.0        # Do NOT proceed, ask clarifying questions


@dataclass
class InputContract:
    """
    Input contract specification for skills and agents.

    Validates that required inputs are present and of correct type.
    """
    required: Dict[str, type] = field(default_factory=dict)
    optional: Dict[str, type] = field(default_factory=dict)

    def validate(self, inputs: Dict[str, Any]) -> tuple:
        """Validate inputs against contract. Returns (valid, errors)."""
        errors = []
        for name, expected_type in self.required.items():
            if name not in inputs:
                errors.append(f"Missing required input: {name}")
            elif not isinstance(inputs.get(name), expected_type):
                errors.append(f"Invalid type for {name}: expected {expected_type.__name__}")
        return len(errors) == 0, errors


@dataclass
class OutputContract:
    """
    Output contract specification for skills and agents.

    Specifies expected output structure.
    """
    required: Dict[str, type] = field(default_factory=dict)
    optional: Dict[str, type] = field(default_factory=dict)


# =============================================================================
# PROTOCOLS (Structural Typing)
# =============================================================================
# Components can implement these for duck-typed compatibility
# =============================================================================

@runtime_checkable
class Validatable(Protocol):
    """Protocol for objects that can be validated."""

    def validate(self) -> ValidationResult:
        """Validate this object and return result."""
        ...


@runtime_checkable
class Scorable(Protocol):
    """Protocol for objects that produce a score."""

    def score(self) -> float:
        """Calculate and return a score (0.0 to 1.0)."""
        ...
