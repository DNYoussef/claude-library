"""
AST Visitor Base Pattern

Base visitor classes for traversing Python AST nodes during
code analysis. Implements the visitor pattern for detecting
various code quality issues.

Features:
- Context tracking (file, class, function scope)
- Violation collection with severity and recommendations
- Concrete visitors for common patterns:
  - Magic literal detection (CoM)
  - Parameter bomb detection (CoP)
  - God object detection (CoA)
  - Cyclomatic complexity (CoA)

Usage:
    # Create custom visitor
    class MyVisitor(BaseConnascenceVisitor):
        def get_violation_type(self) -> str:
            return "MyType"

        def visit_FunctionDef(self, node):
            # Analyze function
            if self.is_problematic(node):
                self.add_violation(
                    node,
                    "Found issue in function",
                    severity="medium",
                    recommendation="Consider refactoring",
                )
            self.generic_visit(node)

    # Run visitor
    import ast
    visitor = MyVisitor()
    context = VisitorContext(file_path="example.py", source_code=code)
    tree = ast.parse(code)
    violations = visitor.visit_with_context(tree, context)

Source: Extracted from connascence/analyzer/ast_engine/visitors.py
"""

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class VisitorContext:
    """
    Context passed to visitors during AST traversal.

    Attributes:
        file_path: Path to the file being analyzed
        source_code: Original source code
        current_class: Name of class being visited (if any)
        current_function: Name of function being visited (if any)
        scope_stack: Stack of scope names for nested contexts
        findings: Accumulated findings during traversal
    """
    file_path: str = ""
    source_code: str = ""
    current_class: Optional[str] = None
    current_function: Optional[str] = None
    scope_stack: List[str] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)


class BaseConnascenceVisitor(ast.NodeVisitor, ABC):
    """
    Base visitor class for code analysis.

    Subclasses should implement specific detection logic for
    different types of issues (connascence, complexity, etc.).

    The visitor pattern allows traversing the AST while
    maintaining context about the current scope and
    collecting violations.
    """

    def __init__(self):
        """Initialize visitor with empty state."""
        self.context: Optional[VisitorContext] = None
        self.violations: List[Dict[str, Any]] = []

    def visit_with_context(
        self,
        node: ast.AST,
        context: VisitorContext
    ) -> List[Dict[str, Any]]:
        """
        Visit AST with provided context and return violations.

        Args:
            node: Root AST node to visit
            context: Context with file path, source, etc.

        Returns:
            List of violations found during traversal
        """
        self.context = context
        self.violations = []
        self.visit(node)
        return self.violations

    @abstractmethod
    def get_violation_type(self) -> str:
        """
        Return the type identifier for violations this visitor detects.

        Examples: "CoM", "CoP", "CoA", "complexity"
        """
        pass

    def add_violation(
        self,
        node: ast.AST,
        description: str,
        severity: str = "medium",
        recommendation: str = "",
    ) -> None:
        """
        Add a violation to the findings list.

        Args:
            node: AST node where violation was found
            description: Human-readable description
            severity: One of "critical", "high", "medium", "low", "info"
            recommendation: Suggested fix
        """
        self.violations.append({
            "type": self.get_violation_type(),
            "severity": severity,
            "line_number": getattr(node, "lineno", 0),
            "column": getattr(node, "col_offset", 0),
            "description": description,
            "recommendation": recommendation,
            "file_path": self.context.file_path if self.context else "",
        })


class MagicLiteralVisitor(BaseConnascenceVisitor):
    """
    Visitor that detects magic literals (Connascence of Meaning).

    Magic literals are hardcoded values that should be named constants.
    Allowed: 0, 1, -1, "", True, False, None
    """

    ALLOWED_LITERALS: Set[Any] = {0, 1, -1, "", True, False, None}

    def get_violation_type(self) -> str:
        return "CoM"

    def visit_Constant(self, node: ast.Constant) -> None:
        """Check for magic literal constants."""
        if node.value in self.ALLOWED_LITERALS:
            self.generic_visit(node)
            return
        if isinstance(node.value, (int, float)) and abs(node.value) > 1:
            self.add_violation(
                node,
                f"Magic literal '{node.value}' should be extracted to a named constant",
                severity="medium",
                recommendation="Extract to a named constant with descriptive name",
            )
        self.generic_visit(node)


class ParameterPositionVisitor(BaseConnascenceVisitor):
    """
    Visitor that detects position coupling (Connascence of Position).

    Functions with too many positional parameters create coupling
    where callers must remember argument order.
    """

    MAX_POSITIONAL_PARAMS: int = 4

    def get_violation_type(self) -> str:
        return "CoP"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function parameter count."""
        positional_params = [
            arg for arg in node.args.args
            if arg.arg not in ("self", "cls")
        ]
        if len(positional_params) > self.MAX_POSITIONAL_PARAMS:
            self.add_violation(
                node,
                f"Function '{node.name}' has {len(positional_params)} positional parameters (max: {self.MAX_POSITIONAL_PARAMS})",
                severity="high",
                recommendation="Use keyword-only arguments or a configuration object",
            )
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef


class GodObjectVisitor(BaseConnascenceVisitor):
    """
    Visitor that detects god objects (excessive class complexity).

    Classes with too many methods violate single responsibility
    and become difficult to maintain.
    """

    MAX_METHODS: int = 20
    MAX_ATTRIBUTES: int = 15

    def get_violation_type(self) -> str:
        return "CoA"

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Check class complexity."""
        methods = [
            n for n in node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        if len(methods) > self.MAX_METHODS:
            self.add_violation(
                node,
                f"Class '{node.name}' has {len(methods)} methods (max: {self.MAX_METHODS})",
                severity="critical",
                recommendation="Split into smaller, focused classes",
            )
        self.generic_visit(node)


class ComplexityVisitor(BaseConnascenceVisitor):
    """
    Visitor that detects high cyclomatic complexity.

    High complexity makes code hard to test and maintain.
    Each branch point (if, for, while, etc.) adds complexity.
    """

    MAX_COMPLEXITY: int = 10

    def get_violation_type(self) -> str:
        return "complexity"

    def _count_complexity(self, node: ast.AST) -> int:
        """Count cyclomatic complexity for a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Each branch point adds 1
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # and/or add complexity
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                if child.ifs:
                    complexity += len(child.ifs)

        return complexity

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function cyclomatic complexity."""
        complexity = self._count_complexity(node)
        if complexity > self.MAX_COMPLEXITY:
            self.add_violation(
                node,
                f"Function '{node.name}' has cyclomatic complexity {complexity} (max: {self.MAX_COMPLEXITY})",
                severity="high",
                recommendation="Refactor into smaller functions or use early returns",
            )
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef
