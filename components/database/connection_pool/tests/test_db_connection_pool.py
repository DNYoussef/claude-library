from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.database.connection_pool'
EXPORTS = ['Base', 'ConnectionPool', 'DatabaseHealthChecker', 'HealthCheckConfig', 'HealthCheckEndpoint', 'HealthState', 'HealthStatus', 'PoolConfig', 'close_pool', 'get_db', 'get_pool', 'init_pool', 'with_retry']


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
