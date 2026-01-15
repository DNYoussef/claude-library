"""
AST Visitor Base Component

Extended AST visitor with violation collection, path tracking,
and pattern matching support for code analysis.

Based on:
- Python ast.NodeVisitor: https://docs.python.org/3/library/ast.html
- LibCST patterns: https://github.com/Instagram/LibCST

Features:
- Enhanced NodeVisitor with context tracking
- Automatic violation collection using common/types
- Scope and path tracking
- Pattern matching helpers
- NodeTransformer for modifications

Example:
    from library.components.analysis.ast_visitor import (
        AnalysisVisitor,
        visit_file,
    )

    class ComplexityChecker(AnalysisVisitor):
        def visit_FunctionDef(self, node):
            if len(node.body) > 50:
                self.add_violation(
                    severity="high",
                    message=f"Function {node.name} too long",
                    node=node,
                )
            self.generic_visit(node)

    violations = visit_file("my_code.py", ComplexityChecker)
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

# LEGO Pattern: Import shared types from common/types
from library.common.types import Severity, Violation, QualityResult


@dataclass
class VisitorContext:
    """
    Context maintained during AST traversal.

    Tracks current file, scope chain, and visited nodes.
    """

    file_path: Optional[str] = None
    scope_chain: List[str] = field(default_factory=list)
    current_class: Optional[str] = None
    current_function: Optional[str] = None
    depth: int = 0
    visited_nodes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def scope_path(self) -> str:
        """Get current scope as dotted path."""
        return ".".join(self.scope_chain) if self.scope_chain else "<module>"

    def push_scope(self, name: str):
        """Enter a new scope."""
        self.scope_chain.append(name)

    def pop_scope(self) -> Optional[str]:
        """Exit current scope."""
        return self.scope_chain.pop() if self.scope_chain else None


class AnalysisVisitor(ast.NodeVisitor):
    """
    Enhanced AST visitor for code analysis with violation collection.

    Extends ast.NodeVisitor with:
    - Automatic violation collection
    - Scope and context tracking
    - Pattern matching helpers
    - Integration with common/types

    Example:
        class MyAnalyzer(AnalysisVisitor):
            def visit_FunctionDef(self, node):
                if node.name.startswith("_"):
                    self.add_violation(
                        severity="info",
                        message=f"Private function: {node.name}",
                        node=node,
                    )
                self.generic_visit(node)
    """

    def __init__(self, file_path: Optional[str] = None):
        self.context = VisitorContext(file_path=file_path)
        self._violations: List[Violation] = []

    @property
    def violations(self) -> List[Violation]:
        """Get collected violations."""
        return self._violations

    def add_violation(
        self,
        severity: Union[str, Severity],
        message: str,
        node: Optional[ast.AST] = None,
        rule_id: Optional[str] = None,
        suggestion: Optional[str] = None,
        **metadata,
    ):
        """
        Add a violation at the current or specified node.

        Args:
            severity: Violation severity (string or Severity enum)
            message: Description of the issue
            node: AST node where violation occurs
            rule_id: Rule identifier
            suggestion: Fix suggestion
            **metadata: Additional metadata
        """
        if isinstance(severity, str):
            severity = Severity.from_string(severity)

        line = getattr(node, "lineno", None) if node else None
        col = getattr(node, "col_offset", None) if node else None
        end_line = getattr(node, "end_lineno", None) if node else None
        end_col = getattr(node, "end_col_offset", None) if node else None

        violation = Violation(
            severity=severity,
            message=message,
            file_path=self.context.file_path,
            line=line,
            column=col,
            end_line=end_line,
            end_column=end_col,
            rule_id=rule_id or self._get_rule_id(),
            suggestion=suggestion,
            metadata={"scope": self.context.scope_path, **metadata},
        )
        self._violations.append(violation)

    def _get_rule_id(self) -> str:
        """Generate default rule ID from class name."""
        return self.__class__.__name__

    def visit(self, node: ast.AST) -> Any:
        """Visit a node with context tracking."""
        self.context.depth += 1
        self.context.visited_nodes += 1
        try:
            return super().visit(node)
        finally:
            self.context.depth -= 1

    def visit_ClassDef(self, node: ast.ClassDef):
        """Track class scope."""
        old_class = self.context.current_class
        self.context.current_class = node.name
        self.context.push_scope(node.name)
        try:
            self.generic_visit(node)
        finally:
            self.context.pop_scope()
            self.context.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function scope."""
        old_function = self.context.current_function
        self.context.current_function = node.name
        self.context.push_scope(node.name)
        try:
            self.generic_visit(node)
        finally:
            self.context.pop_scope()
            self.context.current_function = old_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Track async function scope (same as sync)."""
        old_function = self.context.current_function
        self.context.current_function = node.name
        self.context.push_scope(node.name)
        try:
            self.generic_visit(node)
        finally:
            self.context.pop_scope()
            self.context.current_function = old_function

    def to_quality_result(
        self,
        score: Optional[float] = None,
        threshold: float = 0.8,
    ) -> QualityResult:
        """
        Convert violations to QualityResult.

        Args:
            score: Optional explicit score (0.0-1.0)
            threshold: Score threshold for pass/fail

        Returns:
            QualityResult with violations and computed score
        """
        if score is None:
            # Compute score based on violation weights
            total_weight = sum(v.severity.weight for v in self._violations)
            max_weight = self.context.visited_nodes * Severity.CRITICAL.weight
            if max_weight > 0:
                score = 1.0 - (total_weight / max_weight)
            else:
                score = 1.0

        return QualityResult(
            passed=score >= threshold,
            score=score,
            violations=self._violations,
            metadata={
                "file_path": self.context.file_path,
                "nodes_visited": self.context.visited_nodes,
            },
        )


class AnalysisTransformer(ast.NodeTransformer):
    """
    AST transformer with context tracking for code modifications.

    Extends ast.NodeTransformer with same context features as AnalysisVisitor.

    Example:
        class RemoveComments(AnalysisTransformer):
            def visit_Expr(self, node):
                # Remove docstrings
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    return None
                return node
    """

    def __init__(self, file_path: Optional[str] = None):
        self.context = VisitorContext(file_path=file_path)
        self._modifications: List[str] = []

    def log_modification(self, message: str, node: Optional[ast.AST] = None):
        """Log a modification made."""
        location = ""
        if node:
            line = getattr(node, "lineno", "?")
            location = f" at line {line}"
        self._modifications.append(f"{message}{location}")

    @property
    def modifications(self) -> List[str]:
        """Get list of modifications made."""
        return self._modifications


class CompositeVisitor(AnalysisVisitor):
    """
    Composite visitor that runs multiple visitors in sequence.

    Example:
        composite = CompositeVisitor([
            ComplexityChecker(),
            SecurityScanner(),
            StyleChecker(),
        ])
        composite.visit(tree)
        all_violations = composite.violations
    """

    def __init__(
        self,
        visitors: List[AnalysisVisitor],
        file_path: Optional[str] = None,
    ):
        super().__init__(file_path)
        self._visitors = visitors
        # Share context
        for v in visitors:
            v.context = self.context

    def visit(self, node: ast.AST) -> Any:
        """Visit with all sub-visitors."""
        for visitor in self._visitors:
            visitor.visit(node)
        return super().visit(node)

    @property
    def violations(self) -> List[Violation]:
        """Aggregate violations from all visitors."""
        all_violations = []
        for visitor in self._visitors:
            all_violations.extend(visitor.violations)
        return all_violations


def parse_file(file_path: Union[str, Path]) -> ast.Module:
    """
    Parse a Python file into an AST.

    Args:
        file_path: Path to Python file

    Returns:
        Parsed AST module
    """
    path = Path(file_path)
    source = path.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(path))


def parse_source(source: str, filename: str = "<string>") -> ast.Module:
    """
    Parse Python source code into an AST.

    Args:
        source: Python source code
        filename: Optional filename for error messages

    Returns:
        Parsed AST module
    """
    return ast.parse(source, filename=filename)


def visit_file(
    file_path: Union[str, Path],
    visitor_class: Type[AnalysisVisitor],
    **visitor_kwargs,
) -> List[Violation]:
    """
    Parse and visit a file, returning violations.

    Args:
        file_path: Path to Python file
        visitor_class: AnalysisVisitor subclass
        **visitor_kwargs: Arguments for visitor constructor

    Returns:
        List of violations found
    """
    path = Path(file_path)
    tree = parse_file(path)
    visitor = visitor_class(file_path=str(path), **visitor_kwargs)
    visitor.visit(tree)
    return visitor.violations


def visit_source(
    source: str,
    visitor_class: Type[AnalysisVisitor],
    filename: str = "<string>",
    **visitor_kwargs,
) -> List[Violation]:
    """
    Parse and visit source code, returning violations.

    Args:
        source: Python source code
        visitor_class: AnalysisVisitor subclass
        filename: Optional filename for error messages
        **visitor_kwargs: Arguments for visitor constructor

    Returns:
        List of violations found
    """
    tree = parse_source(source, filename)
    visitor = visitor_class(file_path=filename, **visitor_kwargs)
    visitor.visit(tree)
    return visitor.violations


# =============================================================================
# PATTERN MATCHERS
# =============================================================================


def is_name(node: ast.AST, name: str) -> bool:
    """Check if node is a Name with given id."""
    return isinstance(node, ast.Name) and node.id == name


def is_call(node: ast.AST, func_name: str) -> bool:
    """Check if node is a Call to given function."""
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name):
        return node.func.id == func_name
    if isinstance(node.func, ast.Attribute):
        return node.func.attr == func_name
    return False


def is_method_call(node: ast.AST, obj_name: str, method_name: str) -> bool:
    """Check if node is a method call like obj.method()."""
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr != method_name:
        return False
    return isinstance(node.func.value, ast.Name) and node.func.value.id == obj_name


def get_assigned_name(node: ast.Assign) -> Optional[str]:
    """Get name being assigned to (first target only)."""
    if not node.targets:
        return None
    target = node.targets[0]
    if not isinstance(target, ast.Name):
        return None
    return target.id


def count_nodes(tree: ast.AST, node_type: Type[ast.AST]) -> int:
    """Count nodes of a specific type in tree."""
    return sum(1 for _ in ast.walk(tree) if isinstance(_, node_type))
from abc import ABC, abstractmethod
