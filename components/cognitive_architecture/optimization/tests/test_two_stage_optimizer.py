from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.cognitive_architecture.optimization.two_stage_optimizer'
EXPORTS = ['CognitiveProblem14D', 'CognitiveProblem5D', 'OptimizationResult', 'TwoStageOptimizer', 'config_14d_to_fullconfig', 'distill_named_modes', 'evaluate_config_14dim', 'evaluate_config_5dim', 'expand_5d_to_14d', 'main', 'run_globalmoo_stage', 'run_pymoo_refinement_stage', 'run_with_telemetry', 'save_results']


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
