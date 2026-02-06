from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.analysis.statistical_analyzer'
EXPORTS = ['BurstinessMetrics', 'EntropyMetrics', 'HapaxMetrics', 'LexicalDiversityMetrics', 'SentenceStartMetrics', 'StatisticalAnalyzer', 'StatisticalMetrics', 'calculate_coefficient_of_variation', 'calculate_hapax_ratio', 'calculate_shannon_entropy', 'calculate_type_token_ratio']


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
