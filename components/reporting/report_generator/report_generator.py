"""
Report Generator - Generic issue report generation with priority sorting and multi-format output.

A reusable component for generating structured reports from analysis results.
Supports text, markdown, and JSON output formats with priority-based sorting.

Source: Extracted and generalized from slop-detector/backend/report_generator.py
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import json

# Import shared Severity from library common types for LEGO compatibility
try:
    from library.common.types import Severity
except ImportError:
    try:
        from common.types import Severity
    except ImportError:
        # Fallback for standalone use
        from enum import Enum

        class Severity(Enum):
            """Issue severity levels - FALLBACK (prefer library.common.types)."""
            CRITICAL = "critical"
            HIGH = "high"
            MEDIUM = "medium"
            LOW = "low"
            INFO = "info"

            @property
            def weight(self) -> int:
                weights = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
                return weights[self.value]

            def __lt__(self, other: "Severity") -> bool:
                return self.weight < other.weight

            def __gt__(self, other: "Severity") -> bool:
                return self.weight > other.weight


class OutputFormat(Enum):
    """Supported output formats."""
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"


@dataclass
class Issue:
    """
    Generic issue representation for any analysis domain.

    Attributes:
        category: The domain/category of the issue (e.g., "security", "style", "performance")
        issue_type: Specific type within the category (e.g., "sql_injection", "long_method")
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW, INFO)
        description: Human-readable description of the issue
        points: Numeric score/weight for prioritization (higher = more important)
        location: Optional location info (file path, line number, etc.)
        details: Additional structured details about the issue
        quick_fix: Optional suggested fix for this specific issue
    """
    category: str
    issue_type: str
    severity: Severity
    description: str
    points: float = 0.0
    location: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    quick_fix: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "category": self.category,
            "type": self.issue_type,
            "severity": self.severity.name,
            "description": self.description,
            "points": self.points,
        }
        if not (self.location or self.details or self.quick_fix):
            return result
        if self.location:
            result["location"] = self.location
        if self.details:
            result["details"] = self.details
        if self.quick_fix:
            result["quick_fix"] = self.quick_fix
        return result


@dataclass
class ReportSummary:
    """
    Summary statistics for a report.

    Attributes:
        total_issues: Total number of issues found
        by_severity: Count of issues per severity level
        by_category: Count of issues per category
        score: Optional overall score (0-100, domain-specific)
        grade: Optional letter grade (A-F)
        confidence: Optional confidence level (0.0-1.0)
    """
    total_issues: int = 0
    by_severity: Dict[str, int] = field(default_factory=dict)
    by_category: Dict[str, int] = field(default_factory=dict)
    score: Optional[float] = None
    grade: Optional[str] = None
    confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "total_issues": self.total_issues,
            "by_severity": self.by_severity,
            "by_category": self.by_category,
        }
        if self.score is not None:
            result["score"] = self.score
        if self.grade is not None:
            result["grade"] = self.grade
        if self.confidence is not None:
            result["confidence"] = self.confidence
        return result


@dataclass
class Report:
    """
    Complete analysis report with prioritized issues and recommendations.

    Attributes:
        title: Report title
        summary: Summary statistics
        issues: All issues (will be sorted by priority)
        recommendations: List of actionable recommendations
        metadata: Additional report metadata
        generated_at: Timestamp of report generation
    """
    title: str
    summary: ReportSummary
    issues: List[Issue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "summary": self.summary.to_dict(),
            "issues": [issue.to_dict() for issue in self.issues],
            "recommendations": self.recommendations,
            "metadata": self.metadata,
            "generated_at": self.generated_at,
        }


class ReportGenerator:
    """
    Generates formatted reports from analysis issues.

    Supports multiple output formats (text, markdown, JSON) and
    priority-based sorting of issues.

    Example:
        generator = ReportGenerator()

        # Add issues from your analysis
        issues = [
            Issue(
                category="security",
                issue_type="sql_injection",
                severity=Severity.CRITICAL,
                description="SQL injection vulnerability in user input",
                points=10.0,
                location="api/users.py:42",
                quick_fix="Use parameterized queries"
            ),
            Issue(
                category="style",
                issue_type="long_method",
                severity=Severity.LOW,
                description="Method exceeds 50 lines",
                points=2.0,
                location="utils/helpers.py:100"
            ),
        ]

        # Generate report
        report = generator.generate(
            title="Code Analysis Report",
            issues=issues,
            score=75.0,
            grade="C"
        )

        # Output in different formats
        print(generator.format(report, OutputFormat.MARKDOWN))
    """

    def __init__(
        self,
        max_priority_issues: int = 10,
        max_secondary_issues: int = 10,
        max_minor_issues: int = 5,
        max_recommendations: int = 5,
    ):
        """
        Initialize the report generator.

        Args:
            max_priority_issues: Maximum high/critical issues to include
            max_secondary_issues: Maximum medium issues to include
            max_minor_issues: Maximum low/info issues to include
            max_recommendations: Maximum quick-fix recommendations to generate
        """
        self.max_priority_issues = max_priority_issues
        self.max_secondary_issues = max_secondary_issues
        self.max_minor_issues = max_minor_issues
        self.max_recommendations = max_recommendations

        # Quick fix generators by category (can be extended)
        self._quick_fix_generators: Dict[str, Callable[[Issue], Optional[str]]] = {}

    def register_quick_fix_generator(
        self,
        category: str,
        generator: Callable[[Issue], Optional[str]]
    ) -> None:
        """
        Register a custom quick-fix generator for a category.

        Args:
            category: The issue category this generator handles
            generator: Function that takes an Issue and returns a fix suggestion or None
        """
        self._quick_fix_generators[category] = generator

    def generate(
        self,
        title: str,
        issues: List[Issue],
        score: Optional[float] = None,
        grade: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Report:
        """
        Generate a structured report from a list of issues.

        Args:
            title: Report title
            issues: List of Issue objects from analysis
            score: Optional overall score (0-100)
            grade: Optional letter grade
            confidence: Optional confidence level (0.0-1.0)
            metadata: Optional additional metadata

        Returns:
            Report object with prioritized issues and recommendations
        """
        # Sort and prioritize issues
        prioritized = self._prioritize_issues(issues)

        # Calculate summary statistics
        summary = self._calculate_summary(issues, score, grade, confidence)

        # Generate recommendations from high-priority issues
        recommendations = self._generate_recommendations(prioritized["priority"])

        # Combine all issues in priority order
        all_sorted_issues = (
            prioritized["priority"] +
            prioritized["secondary"] +
            prioritized["minor"]
        )

        return Report(
            title=title,
            summary=summary,
            issues=all_sorted_issues,
            recommendations=recommendations,
            metadata=metadata or {},
        )

    def format(self, report: Report, output_format: OutputFormat = OutputFormat.TEXT) -> str:
        """
        Format a report for output.

        Args:
            report: The Report object to format
            output_format: Desired output format (TEXT, MARKDOWN, JSON)

        Returns:
            Formatted string representation of the report
        """
        if output_format == OutputFormat.JSON:
            return self._format_json(report)
        elif output_format == OutputFormat.MARKDOWN:
            return self._format_markdown(report)
        else:
            return self._format_text(report)

    def _prioritize_issues(
        self,
        issues: List[Issue]
    ) -> Dict[str, List[Issue]]:
        """Sort and group issues by severity."""
        # Group by severity
        priority = [i for i in issues if i.severity in (Severity.CRITICAL, Severity.HIGH)]
        secondary = [i for i in issues if i.severity == Severity.MEDIUM]
        minor = [i for i in issues if i.severity in (Severity.LOW, Severity.INFO)]

        # Sort each group by points (descending), then by severity
        def sort_key(issue: Issue) -> tuple:
            return (-issue.points, -issue.severity.weight)

        priority.sort(key=sort_key)
        secondary.sort(key=sort_key)
        minor.sort(key=sort_key)

        return {
            "priority": priority[:self.max_priority_issues],
            "secondary": secondary[:self.max_secondary_issues],
            "minor": minor[:self.max_minor_issues],
        }

    def _calculate_summary(
        self,
        issues: List[Issue],
        score: Optional[float],
        grade: Optional[str],
        confidence: Optional[float],
    ) -> ReportSummary:
        """Calculate summary statistics from issues."""
        by_severity: Dict[str, int] = {}
        by_category: Dict[str, int] = {}

        for issue in issues:
            # Count by severity
            sev_name = issue.severity.name
            by_severity[sev_name] = by_severity.get(sev_name, 0) + 1

            # Count by category
            by_category[issue.category] = by_category.get(issue.category, 0) + 1

        return ReportSummary(
            total_issues=len(issues),
            by_severity=by_severity,
            by_category=by_category,
            score=score,
            grade=grade,
            confidence=confidence,
        )

    def _generate_recommendations(self, priority_issues: List[Issue]) -> List[str]:
        """Generate actionable recommendations from high-priority issues."""
        recommendations: List[str] = []
        seen: set = set()

        for issue in priority_issues[:self.max_recommendations * 2]:
            fix = None

            # Try issue's own quick_fix first
            if issue.quick_fix:
                fix = issue.quick_fix

            # Try registered generator for this category
            elif issue.category in self._quick_fix_generators:
                fix = self._quick_fix_generators[issue.category](issue)

            # Use default generator
            else:
                fix = self._default_quick_fix(issue)

            if fix and fix not in seen:
                recommendations.append(fix)
                seen.add(fix)

            if len(recommendations) >= self.max_recommendations:
                break

        return recommendations

    def _default_quick_fix(self, issue: Issue) -> str:
        """Generate a default quick-fix suggestion."""
        severity_prefix = {
            Severity.CRITICAL: "URGENT: ",
            Severity.HIGH: "",
            Severity.MEDIUM: "",
            Severity.LOW: "Consider: ",
            Severity.INFO: "Note: ",
        }

        prefix = severity_prefix.get(issue.severity, "")
        return f"{prefix}Address {issue.issue_type} issue in {issue.category}: {issue.description}"

    def _format_json(self, report: Report) -> str:
        """Format report as JSON."""
        return json.dumps(report.to_dict(), indent=2)

    def _format_markdown(self, report: Report) -> str:
        """Format report as Markdown."""
        lines: List[str] = []

        # Title
        lines.append(f"# {report.title}")
        lines.append("")
        lines.append(f"*Generated: {report.generated_at}*")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Issues:** {report.summary.total_issues}")

        if report.summary.score is not None:
            lines.append(f"- **Score:** {report.summary.score:.1f}")
        if report.summary.grade:
            lines.append(f"- **Grade:** {report.summary.grade}")
        if report.summary.confidence is not None:
            lines.append(f"- **Confidence:** {report.summary.confidence:.1%}")

        lines.append("")

        # By severity
        if report.summary.by_severity:
            lines.append("### Issues by Severity")
            lines.append("")
            for sev, count in sorted(
                report.summary.by_severity.items(),
                key=lambda x: Severity[x[0]].weight,
                reverse=True
            ):
                emoji = {"CRITICAL": "!!!", "HIGH": "!!", "MEDIUM": "!", "LOW": "-", "INFO": "i"}
                lines.append(f"- {emoji.get(sev, '-')} **{sev}:** {count}")
            lines.append("")

        # By category
        if report.summary.by_category:
            lines.append("### Issues by Category")
            lines.append("")
            for cat, count in sorted(report.summary.by_category.items()):
                lines.append(f"- **{cat}:** {count}")
            lines.append("")

        # Recommendations
        if report.recommendations:
            lines.append("## Quick Fixes")
            lines.append("")
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        # Issues
        if report.issues:
            lines.append("## Issues")
            lines.append("")

            current_severity = None
            for issue in report.issues:
                if issue.severity != current_severity:
                    current_severity = issue.severity
                    lines.append(f"### {current_severity.name} Priority")
                    lines.append("")

                location_str = f" at `{issue.location}`" if issue.location else ""
                lines.append(f"- **[{issue.category}]** {issue.description}{location_str}")
                if issue.quick_fix:
                    lines.append(f"  - *Fix: {issue.quick_fix}*")

            lines.append("")

        return "\n".join(lines)

    def _format_text(self, report: Report, width: int = 70) -> str:
        """Format report as plain text.

        Args:
            report: The Report object to format
            width: Line width for formatting (default: 70)
        """
        lines: List[str] = []

        # Title
        lines.append("=" * width)
        lines.append(report.title.center(width))
        lines.append("=" * width)
        lines.append(f"Generated: {report.generated_at}")
        lines.append("")

        # Summary
        lines.append("-" * width)
        lines.append("SUMMARY")
        lines.append("-" * width)
        lines.append(f"Total Issues: {report.summary.total_issues}")

        if report.summary.score is not None:
            lines.append(f"Score: {report.summary.score:.1f}")
        if report.summary.grade:
            lines.append(f"Grade: {report.summary.grade}")
        if report.summary.confidence is not None:
            lines.append(f"Confidence: {report.summary.confidence:.1%}")

        lines.append("")

        # By severity
        if report.summary.by_severity:
            lines.append("By Severity:")
            for sev, count in sorted(
                report.summary.by_severity.items(),
                key=lambda x: Severity[x[0]].weight,
                reverse=True
            ):
                lines.append(f"  {sev}: {count}")
            lines.append("")

        # Recommendations
        if report.recommendations:
            lines.append("-" * width)
            lines.append("QUICK FIXES")
            lines.append("-" * width)
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        # Issues
        if report.issues:
            lines.append("-" * width)
            lines.append("ISSUES")
            lines.append("-" * width)

            current_severity = None
            for issue in report.issues:
                if issue.severity != current_severity:
                    current_severity = issue.severity
                    lines.append("")
                    lines.append(f"[{current_severity.name}]")

                location_str = f" @ {issue.location}" if issue.location else ""
                lines.append(f"  [{issue.category}] {issue.description}{location_str}")

            lines.append("")

        lines.append("=" * width)
        return "\n".join(lines)


def create_issue(
    category: str,
    issue_type: str,
    severity: str,
    description: str,
    points: float = 0.0,
    location: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    quick_fix: Optional[str] = None,
) -> Issue:
    """
    Factory function to create an Issue with string severity.

    Args:
        category: Issue category
        issue_type: Specific issue type
        severity: Severity as string ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")
        description: Human-readable description
        points: Numeric weight for sorting
        location: Optional location info
        details: Optional additional details
        quick_fix: Optional suggested fix

    Returns:
        Issue object

    Example:
        issue = create_issue(
            category="security",
            issue_type="xss",
            severity="HIGH",
            description="Potential XSS vulnerability",
            points=8.0,
            location="templates/user.html:15"
        )

    Raises:
        ValueError: If severity is not a valid severity level
    """
    try:
        severity_enum = Severity[severity.upper()]
    except KeyError:
        valid_values = ", ".join(s.name for s in Severity)
        raise ValueError(
            f"Invalid severity '{severity}'. Must be one of: {valid_values}"
        )
    return Issue(
        category=category,
        issue_type=issue_type,
        severity=severity_enum,
        description=description,
        points=points,
        location=location,
        details=details or {},
        quick_fix=quick_fix,
    )


def generate_simple_report(
    title: str,
    issues: List[Dict[str, Any]],
    score: Optional[float] = None,
    output_format: str = "text",
) -> str:
    """
    Convenience function for simple report generation.

    Args:
        title: Report title
        issues: List of issue dicts with keys: category, type, severity, description
        score: Optional overall score
        output_format: Output format ("text", "markdown", "json")

    Returns:
        Formatted report string

    Example:
        report = generate_simple_report(
            title="Analysis Results",
            issues=[
                {"category": "quality", "type": "complexity", "severity": "MEDIUM",
                 "description": "High cyclomatic complexity"},
            ],
            score=85.0,
            output_format="markdown"
        )
    """
    generator = ReportGenerator()

    issue_objects = [
        create_issue(
            category=i.get("category", "general"),
            issue_type=i.get("type", "unknown"),
            severity=i.get("severity", "INFO"),
            description=i.get("description", ""),
            points=i.get("points", 0.0),
            location=i.get("location"),
            details=i.get("details"),
            quick_fix=i.get("quick_fix"),
        )
        for i in issues
    ]

    report = generator.generate(
        title=title,
        issues=issue_objects,
        score=score,
    )

    format_map = {
        "text": OutputFormat.TEXT,
        "markdown": OutputFormat.MARKDOWN,
        "json": OutputFormat.JSON,
    }

    return generator.format(report, format_map.get(output_format, OutputFormat.TEXT))
