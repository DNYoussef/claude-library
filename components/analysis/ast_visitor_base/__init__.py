"""
AST Visitor Base Pattern - Code Analysis Framework

Provides base visitor classes for traversing Python AST nodes
during code analysis. Includes concrete implementations for
common analysis patterns.

Source: Extracted from connascence/analyzer/ast_engine/visitors.py
"""

from .visitor_base import (
    VisitorContext,
    BaseConnascenceVisitor,
    MagicLiteralVisitor,
    ParameterPositionVisitor,
    GodObjectVisitor,
    ComplexityVisitor,
)

__all__ = [
    "VisitorContext",
    "BaseConnascenceVisitor",
    "MagicLiteralVisitor",
    "ParameterPositionVisitor",
    "GodObjectVisitor",
    "ComplexityVisitor",
]
