"""Shared import helpers for component test modules."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest


_CACHED_LIBRARY_ROOT: Path | None = None


def _library_root() -> Path:
    global _CACHED_LIBRARY_ROOT
    if _CACHED_LIBRARY_ROOT is not None:
        return _CACHED_LIBRARY_ROOT

    root = Path(__file__).resolve()
    while root != root.parent:
        has_catalog = (root / "catalog-index.json").exists() or (root / "catalog.json").exists()
        if has_catalog and (root / "components").exists():
            _CACHED_LIBRARY_ROOT = root
            return root
        root = root.parent

    raise RuntimeError("Library root not found")


def ensure_library_package() -> None:
    root = _library_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    if "library" not in sys.modules:
        library = types.ModuleType("library")
        library.__path__ = [str(root)]
        sys.modules["library"] = library


def import_component_module(module_path: str):
    """Import a component module while gracefully skipping optional dependencies."""
    ensure_library_package()

    try:
        return importlib.import_module(module_path)
    except ModuleNotFoundError as exc:
        if exc.name and exc.name in module_path:
            raise
        pytest.skip(f"Missing dependency: {exc.name}")
    except ImportError as exc:
        pytest.skip(f"Import error: {exc}")
