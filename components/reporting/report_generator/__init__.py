"""
Report Generator Component

Generic issue report generation with priority sorting and multi-format output.
Zero external dependencies - uses Python standard library only.

Exports:
    Classes:
        - Issue: Generic issue dataclass
        - Report: Complete report with issues and recommendations
        - ReportSummary: Summary statistics
        - ReportGenerator: Main generator class
        - Severity: Issue severity enum (CRITICAL, HIGH, MEDIUM, LOW, INFO)
        - OutputFormat: Output format enum (TEXT, MARKDOWN, JSON)

    Functions:
        - create_issue: Factory function to create Issue with string severity
        - generate_simple_report: One-liner convenience function

Example:
    from report_generator import ReportGenerator, Issue, Severity, OutputFormat

    generator = ReportGenerator()

    issues = [
        Issue(
            category="security",
            issue_type="sql_injection",
            severity=Severity.CRITICAL,
            description="SQL injection in user input",
            points=10.0,
            location="api/users.py:42"
        ),
    ]

    report = generator.generate("Security Audit", issues, score=65.0)
    print(generator.format(report, OutputFormat.MARKDOWN))
"""

from .report_generator import (
    # Enums
    Severity,
    OutputFormat,
    # Dataclasses
    Issue,
    Report,
    ReportSummary,
    # Main class
    ReportGenerator,
    # Factory functions
    create_issue,
    generate_simple_report,
)

__all__ = [
    # Enums
    "Severity",
    "OutputFormat",
    # Dataclasses
    "Issue",
    "Report",
    "ReportSummary",
    # Main class
    "ReportGenerator",
    # Factory functions
    "create_issue",
    "generate_simple_report",
]

__version__ = "1.0.0"
