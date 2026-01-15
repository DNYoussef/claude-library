"""
AST Visitor Base Component

Extended AST visitor with violation collection, path tracking,
and pattern matching support for code analysis.

References:
- https://docs.python.org/3/library/ast.html
- https://github.com/Instagram/LibCST

Example:
    from library.components.analysis.ast_visitor import (
        AnalysisVisitor,
        visit_file,
    )
    from library.common.types import Severity

    class ComplexityChecker(AnalysisVisitor):
        def visit_FunctionDef(self, node):
            if len(node.body) > 50:
                self.add_violation(
                    severity=Severity.HIGH,
                    message=f"Function {node.name} too long",
                    node=node,
                )
            self.generic_visit(node)

    violations = visit_file("my_code.py", ComplexityChecker)
"""

from .visitor import (
    # Core classes
    AnalysisVisitor,
    AnalysisTransformer,
    CompositeVisitor,
    VisitorContext,
    # Parsing functions
    parse_file,
    parse_source,
    visit_file,
    visit_source,
    # Pattern matchers
    is_name,
    is_call,
    is_method_call,
    get_assigned_name,
    count_nodes,
)

__all__ = [
    # Core classes
    "AnalysisVisitor",
    "AnalysisTransformer",
    "CompositeVisitor",
    "VisitorContext",
    # Parsing functions
    "parse_file",
    "parse_source",
    "visit_file",
    "visit_source",
    # Pattern matchers
    "is_name",
    "is_call",
    "is_method_call",
    "get_assigned_name",
    "count_nodes",
]
