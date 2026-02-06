from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.utilities.quality_gate.quality_gate'
EXPORTS = ['GateConfig', 'GateFailedError', 'GateManager', 'GateResult', 'GateStatus', 'GateType', 'RichMetricResult', 'create_compile_gate', 'create_dependency_gate', 'create_quality_gate', 'create_sync_gate']


def _import_module():
    return import_component_module(MODULE_PATH)

def test_module_imports():
    _import_module()


def test_exports_present():
    module = _import_module()
    if not EXPORTS:
        return
    missing = [name for name in EXPORTS if not hasattr(module, name)]
    assert not missing, f"Missing exports: {missing}"
