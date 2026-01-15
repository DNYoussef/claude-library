from __future__ import annotations

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


def _library_root() -> Path:
    root = Path(__file__).resolve()
    while root != root.parent:
        if (root / "catalog.json").exists() and (root / "components").exists():
            return root
        root = root.parent
    raise RuntimeError("Library root not found")


def _ensure_library_package() -> None:
    root = _library_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    if "library" not in sys.modules:
        library = types.ModuleType("library")
        library.__path__ = [str(root)]
        sys.modules["library"] = library


def _import_module():
    _ensure_library_package()
    try:
        return importlib.import_module(MODULE_PATH)
    except ModuleNotFoundError as exc:
        if exc.name and exc.name in MODULE_PATH:
            raise
        pytest.skip(f"Missing dependency: {exc.name}")
    except ImportError as exc:
        pytest.skip(f"Import error: {exc}")


def test_module_imports():
    _import_module()


def test_exports_present():
    module = _import_module()
    missing = [name for name in EXPORTS if not hasattr(module, name)]
    assert not missing, f"Missing exports: {missing}"
