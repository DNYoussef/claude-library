from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.cognitive.cognitive_config'
EXPORTS = ['CompressionLevel', 'DEFAULT_CONFIG', 'DEFAULT_EVIDENTIAL_MINIMUM', 'DEFAULT_FRAME_WEIGHTS', 'FrameworkConfig', 'FullConfig', 'MINIMAL_CONFIG', 'NAMED_MODES', 'PromptConfig', 'STRICT_CONFIG', 'VectorCodec', 'VerixStrictness', 'create_audit_config', 'create_balanced_config', 'create_research_config', 'create_robust_config', 'create_speed_config', 'get_named_mode']


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
