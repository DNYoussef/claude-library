# Report Generator

Generic issue report generation with priority sorting and multi-format output.

## Overview

A reusable component for generating structured reports from analysis results. Originally extracted from the Slop Detector project and generalized for any domain.

**Source:** `D:\Projects\slop-detector\backend\report_generator.py`

## Features

- Generic `Issue` dataclass supporting any analysis domain
- Priority-based sorting (by severity and points)
- Multiple output formats: TEXT, MARKDOWN, JSON
- Automatic quick-fix recommendation generation
- Extensible quick-fix generators per category
- Summary statistics (by severity, by category)
- Zero external dependencies (stdlib only)

## Installation

Copy the component to your project or import directly:

```python
import sys
sys.path.insert(0, r"C:\Users\17175\.claude\library\components\reporting\report-generator")

from report_generator import ReportGenerator, Issue, Severity, OutputFormat
```

## Quick Start

### Simple Usage

```python
from report_generator import generate_simple_report

report = generate_simple_report(
    title="Code Analysis",
    issues=[
        {
            "category": "security",
            "type": "sql_injection",
            "severity": "CRITICAL",
            "description": "SQL injection vulnerability",
            "points": 10.0
        },
        {
            "category": "style",
            "type": "long_method",
            "severity": "LOW",
            "description": "Method exceeds 50 lines",
            "points": 2.0
        }
    ],
    score=75.0,
    output_format="markdown"
)

print(report)
```

### Full Control

```python
from report_generator import ReportGenerator, Issue, Severity, OutputFormat

# Create generator with custom limits
generator = ReportGenerator(
    max_priority_issues=10,
    max_secondary_issues=10,
    max_minor_issues=5,
    max_recommendations=5
)

# Create issues
issues = [
    Issue(
        category="security",
        issue_type="sql_injection",
        severity=Severity.CRITICAL,
        description="SQL injection in user input handling",
        points=10.0,
        location="api/users.py:42",
        details={"input_source": "request.args"},
        quick_fix="Use parameterized queries instead of string concatenation"
    ),
    Issue(
        category="performance",
        issue_type="n_plus_one",
        severity=Severity.HIGH,
        description="N+1 query pattern detected",
        points=8.0,
        location="models/orders.py:156"
    ),
    Issue(
        category="style",
        issue_type="complexity",
        severity=Severity.MEDIUM,
        description="Cyclomatic complexity exceeds threshold",
        points=4.0,
        location="utils/parser.py:89"
    ),
]

# Generate report
report = generator.generate(
    title="Security Audit Report",
    issues=issues,
    score=65.0,
    grade="D",
    confidence=0.95,
    metadata={"analyzer_version": "2.1.0", "files_scanned": 142}
)

# Output in different formats
print(generator.format(report, OutputFormat.TEXT))
print(generator.format(report, OutputFormat.MARKDOWN))
print(generator.format(report, OutputFormat.JSON))
```

## API Reference

### Classes

#### `Severity` (Enum)

Issue severity levels with numeric weights:

| Level | Value | Description |
|-------|-------|-------------|
| CRITICAL | 4 | Must fix immediately |
| HIGH | 3 | Should fix soon |
| MEDIUM | 2 | Should address |
| LOW | 1 | Consider fixing |
| INFO | 0 | Informational only |

#### `OutputFormat` (Enum)

- `TEXT` - Plain text report
- `MARKDOWN` - Markdown formatted
- `JSON` - JSON structured data

#### `Issue` (Dataclass)

```python
@dataclass
class Issue:
    category: str              # Domain (security, style, etc.)
    issue_type: str            # Specific type within category
    severity: Severity         # Severity level
    description: str           # Human-readable description
    points: float = 0.0        # Numeric weight for prioritization
    location: Optional[str]    # File path, line number, etc.
    details: Dict[str, Any]    # Additional structured data
    quick_fix: Optional[str]   # Suggested fix
```

#### `ReportSummary` (Dataclass)

```python
@dataclass
class ReportSummary:
    total_issues: int
    by_severity: Dict[str, int]
    by_category: Dict[str, int]
    score: Optional[float]
    grade: Optional[str]
    confidence: Optional[float]
```

#### `Report` (Dataclass)

```python
@dataclass
class Report:
    title: str
    summary: ReportSummary
    issues: List[Issue]
    recommendations: List[str]
    metadata: Dict[str, Any]
    generated_at: str
```

#### `ReportGenerator` (Class)

Main generator class with methods:

- `generate(title, issues, score, grade, confidence, metadata)` -> `Report`
- `format(report, output_format)` -> `str`
- `register_quick_fix_generator(category, generator)` -> `None`

### Factory Functions

#### `create_issue(...)`

Create an Issue with string severity (convenience function):

```python
issue = create_issue(
    category="security",
    issue_type="xss",
    severity="HIGH",  # String instead of Severity.HIGH
    description="XSS vulnerability",
    points=8.0
)
```

#### `generate_simple_report(...)`

One-liner for simple reports:

```python
report_str = generate_simple_report(
    title="Analysis",
    issues=[{"category": "x", "type": "y", "severity": "HIGH", "description": "z"}],
    score=80.0,
    output_format="markdown"
)
```

## Custom Quick-Fix Generators

Register domain-specific quick-fix generators:

```python
def security_fix_generator(issue: Issue) -> Optional[str]:
    fixes = {
        "sql_injection": "Use parameterized queries",
        "xss": "Sanitize user input before rendering",
        "csrf": "Add CSRF token validation",
    }
    return fixes.get(issue.issue_type)

generator = ReportGenerator()
generator.register_quick_fix_generator("security", security_fix_generator)
```

## Output Examples

### Text Format

```
======================================================================
                        Security Audit Report
======================================================================
Generated: 2025-01-10T14:30:00

----------------------------------------------------------------------
SUMMARY
----------------------------------------------------------------------
Total Issues: 15
Score: 65.0
Grade: D
Confidence: 95.0%

By Severity:
  CRITICAL: 2
  HIGH: 5
  MEDIUM: 6
  LOW: 2

----------------------------------------------------------------------
QUICK FIXES
----------------------------------------------------------------------
1. Use parameterized queries instead of string concatenation
2. Add input validation for user-supplied data
...
```

### Markdown Format

```markdown
# Security Audit Report

*Generated: 2025-01-10T14:30:00*

## Summary

- **Total Issues:** 15
- **Score:** 65.0
- **Grade:** D
- **Confidence:** 95.0%

### Issues by Severity

- !!! **CRITICAL:** 2
- !! **HIGH:** 5
- ! **MEDIUM:** 6
- - **LOW:** 2

## Quick Fixes

1. Use parameterized queries instead of string concatenation
2. Add input validation for user-supplied data
...

## Issues

### CRITICAL Priority

- **[security]** SQL injection in user input handling at `api/users.py:42`
  - *Fix: Use parameterized queries*
...
```

## Integration Example

Integrating with an existing analyzer:

```python
from report_generator import ReportGenerator, create_issue, OutputFormat

class MyAnalyzer:
    def analyze(self, code: str) -> dict:
        # Your analysis logic
        return {"issues": [...], "score": 85.0}

    def generate_report(self, analysis: dict) -> str:
        generator = ReportGenerator()

        issues = [
            create_issue(
                category=i["category"],
                issue_type=i["type"],
                severity=i["severity"],
                description=i["message"],
                points=i.get("weight", 1.0),
                location=f"{i['file']}:{i['line']}"
            )
            for i in analysis["issues"]
        ]

        report = generator.generate(
            title="My Analysis Report",
            issues=issues,
            score=analysis["score"]
        )

        return generator.format(report, OutputFormat.MARKDOWN)
```

## Version History

- **1.0.0** - Initial extraction from slop-detector, generalized for reuse
