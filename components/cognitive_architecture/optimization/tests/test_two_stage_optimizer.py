from __future__ import annotations

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.cognitive_architecture.optimization.two_stage_optimizer'
EXPORTS = ['CognitiveProblem14D', 'CognitiveProblem5D', 'OptimizationResult', 'TwoStageOptimizer', 'config_14d_to_fullconfig', 'distill_named_modes', 'evaluate_config_14dim', 'evaluate_config_5dim', 'expand_5d_to_14d', 'main', 'run_globalmoo_stage', 'run_pymoo_refinement_stage', 'run_with_telemetry', 'save_results']


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
