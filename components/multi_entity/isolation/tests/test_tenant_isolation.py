from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.multi_entity.isolation'
EXPORTS = ['RLSPolicy', 'TenantContext', 'TenantMiddleware', 'TenantMixin', 'create_tenant_policy', 'disable_rls', 'enable_rls', 'extract_tenant_from_header', 'extract_tenant_from_path', 'extract_tenant_from_subdomain', 'force_rls', 'generate_rls_migration', 'get_current_tenant', 'require_tenant', 'set_current_tenant', 'setup_rls_session', 'setup_tenant_isolation']


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
