from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.cognitive_architecture.core.vcl_validator'
EXPORTS = ['ASPType', 'CompressionLevel', 'EVDType', 'HONLevel', 'L2Naturalizer', 'VCLConfig', 'VCLSlot', 'VCLStatement', 'VCLValidator', 'ValidationResult', 'compute_cluster_signature', 'enforce_safety_bounds', 'naturalize_to_l2', 'validate_vcl']


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
