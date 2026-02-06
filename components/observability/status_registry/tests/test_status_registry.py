from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

import importlib
import sys
import types
from pathlib import Path

import pytest

MODULE_PATH = "components.observability.status_registry.status_registry"
EXPORTS = [
    "ProjectStatus",
    "RepoSignals",
    "STATUS_END_MARKER",
    "STATUS_START_MARKER",
    "build_registry",
    "parse_project_table",
    "render_project_markdown",
    "render_markdown",
    "scan_repo_signals",
    "update_marked_section",
    "update_project_readme",
    "update_repo_readmes",
]


def _import_module():
    return import_component_module(MODULE_PATH)

def test_module_imports():
    _import_module()


def test_exports_present():
    module = _import_module()
    missing = [name for name in EXPORTS if not hasattr(module, name)]
    assert not missing, f"Missing exports: {missing}"
