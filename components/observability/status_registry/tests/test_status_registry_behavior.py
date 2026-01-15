from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

MODULE_PATH = "components.observability.status_registry.status_registry"


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


def test_slugify_normalizes():
    module = _import_module()
    assert module.slugify(" Memory MCP ") == "memory-mcp"
    assert module.slugify("AI Exoskeleton 2026") == "ai-exoskeleton-2026"
    assert module.slugify("!!!") == "unknown"


def test_parse_project_table_extracts_rows(tmp_path: Path):
    module = _import_module()
    organ_map = tmp_path / "organ.md"
    organ_map.write_text(
        "\n".join(
            [
                "Intro",
                module.PROJECT_TABLE_HEADER,
                "|---|---|---|---|---|",
                "| 1 | Memory MCP | CNS | `D:\\Projects\\memory-mcp` | VERIFIED |",
                "| 2 | Context Cascade | Cortex | `C:\\Users\\17175\\context` | VERIFIED |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    projects = module.parse_project_table(organ_map)
    assert [p.name for p in projects] == ["Memory MCP", "Context Cascade"]
    assert projects[0].project_id == "memory-mcp"
    assert projects[0].location == "D:\\Projects\\memory-mcp"


def test_update_marked_section_replaces_block(tmp_path: Path):
    module = _import_module()
    path = tmp_path / "doc.md"
    path.write_text(
        "\n".join(
            [
                "# Doc",
                module.STATUS_START_MARKER,
                "old content",
                module.STATUS_END_MARKER,
                "tail",
            ]
        ),
        encoding="utf-8",
    )
    module.update_marked_section(path, "new content")
    updated = path.read_text(encoding="utf-8")
    assert "old content" not in updated
    assert "new content" in updated


def test_render_markdown_includes_summary_row():
    module = _import_module()
    data = {
        "summary": {
            "total_projects": 1,
            "git_repos": 1,
            "with_tests": 0,
            "with_ci": 1,
            "with_readme": 1,
        },
        "projects": [
            {
                "name": "memory-mcp",
                "role": "Central Nervous System",
                "status_percent": 90,
                "signals": {
                    "git": True,
                    "tests": False,
                    "ci": True,
                    "readme": True,
                    "last_commit_short": "abc123",
                },
            }
        ],
    }
    rendered = module.render_markdown(data)
    assert "Projects: 1 | Git: 1 | Tests: 0 | CI: 1 | README: 1" in rendered
    assert "| memory-mcp | Central Nervous System | 90% | yes | no | yes | yes | abc123 |" in rendered
