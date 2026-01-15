"""
Violation Factory - Generic Code Analysis Violation Creation

A generalized factory for creating standardized violation objects for code analysis
tools. Provides dataclasses, factory methods, and serialization utilities with zero
external dependencies (stdlib only).

Extracted and generalized from connascence analyzer for reuse across analysis tools.
"""

from dataclasses import dataclass, field
from functools import total_ordering
from typing import Any, Dict, List, Optional, Union
import json

# Import shared types from library common types for LEGO compatibility
try:
    from library.common.types import Severity
    from library.common.types import Violation as BaseViolation
except ImportError:
    try:
        from common.types import Severity
        from common.types import Violation as BaseViolation
    except ImportError:
        # Fallback for standalone usage
        from enum import Enum
        BaseViolation = None  # Will use local definition below

        @total_ordering
        class Severity(Enum):
            """
            Violation severity levels - FALLBACK (prefer library.common.types).
            """
            CRITICAL = "critical"
            HIGH = "high"
            MEDIUM = "medium"
            LOW = "low"
            INFO = "info"

            @classmethod
            def from_string(cls, value: str) -> "Severity":
                normalized = value.lower().strip()
                for member in cls:
                    if member.value == normalized:
                        return member
                valid = [m.value for m in cls]
                raise ValueError(f"Invalid severity '{value}'. Valid: {valid}")

            def __lt__(self, other: "Severity") -> bool:
                if not isinstance(other, Severity):
                    return NotImplemented
                order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
                return order.index(self) < order.index(other)


@dataclass
class Location:
    """
    Source code location with file path and position information.

    Supports both single-point locations (line/column) and ranges
    (with end_line/end_column).

    Note:
        Line and column numbers use 0-indexed convention (first line is 0).
        This aligns with most AST parsers and LSP implementations.
        Display formatters may convert to 1-indexed for user presentation.
    """
    file: str
    line: int
    column: int = 0
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate location data."""
        if not self.file:
            raise ValueError("file cannot be empty")
        if self.line < 0:
            raise ValueError("line must be non-negative (0-indexed)")
        if self.column < 0:
            raise ValueError("column must be non-negative (0-indexed)")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary, omitting None values.

        Returns:
            Dict with file, line, column, and optionally end_line/end_column
        """
        result = {
            "file": self.file,
            "line": self.line,
            "column": self.column,
        }
        if self.end_line is not None:
            result["end_line"] = self.end_line
        if self.end_column is not None:
            result["end_column"] = self.end_column
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        """
        Create Location from dictionary.

        Args:
            data: Dict with file, line, and optional column/end_line/end_column

        Returns:
            Location instance
        """
        return cls(
            file=data["file"],
            line=data["line"],
            column=data.get("column", 0),
            end_line=data.get("end_line"),
            end_column=data.get("end_column"),
        )

    def __str__(self) -> str:
        """Format as file:line:column."""
        return f"{self.file}:{self.line}:{self.column}"


# Note: This module defines an extended Violation class with Location support.
# The base Violation from library.common.types has a simpler flat structure.
# This extended version is used by ViolationFactory for richer analysis output.
# For interoperability, use to_dict()/from_dict() methods.

@dataclass
class Violation:
    """
    A code analysis violation with location, severity, and metadata.

    Extended violation dataclass for code analysis tools with Location support.
    Supports serialization to/from dict and JSON formats.

    Note: This extends the base library.common.types.Violation with:
    - Location object (instead of flat file/line fields)
    - violation_type field (instead of rule_name)
    - analyzer field for source tracking

    Attributes:
        violation_type: Category/type identifier (e.g., "unused-import", "CoP")
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW, INFO)
        location: Source code location
        description: Human-readable description of the violation
        recommendation: Optional fix suggestion
        code_snippet: Optional code excerpt showing the violation
        context: Optional additional metadata
        rule_id: Optional rule identifier for filtering
        analyzer: Optional name of the analyzer that found this
    """
    violation_type: str
    severity: Union[str, Severity]
    location: Location
    description: str
    recommendation: Optional[str] = None
    code_snippet: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    rule_id: Optional[str] = None
    analyzer: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate and normalize violation data."""
        if not self.violation_type:
            raise ValueError("violation_type cannot be empty")
        if not self.description:
            raise ValueError("description cannot be empty")
        # Convert string severity to enum if needed
        if isinstance(self.severity, str):
            self.severity = Severity.from_string(self.severity)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert violation to dictionary format.

        Returns:
            Dict with all violation fields, severity as string
        """
        result = {
            "type": self.violation_type,
            "severity": self.severity.value,
            "file_path": self.location.file,
            "line_number": self.location.line,
            "column": self.location.column,
            "description": self.description,
        }

        # Add optional location fields
        if self.location.end_line is not None:
            result["end_line"] = self.location.end_line
        if self.location.end_column is not None:
            result["end_column"] = self.location.end_column

        # Add optional fields if present
        if self.recommendation:
            result["recommendation"] = self.recommendation
        if self.code_snippet:
            result["code_snippet"] = self.code_snippet
        if self.context:
            result["context"] = self.context
        if self.rule_id:
            result["rule_id"] = self.rule_id
        if self.analyzer:
            result["analyzer"] = self.analyzer

        return result

    def to_base_violation(self) -> Any:
        """
        Convert to library.common.types.Violation for interoperability.

        Returns:
            BaseViolation instance if library is available, else dict representation

        Note:
            Some fields are mapped: violation_type -> rule_name, description -> message
        """
        if BaseViolation is not None:
            return BaseViolation(
                severity=self.severity if isinstance(self.severity, Severity) else Severity.from_string(self.severity),
                message=self.description,
                file_path=self.location.file,
                line=self.location.line,
                column=self.location.column,
                end_line=self.location.end_line,
                end_column=self.location.end_column,
                rule_id=self.rule_id,
                rule_name=self.violation_type,
                suggestion=self.recommendation,
                metadata={
                    "analyzer": self.analyzer,
                    "code_snippet": self.code_snippet,
                    **self.context,
                },
            )
        # Fallback: return dict representation
        return self.to_dict()

    @classmethod
    def from_base_violation(
        cls,
        base: Any,
        violation_type: Optional[str] = None,
        analyzer: Optional[str] = None,
    ) -> "Violation":
        """
        Create from library.common.types.Violation.

        Args:
            base: BaseViolation instance or dict
            violation_type: Override violation_type (uses rule_name from base if None)
            analyzer: Override analyzer name

        Returns:
            Violation instance
        """
        if hasattr(base, "to_dict"):
            data = base.to_dict()
        else:
            data = base

        return cls(
            violation_type=violation_type or data.get("rule_name") or data.get("rule_id") or "unknown",
            severity=data["severity"],
            location=Location(
                file=data.get("file_path") or "",
                line=data.get("line") or 0,
                column=data.get("column") or 0,
                end_line=data.get("end_line"),
                end_column=data.get("end_column"),
            ),
            description=data.get("message") or "",
            recommendation=data.get("suggestion"),
            rule_id=data.get("rule_id"),
            analyzer=analyzer or data.get("metadata", {}).get("analyzer"),
            code_snippet=data.get("metadata", {}).get("code_snippet"),
            context={k: v for k, v in data.get("metadata", {}).items() if k not in ("analyzer", "code_snippet")},
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Violation":
        """
        Create Violation from dictionary.

        Args:
            data: Dict with violation fields

        Returns:
            Violation instance
        """
        # Handle both "type" and "violation_type" keys
        violation_type = data.get("type") or data.get("violation_type")

        # Build location from flat or nested format
        if "location" in data and isinstance(data["location"], dict):
            location = Location.from_dict(data["location"])
        else:
            file_path = data.get("file_path") or data.get("file")
            if not file_path:
                raise ValueError(
                    "Missing file path: data must contain 'file_path', 'file', "
                    "or a 'location' dict with 'file' key"
                )
            location = Location(
                file=file_path,
                line=data.get("line_number") or data.get("line", 0),
                column=data.get("column", 0),
                end_line=data.get("end_line"),
                end_column=data.get("end_column"),
            )

        return cls(
            violation_type=violation_type,
            severity=data["severity"],
            location=location,
            description=data["description"],
            recommendation=data.get("recommendation"),
            code_snippet=data.get("code_snippet"),
            context=data.get("context", {}),
            rule_id=data.get("rule_id"),
            analyzer=data.get("analyzer"),
        )

    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Serialize violation to JSON string.

        Args:
            indent: Optional indentation for pretty printing

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "Violation":
        """
        Create Violation from JSON string.

        Args:
            json_str: JSON string

        Returns:
            Violation instance
        """
        return cls.from_dict(json.loads(json_str))

    def __str__(self) -> str:
        """Format as severity:type at location - description."""
        return f"[{self.severity.value.upper()}] {self.violation_type} at {self.location} - {self.description}"


class ViolationFactory:
    """
    Factory class for creating Violation objects with validation and defaults.

    Provides standardized violation creation with proper defaults, validation,
    and consistent formatting. Can be subclassed for domain-specific factories.

    Example:
        factory = ViolationFactory(analyzer="my-linter")
        violation = factory.create(
            violation_type="unused-import",
            severity="medium",
            file="app.py",
            line=10,
            description="Unused import 'os'"
        )
    """

    VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}

    def __init__(self, analyzer: Optional[str] = None):
        """
        Initialize factory with optional analyzer name.

        Args:
            analyzer: Name of the analyzer using this factory
        """
        self.analyzer = analyzer

    def _validate_inputs(
        self,
        violation_type: str,
        severity: Union[str, Severity],
        file: str,
        description: str,
    ) -> None:
        """
        Validate inputs for violation creation.

        Note: Line/column validation is delegated to Location dataclass.

        Args:
            violation_type: Type of violation
            severity: Severity level
            file: File path
            description: Description text

        Raises:
            ValueError: If any input is invalid
        """
        if not violation_type:
            raise ValueError("violation_type is required")
        if not file:
            raise ValueError("file is required")
        if not description:
            raise ValueError("description is required")

        # Validate severity
        if not isinstance(severity, str):
            return
        sev_lower = severity.lower()
        if sev_lower not in self.VALID_SEVERITIES:
            raise ValueError(f"Invalid severity: {severity}. Valid: {list(self.VALID_SEVERITIES)}")

    def create(
        self,
        violation_type: str,
        severity: Union[str, Severity],
        file: str,
        line: int,
        description: str,
        column: int = 0,
        end_line: Optional[int] = None,
        end_column: Optional[int] = None,
        recommendation: Optional[str] = None,
        code_snippet: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        rule_id: Optional[str] = None,
    ) -> Violation:
        """
        Create a standardized Violation object.

        Args:
            violation_type: Type/category of violation
            severity: Severity level (string or Severity enum)
            file: File path
            line: Line number (0-indexed)
            description: Human-readable description
            column: Column number (default: 0)
            end_line: Optional end line for ranges
            end_column: Optional end column for ranges
            recommendation: Optional fix suggestion
            code_snippet: Optional code excerpt
            context: Optional additional metadata
            rule_id: Optional rule identifier

        Returns:
            Violation instance

        Raises:
            ValueError: If any required input is invalid
        """
        self._validate_inputs(violation_type, severity, file, description)

        location = Location(
            file=file,
            line=line,
            column=column,
            end_line=end_line,
            end_column=end_column,
        )

        return Violation(
            violation_type=violation_type,
            severity=severity if isinstance(severity, Severity) else Severity.from_string(severity),
            location=location,
            description=description,
            recommendation=recommendation,
            code_snippet=code_snippet,
            context=context or {},
            rule_id=rule_id,
            analyzer=self.analyzer,
        )

    def create_from_location(
        self,
        violation_type: str,
        severity: Union[str, Severity],
        location: Union[Location, Dict[str, Any]],
        description: str,
        recommendation: Optional[str] = None,
        code_snippet: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        rule_id: Optional[str] = None,
    ) -> Violation:
        """
        Create violation from a Location object or dict.

        Args:
            violation_type: Type/category of violation
            severity: Severity level
            location: Location object or dict with file/line
            description: Human-readable description
            recommendation: Optional fix suggestion
            code_snippet: Optional code excerpt
            context: Optional additional metadata
            rule_id: Optional rule identifier

        Returns:
            Violation instance
        """
        if isinstance(location, dict):
            loc = Location.from_dict(location)
        else:
            loc = location

        return self.create(
            violation_type=violation_type,
            severity=severity,
            file=loc.file,
            line=loc.line,
            column=loc.column,
            end_line=loc.end_line,
            end_column=loc.end_column,
            description=description,
            recommendation=recommendation,
            code_snippet=code_snippet,
            context=context,
            rule_id=rule_id,
        )

    # Common factory methods for frequent patterns

    def create_unused_import(
        self,
        file: str,
        line: int,
        import_name: str,
        column: int = 0,
    ) -> Violation:
        """
        Create an unused import violation.

        Args:
            file: File path
            line: Line number
            import_name: Name of unused import
            column: Column number

        Returns:
            Violation for unused import
        """
        return self.create(
            violation_type="unused-import",
            severity="low",
            file=file,
            line=line,
            column=column,
            description=f"Unused import '{import_name}'",
            recommendation=f"Remove the unused import '{import_name}'",
            context={"import_name": import_name},
            rule_id="UNUSED-IMPORT",
        )

    def create_complexity_violation(
        self,
        file: str,
        line: int,
        function_name: str,
        complexity: int,
        threshold: int,
        column: int = 0,
    ) -> Violation:
        """
        Create a cyclomatic complexity violation.

        Args:
            file: File path
            line: Line number
            function_name: Name of function
            complexity: Measured complexity
            threshold: Maximum allowed complexity
            column: Column number

        Returns:
            Violation for high complexity
        """
        # Determine severity based on how much threshold is exceeded
        excess = complexity - threshold
        if excess >= 10:
            severity = "critical"
        elif excess >= 5:
            severity = "high"
        else:
            severity = "medium"

        return self.create(
            violation_type="high-complexity",
            severity=severity,
            file=file,
            line=line,
            column=column,
            description=f"Function '{function_name}' has complexity {complexity} (threshold: {threshold})",
            recommendation="Consider breaking this function into smaller, more focused functions",
            context={
                "function_name": function_name,
                "complexity": complexity,
                "threshold": threshold,
            },
            rule_id="COMPLEXITY",
        )

    def create_missing_type_hint(
        self,
        file: str,
        line: int,
        element_name: str,
        missing_types: str,
        column: int = 0,
    ) -> Violation:
        """
        Create a missing type hint violation.

        Args:
            file: File path
            line: Line number
            element_name: Name of element missing types
            missing_types: Description of what's missing
            column: Column number

        Returns:
            Violation for missing type hints
        """
        return self.create(
            violation_type="missing-type-hint",
            severity="medium",
            file=file,
            line=line,
            column=column,
            description=f"'{element_name}' is missing type hints: {missing_types}",
            recommendation="Add explicit type hints for better code clarity and IDE support",
            context={
                "element_name": element_name,
                "missing_types": missing_types,
            },
            rule_id="TYPE-HINT",
        )

    def create_magic_literal(
        self,
        file: str,
        line: int,
        literal_value: Any,
        literal_type: str,
        column: int = 0,
    ) -> Violation:
        """
        Create a magic literal/number violation.

        Args:
            file: File path
            line: Line number
            literal_value: The magic value
            literal_type: Type of literal (number, string, etc.)
            column: Column number

        Returns:
            Violation for magic literal
        """
        return self.create(
            violation_type="magic-literal",
            severity="medium",
            file=file,
            line=line,
            column=column,
            description=f"Magic {literal_type} literal '{literal_value}' should be a named constant",
            recommendation="Extract this literal to a module-level constant with a descriptive name",
            context={
                "literal_value": literal_value,
                "literal_type": literal_type,
            },
            rule_id="MAGIC-LITERAL",
        )

    def create_too_many_parameters(
        self,
        file: str,
        line: int,
        function_name: str,
        param_count: int,
        threshold: int = 5,
        column: int = 0,
    ) -> Violation:
        """
        Create a too-many-parameters violation.

        Args:
            file: File path
            line: Line number
            function_name: Name of function
            param_count: Number of parameters
            threshold: Maximum allowed parameters
            column: Column number

        Returns:
            Violation for too many parameters
        """
        severity = "high" if param_count > threshold + 2 else "medium"

        return self.create(
            violation_type="too-many-parameters",
            severity=severity,
            file=file,
            line=line,
            column=column,
            description=f"Function '{function_name}' has {param_count} parameters (threshold: {threshold})",
            recommendation="Consider using a parameter object, keyword arguments, or breaking the function into smaller pieces",
            context={
                "function_name": function_name,
                "param_count": param_count,
                "threshold": threshold,
            },
            rule_id="PARAM-COUNT",
        )

    def create_security_violation(
        self,
        file: str,
        line: int,
        vulnerability_type: str,
        description: str,
        recommendation: str,
        column: int = 0,
        cwe_id: Optional[str] = None,
    ) -> Violation:
        """
        Create a security vulnerability violation.

        Args:
            file: File path
            line: Line number
            vulnerability_type: Type of vulnerability (e.g., "sql-injection")
            description: Description of the vulnerability
            recommendation: How to fix it
            column: Column number
            cwe_id: Optional CWE identifier

        Returns:
            Violation for security issue
        """
        context = {"vulnerability_type": vulnerability_type}
        if cwe_id:
            context["cwe_id"] = cwe_id

        return self.create(
            violation_type=f"security-{vulnerability_type}",
            severity="critical",
            file=file,
            line=line,
            column=column,
            description=description,
            recommendation=recommendation,
            context=context,
            rule_id=cwe_id or f"SEC-{vulnerability_type.upper()}",
        )


class ViolationCollection:
    """
    Collection of violations with filtering, sorting, and aggregation utilities.

    Provides convenient methods for working with multiple violations.
    """

    def __init__(self, violations: Optional[List[Violation]] = None):
        """
        Initialize collection with optional list of violations.

        Args:
            violations: Initial list of violations
        """
        self._violations: List[Violation] = violations or []

    def add(self, violation: Violation) -> None:
        """Add a violation to the collection."""
        self._violations.append(violation)

    def extend(self, violations: List[Violation]) -> None:
        """Add multiple violations to the collection."""
        self._violations.extend(violations)

    def __len__(self) -> int:
        return len(self._violations)

    def __iter__(self):
        return iter(self._violations)

    def __getitem__(self, index: int) -> Violation:
        return self._violations[index]

    @property
    def violations(self) -> List[Violation]:
        """Get all violations."""
        return list(self._violations)

    def filter_by_severity(self, *severities: Severity) -> "ViolationCollection":
        """
        Filter violations by severity levels.

        Args:
            severities: One or more severity levels to include

        Returns:
            New ViolationCollection with filtered violations
        """
        filtered = [v for v in self._violations if v.severity in severities]
        return ViolationCollection(filtered)

    def filter_by_type(self, *types: str) -> "ViolationCollection":
        """
        Filter violations by type.

        Args:
            types: One or more violation types to include

        Returns:
            New ViolationCollection with filtered violations
        """
        filtered = [v for v in self._violations if v.violation_type in types]
        return ViolationCollection(filtered)

    def filter_by_file(self, file_pattern: str) -> "ViolationCollection":
        """
        Filter violations by file path pattern.

        Args:
            file_pattern: Substring to match in file path

        Returns:
            New ViolationCollection with filtered violations
        """
        filtered = [v for v in self._violations if file_pattern in v.location.file]
        return ViolationCollection(filtered)

    def sort_by_severity(self, descending: bool = True) -> "ViolationCollection":
        """
        Sort violations by severity.

        Args:
            descending: If True, CRITICAL first; if False, INFO first

        Returns:
            New sorted ViolationCollection
        """
        sorted_violations = sorted(
            self._violations,
            key=lambda v: v.severity,
            reverse=not descending,
        )
        return ViolationCollection(sorted_violations)

    def sort_by_location(self) -> "ViolationCollection":
        """
        Sort violations by file path, then line number.

        Returns:
            New sorted ViolationCollection
        """
        sorted_violations = sorted(
            self._violations,
            key=lambda v: (v.location.file, v.location.line),
        )
        return ViolationCollection(sorted_violations)

    def group_by_file(self) -> Dict[str, List[Violation]]:
        """
        Group violations by file path.

        Returns:
            Dict mapping file paths to lists of violations
        """
        groups: Dict[str, List[Violation]] = {}
        for v in self._violations:
            path = v.location.file
            if path not in groups:
                groups[path] = []
            groups[path].append(v)
        return groups

    def group_by_type(self) -> Dict[str, List[Violation]]:
        """
        Group violations by type.

        Returns:
            Dict mapping violation types to lists of violations
        """
        groups: Dict[str, List[Violation]] = {}
        for v in self._violations:
            vtype = v.violation_type
            if vtype not in groups:
                groups[vtype] = []
            groups[vtype].append(v)
        return groups

    def count_by_severity(self) -> Dict[str, int]:
        """
        Count violations by severity level.

        Returns:
            Dict mapping severity names to counts
        """
        counts: Dict[str, int] = {s.value: 0 for s in Severity}
        for v in self._violations:
            counts[v.severity.value] += 1
        return counts

    def has_critical(self) -> bool:
        """Check if collection has any CRITICAL violations."""
        return any(v.severity == Severity.CRITICAL for v in self._violations)

    def has_blocking(self, min_severity: Severity = Severity.HIGH) -> bool:
        """
        Check if collection has any blocking violations.

        Args:
            min_severity: Minimum severity to consider blocking

        Returns:
            True if any violation meets or exceeds min_severity
        """
        return any(v.severity <= min_severity for v in self._violations)

    def to_list(self) -> List[Dict[str, Any]]:
        """
        Convert all violations to list of dicts.

        Returns:
            List of violation dictionaries
        """
        return [v.to_dict() for v in self._violations]

    def to_json(self, indent: Optional[int] = 2) -> str:
        """
        Serialize collection to JSON string.

        Args:
            indent: Optional indentation for pretty printing

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_list(), indent=indent)

    @classmethod
    def from_list(cls, data: List[Dict[str, Any]]) -> "ViolationCollection":
        """
        Create collection from list of dicts.

        Args:
            data: List of violation dictionaries

        Returns:
            ViolationCollection instance
        """
        violations = [Violation.from_dict(d) for d in data]
        return cls(violations)

    @classmethod
    def from_json(cls, json_str: str) -> "ViolationCollection":
        """
        Create collection from JSON string.

        Args:
            json_str: JSON string

        Returns:
            ViolationCollection instance
        """
        return cls.from_list(json.loads(json_str))
