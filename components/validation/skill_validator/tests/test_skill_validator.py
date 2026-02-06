from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.validation.skill_validator'
EXPORTS = ['DEFAULT_CATEGORY_KEYWORDS', 'STOPWORDS', 'SkillData', 'SkillIndexer', 'SkillValidator', 'ValidationResult', 'YAML_AVAILABLE', '__author__', '__version__', 'extract_keywords', 'extract_section', 'extract_trigger_positive', 'parse_yaml_fallback', 'parse_yaml_frontmatter', 'parse_yaml_safe', 'validate_single_file']


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
