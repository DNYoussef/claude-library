from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.analysis.ast_visitor'
EXPORTS = ['AnalysisTransformer', 'AnalysisVisitor', 'CompositeVisitor', 'VisitorContext', 'count_nodes', 'get_assigned_name', 'is_call', 'is_method_call', 'is_name', 'parse_file', 'parse_source', 'visit_file', 'visit_source']


def _import_module():
    return import_component_module(MODULE_PATH)


def test_exports_present():
    module = _import_module()
    if not EXPORTS:
        return
    missing = [name for name in EXPORTS if not hasattr(module, name)]
    assert not missing, f"Missing exports: {missing}"
