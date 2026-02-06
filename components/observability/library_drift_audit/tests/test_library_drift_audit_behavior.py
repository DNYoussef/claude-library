from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

import importlib
import json
import sys
import types
from pathlib import Path

import pytest

MODULE_PATH = "components.observability.library_drift_audit.library_drift_audit"


def _import_module():
    return import_component_module(MODULE_PATH)


def _write_catalog(path: Path, location: str) -> None:
    data = {
        "components": [
            {
                "id": "demo-component",
                "domain": "utilities",
                "location": location,
            }
        ]
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def _write_status(path: Path, repo_root: Path) -> None:
    data = {"projects": [{"name": "DemoRepo", "location": str(repo_root)}]}
    path.write_text(json.dumps(data), encoding="utf-8")


def test_build_report_detects_import_and_copy(tmp_path: Path):
    module = _import_module()
    library_root = tmp_path / "library"
    catalog_path = library_root / "catalog.json"
    components_root = library_root / "components" / "utilities" / "demo"
    components_root.mkdir(parents=True)
    component_file = components_root / "demo.py"
    component_file.write_text("VALUE = 42\n", encoding="utf-8")
    _write_catalog(catalog_path, "components/utilities/demo/demo.py")

    repo_root = tmp_path / "repo"
    repo_component_dir = repo_root / "demo"
    repo_component_dir.mkdir(parents=True)
    (repo_component_dir / "demo.py").write_text("VALUE = 42\n", encoding="utf-8")
    (repo_root / "app.py").write_text(
        "from library.components.utilities.demo import demo\n", encoding="utf-8"
    )
    status_path = tmp_path / "status.json"
    _write_status(status_path, repo_root)

    catalog = module._load_catalog(catalog_path)
    components = module._build_components(catalog, library_root)
    status_data = module._load_status(status_path)
    report = module.build_report(status_data, components)

    summary = report["summary"]
    assert summary["total_imported_components"] == 1
    assert summary["total_drifted_components"] == 0
    assert summary["total_missing_deployments"] == 0


def test_build_report_marks_drifted_copy(tmp_path: Path):
    module = _import_module()
    library_root = tmp_path / "library"
    catalog_path = library_root / "catalog.json"
    components_root = library_root / "components" / "utilities" / "demo"
    components_root.mkdir(parents=True)
    component_file = components_root / "demo.py"
    component_file.write_text("VALUE = 42\n", encoding="utf-8")
    _write_catalog(catalog_path, "components/utilities/demo/demo.py")

    repo_root = tmp_path / "repo"
    repo_component_dir = repo_root / "demo"
    repo_component_dir.mkdir(parents=True)
    (repo_component_dir / "demo.py").write_text("VALUE = 99\n", encoding="utf-8")
    (repo_root / "app.py").write_text(
        "from library.components.utilities.demo import demo\n", encoding="utf-8"
    )
    status_path = tmp_path / "status.json"
    _write_status(status_path, repo_root)

    catalog = module._load_catalog(catalog_path)
    components = module._build_components(catalog, library_root)
    status_data = module._load_status(status_path)
    report = module.build_report(status_data, components)

    summary = report["summary"]
    assert summary["total_imported_components"] == 1
    assert summary["total_drifted_components"] == 1


def test_render_checklists_flags_missing_tests_and_ci():
    module = _import_module()
    report = {
        "repos": [
            {
                "name": "RepoA",
                "location": "C:\\RepoA",
                "signals": {"tests": False, "ci": False, "readme": True, "git": True},
                "missing_deployments": [],
                "drifted": [],
            },
            {
                "name": "RepoB",
                "location": "C:\\RepoB",
                "signals": {"tests": True, "ci": False, "readme": True, "git": True},
                "missing_deployments": [],
                "drifted": [],
            },
        ]
    }
    rendered = module._render_checklists(report)
    assert "Priority: Missing CI/Test Scaffolding" in rendered
    assert "- RepoA:" in rendered
    assert "- Add tests directory + baseline runner config" in rendered
    assert "- Add CI workflow for lint/test" in rendered
    assert "## RepoB" in rendered


def test_scan_imports_falls_back_without_rg(tmp_path: Path, monkeypatch):
    module = _import_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "app.py").write_text(
        "from library.components.utilities.demo import demo\n", encoding="utf-8"
    )

    def _raise(*_args, **_kwargs):
        raise OSError("rg not found")

    monkeypatch.setattr(module.subprocess, "run", _raise)
    hits = module._scan_imports(repo_root)
    assert ("utilities", "demo") in hits
