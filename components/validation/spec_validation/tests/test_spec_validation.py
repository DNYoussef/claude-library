from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.validation.spec_validation'
EXPORTS = ['BaseValidator', 'ContextValidator', 'DEFAULT_CONTEXT_SCHEMA', 'DEFAULT_IMPLEMENTATION_PLAN_SCHEMA', 'DEFAULT_PHASE_SCHEMA', 'DEFAULT_REQUIREMENTS_SCHEMA', 'DEFAULT_SPEC_RECOMMENDED_SECTIONS', 'DEFAULT_SPEC_REQUIRED_SECTIONS', 'DEFAULT_SUBTASK_SCHEMA', 'DEFAULT_VERIFICATION_SCHEMA', 'ImplementationPlanValidator', 'JSONFileValidator', 'MarkdownDocumentValidator', 'PrereqsValidator', 'SpecDocumentValidator', 'SpecValidator', 'Validatable', 'ValidationResult', 'ValidationSchema', 'ValidatorFactory', 'create_validator_from_config', 'validate_spec_directory']


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
