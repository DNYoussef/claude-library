# Violation Factory

Generic code analysis violation creation library. Zero external dependencies (stdlib only).

## Overview

Extracted and generalized from the Connascence Analyzer's violation factory. Provides standardized violation objects for any code analysis tool with:

- **Severity levels**: CRITICAL, HIGH, MEDIUM, LOW, INFO
- **Location tracking**: File, line, column with optional ranges
- **Serialization**: to_dict(), from_dict(), to_json(), from_json()
- **Factory methods**: Common patterns (unused imports, complexity, etc.)
- **Collections**: Filtering, sorting, grouping utilities

## Installation

Copy this directory to your project or add to PYTHONPATH:

```bash
cp -r violation-factory/ your-project/lib/
```

## Quick Start

```python
from violation_factory import ViolationFactory, Severity, ViolationCollection

# Create a factory for your analyzer
factory = ViolationFactory(analyzer="my-linter")

# Create a violation
violation = factory.create(
    violation_type="unused-variable",
    severity="medium",
    file="src/app.py",
    line=42,
    column=8,
    description="Variable 'temp' is assigned but never used",
    recommendation="Remove the unused variable or use it"
)

# Access properties
print(violation.location)  # src/app.py:42:8
print(violation.severity)  # Severity.MEDIUM
print(violation)           # [MEDIUM] unused-variable at src/app.py:42:8 - Variable...

# Serialize
data = violation.to_dict()
json_str = violation.to_json(indent=2)
```

## Classes

### Severity

Enum for violation severity levels:

```python
from violation_factory import Severity

# Severity levels (ordered from most to least severe)
Severity.CRITICAL  # Production-breaking issues
Severity.HIGH      # Significant problems
Severity.MEDIUM    # Code quality issues
Severity.LOW       # Minor improvements
Severity.INFO      # Informational notices

# Parse from string
sev = Severity.from_string("high")  # Severity.HIGH

# Comparison (for sorting)
Severity.CRITICAL < Severity.HIGH  # True (CRITICAL is more severe)
```

### Location

Source code location with optional ranges:

```python
from violation_factory import Location

# Basic location
loc = Location(file="app.py", line=10, column=5)
print(loc)  # app.py:10:5

# With range (for multi-line violations)
loc = Location(
    file="app.py",
    line=10,
    column=5,
    end_line=15,
    end_column=10
)

# Serialize
data = loc.to_dict()
loc2 = Location.from_dict(data)
```

### Violation

Core violation dataclass:

```python
from violation_factory import Violation, Severity, Location

# Direct creation
violation = Violation(
    violation_type="unused-import",
    severity=Severity.MEDIUM,
    location=Location(file="app.py", line=1, column=0),
    description="Unused import 'os'",
    recommendation="Remove the import",
    context={"import_name": "os"},
    rule_id="UNUSED-IMPORT",
    analyzer="my-linter"
)

# Serialize/deserialize
data = violation.to_dict()
json_str = violation.to_json()
restored = Violation.from_dict(data)
restored = Violation.from_json(json_str)
```

### ViolationFactory

Factory with validation and convenience methods:

```python
from violation_factory import ViolationFactory

factory = ViolationFactory(analyzer="my-analyzer")

# Generic creation
v = factory.create(
    violation_type="custom-issue",
    severity="high",
    file="src/main.py",
    line=100,
    description="Something is wrong"
)

# From location dict (compatible with AST node locations)
v = factory.create_from_location(
    violation_type="issue",
    severity="medium",
    location={"file": "app.py", "line": 10, "column": 5},
    description="Issue found"
)

# Convenience methods
v = factory.create_unused_import("app.py", 1, "os")
v = factory.create_complexity_violation("service.py", 20, "process", 15, 10)
v = factory.create_missing_type_hint("utils.py", 5, "calculate", "return type")
v = factory.create_magic_literal("config.py", 10, 3600, "number")
v = factory.create_too_many_parameters("api.py", 30, "create_user", 8, 5)
v = factory.create_security_violation(
    "auth.py", 50, "sql-injection",
    "User input directly in SQL query",
    "Use parameterized queries",
    cwe_id="CWE-89"
)
```

### ViolationCollection

Collection utilities for working with multiple violations:

```python
from violation_factory import ViolationCollection, Severity

# Create collection
collection = ViolationCollection(violations_list)

# Or build incrementally
collection = ViolationCollection()
collection.add(violation1)
collection.extend([violation2, violation3])

# Filter
critical = collection.filter_by_severity(Severity.CRITICAL)
high_critical = collection.filter_by_severity(Severity.CRITICAL, Severity.HIGH)
imports = collection.filter_by_type("unused-import")
src_only = collection.filter_by_file("src/")

# Sort
by_severity = collection.sort_by_severity()  # CRITICAL first
by_location = collection.sort_by_location()  # By file, then line

# Group
by_file = collection.group_by_file()    # {"app.py": [...], "utils.py": [...]}
by_type = collection.group_by_type()    # {"unused-import": [...], ...}

# Aggregate
counts = collection.count_by_severity()  # {"critical": 2, "high": 5, ...}
has_blockers = collection.has_blocking(min_severity=Severity.HIGH)

# Serialize
json_output = collection.to_json(indent=2)
dict_list = collection.to_list()

# Deserialize
restored = ViolationCollection.from_json(json_output)
restored = ViolationCollection.from_list(dict_list)
```

## Integration Examples

### With AST Analysis

```python
import ast
from violation_factory import ViolationFactory

factory = ViolationFactory(analyzer="ast-checker")

class UnusedImportChecker(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.violations = []

    def visit_Import(self, node):
        for alias in node.names:
            # Check if import is used...
            if not self._is_used(alias.name):
                self.violations.append(
                    factory.create_unused_import(
                        self.filename,
                        node.lineno,
                        alias.name,
                        node.col_offset
                    )
                )
        self.generic_visit(node)
```

### Quality Gate

```python
from violation_factory import ViolationCollection, Severity

def quality_gate(violations: ViolationCollection) -> bool:
    """Return True if quality gate passes."""
    counts = violations.count_by_severity()

    # Fail on any critical
    if counts["critical"] > 0:
        return False

    # Fail on more than 5 high
    if counts["high"] > 5:
        return False

    return True
```

### SARIF Output

```python
def to_sarif(violations: ViolationCollection) -> dict:
    """Convert violations to SARIF format."""
    severity_map = {
        "critical": "error",
        "high": "error",
        "medium": "warning",
        "low": "note",
        "info": "note"
    }

    results = []
    for v in violations:
        results.append({
            "ruleId": v.rule_id or v.violation_type,
            "level": severity_map[v.severity.value],
            "message": {"text": v.description},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": v.location.file},
                    "region": {
                        "startLine": v.location.line,
                        "startColumn": v.location.column
                    }
                }
            }]
        })

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"results": results}]
    }
```

## Origin

Extracted from: `D:\Projects\connascence\analyzer\utils\violation_factory.py`

The original was tightly coupled to the Connascence Analyzer's domain. This version:
- Removes the `ProductionAssert` dependency
- Generalizes violation types beyond connascence-specific ones
- Adds the `ViolationCollection` class for batch operations
- Adds JSON serialization support
- Adds common factory methods for frequent patterns
- Makes severity an enum instead of plain strings

## API Reference

### Exported Classes

| Class | Purpose |
|-------|---------|
| `Severity` | Enum: CRITICAL, HIGH, MEDIUM, LOW, INFO |
| `Location` | Source code location (file, line, column, ranges) |
| `Violation` | Single violation with all metadata |
| `ViolationFactory` | Factory with validation and convenience methods |
| `ViolationCollection` | Collection with filtering/sorting/grouping |

### Severity Levels

| Level | Use Case |
|-------|----------|
| CRITICAL | Production-breaking, security vulnerabilities |
| HIGH | Significant bugs, performance issues |
| MEDIUM | Code quality, maintainability |
| LOW | Style, minor improvements |
| INFO | Informational, suggestions |

### Factory Methods

| Method | Creates |
|--------|---------|
| `create()` | Generic violation |
| `create_from_location()` | From Location object/dict |
| `create_unused_import()` | Unused import violation |
| `create_complexity_violation()` | Cyclomatic complexity |
| `create_missing_type_hint()` | Missing type annotations |
| `create_magic_literal()` | Magic numbers/strings |
| `create_too_many_parameters()` | Parameter count |
| `create_security_violation()` | Security issues |

## Version

1.0.0
