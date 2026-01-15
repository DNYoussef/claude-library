from __future__ import annotations

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.validation.spec_validation'
EXPORTS = ['BaseValidator', 'ContextValidator', 'DEFAULT_CONTEXT_SCHEMA', 'DEFAULT_IMPLEMENTATION_PLAN_SCHEMA', 'DEFAULT_PHASE_SCHEMA', 'DEFAULT_REQUIREMENTS_SCHEMA', 'DEFAULT_SPEC_RECOMMENDED_SECTIONS', 'DEFAULT_SPEC_REQUIRED_SECTIONS', 'DEFAULT_SUBTASK_SCHEMA', 'DEFAULT_VERIFICATION_SCHEMA', 'ImplementationPlanValidator', 'JSONFileValidator', 'MarkdownDocumentValidator', 'PrereqsValidator', 'SpecDocumentValidator', 'SpecValidator', 'Validatable', 'ValidationResult', 'ValidationSchema', 'ValidatorFactory', 'create_validator_from_config', 'validate_spec_directory']


def _library_root() -> Path:
    root = Path(__file__).resolve()
    while root != root.parent:
        if (root / 'catalog.json').exists() and (root / 'components').exists():
            return root
        root = root.parent
    raise RuntimeError('Library root not found')


def _ensure_library_package() -> None:
    root = _library_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    if 'library' not in sys.modules:
        library = types.ModuleType('library')
        library.__path__ = [str(root)]
        sys.modules['library'] = library


def _import_module():
    _ensure_library_package()
    try:
        return importlib.import_module(MODULE_PATH)
    except ModuleNotFoundError as exc:
        if exc.name and exc.name in MODULE_PATH:
            raise
        pytest.skip(f'Missing dependency: {exc.name}')
    except ImportError as exc:
        pytest.skip(f'Import error: {exc}')


def test_module_imports():
    _import_module()


def test_exports_present():
    module = _import_module()
    if not EXPORTS:
        return
    missing = [name for name in EXPORTS if not hasattr(module, name)]
    assert not missing, f"Missing exports: {missing}"
