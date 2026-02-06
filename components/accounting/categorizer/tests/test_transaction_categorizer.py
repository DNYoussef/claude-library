from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.accounting.categorizer'
EXPORTS = ['CategorizerConfig', 'CategoryResult', 'TransactionCategorizer', 'TransactionCategory']


def _import_module():
    return import_component_module(MODULE_PATH)


def test_exports_present():
    module = _import_module()
    if not EXPORTS:
        return
    missing = [name for name in EXPORTS if not hasattr(module, name)]
    assert not missing, f"Missing exports: {missing}"
