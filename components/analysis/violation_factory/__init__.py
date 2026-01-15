"""
Violation Factory - Generic Code Analysis Violation Creation

A generalized factory for creating standardized violation objects for code analysis
tools. Zero external dependencies (stdlib only).

Classes:
    Severity: Enum for violation severity levels (CRITICAL, HIGH, MEDIUM, LOW, INFO)
    Location: Dataclass for source code location (file, line, column, ranges)
    Violation: Dataclass for a single code analysis violation
    ViolationFactory: Factory class for creating violations with validation
    ViolationCollection: Collection class with filtering, sorting, aggregation

Example Usage:
    from violation_factory import ViolationFactory, Severity, ViolationCollection

    # Create a factory for your analyzer
    factory = ViolationFactory(analyzer="my-linter")

    # Create violations
    v1 = factory.create(
        violation_type="unused-import",
        severity="medium",
        file="app.py",
        line=10,
        description="Unused import 'os'"
    )

    # Or use convenience methods
    v2 = factory.create_unused_import("app.py", 5, "sys")
    v3 = factory.create_complexity_violation("service.py", 20, "process_data", 15, 10)

    # Work with collections
    collection = ViolationCollection([v1, v2, v3])
    critical_only = collection.filter_by_severity(Severity.CRITICAL, Severity.HIGH)
    by_file = collection.group_by_file()

    # Serialize
    json_output = collection.to_json()
"""

from .violation_factory import (
    # Enums
    Severity,
    # Dataclasses
    Location,
    Violation,
    # Factory
    ViolationFactory,
    # Collection
    ViolationCollection,
)

__all__ = [
    "Severity",
    "Location",
    "Violation",
    "ViolationFactory",
    "ViolationCollection",
]

__version__ = "1.0.0"
