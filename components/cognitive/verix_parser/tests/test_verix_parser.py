from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.cognitive.verix_parser'
EXPORTS = ['Affect', 'Agent', 'CompressionLevel', 'Illocution', 'L0_CONTENT_TRUNCATION_LENGTH', 'MAX_CLAIMS_LIMIT', 'MAX_INPUT_LENGTH', 'MetaLevel', 'PromptConfig', 'State', 'VERSION', 'VerixClaim', 'VerixParser', 'VerixStrictness', 'VerixValidator', '__version__', 'create_claim', 'create_meta_claim', 'create_meta_verix_claim', 'format_claim']


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
