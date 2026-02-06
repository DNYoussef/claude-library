from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.auth.fastapi_jwt.jwt_auth'
EXPORTS = ['AuthenticationError', 'AuthorizationError', 'JWTAuthConfig', 'JWTAuthService', 'TokenData', 'User', 'get_auth_service', 'init_jwt_auth', 'require_any_role', 'require_role', 'verify_resource_ownership', 'verify_resource_ownership_or_admin']


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
