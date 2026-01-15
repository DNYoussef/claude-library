from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


PROJECT_TABLE_HEADER = "| # | Project | Role | Location | Status |"
STATUS_START_MARKER = "<!-- STATUS:START -->"
STATUS_END_MARKER = "<!-- STATUS:END -->"


@dataclass
class RepoSignals:
    path: str
    exists: bool
    git: bool
    readme: bool
    tests: bool
    ci: bool
    last_commit: Optional[str] = None
    last_commit_short: Optional[str] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class ProjectStatus:
    project_id: str
    name: str
    role: str
    location: str
    status_percent: Optional[float] = None
    status_source: Optional[str] = None
    doc_claims: Dict[str, Optional[float]] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    signals: RepoSignals = field(
        default_factory=lambda: RepoSignals(
            path="",
            exists=False,
            git=False,
            readme=False,
            tests=False,
            ci=False,
        )
    )


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return cleaned.strip("-") or "unknown"


def _parse_table_row(line: str) -> Optional[Tuple[str, str, str, str, str]]:
    if not line.strip().startswith("|"):
        return None
    parts = [p.strip() for p in line.strip().strip("|").split("|")]
    if len(parts) < 5:
        return None
    idx, project, role, location, status = parts[:5]
    if idx == "#" or idx == "---":
        return None
    return idx, project, role, location, status


def parse_project_table(organ_map_path: Path) -> List[ProjectStatus]:
    content = organ_map_path.read_text(encoding="utf-8").splitlines()
    try:
        start_index = content.index(PROJECT_TABLE_HEADER)
    except ValueError:
        raise ValueError(f"Project table header not found in {organ_map_path}")

    projects: List[ProjectStatus] = []
    for line in content[start_index + 2 :]:
        row = _parse_table_row(line)
        if row is None:
            if line.strip() == "":
                break
            continue
        _, project, role, location, _ = row
        location = location.strip("`")
        project_id = slugify(project)
        projects.append(
            ProjectStatus(
                project_id=project_id,
                name=project,
                role=role,
                location=location,
                signals=RepoSignals(
                    path=location,
                    exists=False,
                    git=False,
                    readme=False,
                    tests=False,
                    ci=False,
                ),
            )
        )
    return projects


def _walk_with_depth(root: Path, max_depth: int) -> Iterable[Path]:
    root_depth = len(root.parts)
    for path in root.rglob("*"):
        if len(path.parts) - root_depth > max_depth:
            continue
        yield path


def detect_tests(root: Path, max_depth: int = 3) -> bool:
    test_dirs = {"tests", "test", "__tests__"}
    test_files = {"pytest.ini", "pyproject.toml", "jest.config.js", "jest.config.ts"}
    for path in _walk_with_depth(root, max_depth):
        if path.is_dir() and path.name in test_dirs:
            return True
        if path.is_file() and path.name in test_files:
            return True
    return False


def detect_ci(root: Path) -> bool:
    if (root / ".github" / "workflows").exists():
        return True
    ci_files = [".gitlab-ci.yml", "azure-pipelines.yml", ".circleci", "appveyor.yml"]
    return any((root / name).exists() for name in ci_files)


def detect_readme(root: Path) -> bool:
    return (root / "README.md").exists()


def get_git_last_commit(root: Path) -> Tuple[Optional[str], Optional[str]]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "log", "-1", "--format=%cI|%h"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None, None
    if result.returncode != 0:
        return None, None
    output = result.stdout.strip()
    if not output:
        return None, None
    if "|" in output:
        date, short_hash = output.split("|", 1)
        return date, short_hash
    return output, None


def scan_repo_signals(path: Path) -> RepoSignals:
    exists = path.exists()
    git = (path / ".git").exists() if exists else False
    readme = detect_readme(path) if exists else False
    tests = detect_tests(path) if exists else False
    ci = detect_ci(path) if exists else False
    last_commit, last_commit_short = (None, None)
    notes: List[str] = []
    if exists and git:
        last_commit, last_commit_short = get_git_last_commit(path)
    if exists and not git:
        notes.append("no_git")
    if exists and not tests:
        notes.append("no_tests")
    if exists and not ci:
        notes.append("no_ci")
    if not exists:
        notes.append("missing_path")
    return RepoSignals(
        path=str(path),
        exists=exists,
        git=git,
        readme=readme,
        tests=tests,
        ci=ci,
        last_commit=last_commit,
        last_commit_short=last_commit_short,
        notes=notes,
    )


def merge_existing_status(
    projects: List[ProjectStatus], existing_data: Dict[str, Any]
) -> None:
    existing_projects = {
        p.get("project_id"): p for p in existing_data.get("projects", [])
    }
    for project in projects:
        existing = existing_projects.get(project.project_id)
        if not existing:
            continue
        project.status_percent = existing.get("status_percent")
        project.status_source = existing.get("status_source")
        project.doc_claims = existing.get("doc_claims", {}) or {}
        project.tags = existing.get("tags", []) or []


def build_registry(
    organ_map_path: Path,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    projects = parse_project_table(organ_map_path)
    if output_path and output_path.exists():
        existing_data = json.loads(output_path.read_text(encoding="utf-8"))
        merge_existing_status(projects, existing_data)

    for project in projects:
        project.signals = scan_repo_signals(Path(project.location))

    summary = {
        "total_projects": len(projects),
        "git_repos": sum(1 for p in projects if p.signals.git),
        "with_tests": sum(1 for p in projects if p.signals.tests),
        "with_ci": sum(1 for p in projects if p.signals.ci),
        "with_readme": sum(1 for p in projects if p.signals.readme),
    }

    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "organ_map": str(organ_map_path),
        "summary": summary,
        "projects": [asdict(project) for project in projects],
    }


def write_json(output_path: Path, data: Dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def render_markdown(data: Dict[str, Any]) -> str:
    lines = []
    summary = data.get("summary", {})
    lines.append("Generated from repo metadata and canonical status registry.")
    lines.append("")
    lines.append(
        f"Projects: {summary.get('total_projects', 0)} | "
        f"Git: {summary.get('git_repos', 0)} | "
        f"Tests: {summary.get('with_tests', 0)} | "
        f"CI: {summary.get('with_ci', 0)} | "
        f"README: {summary.get('with_readme', 0)}"
    )
    lines.append("")
    lines.append("| Project | Role | Status % | Git | Tests | CI | README | Last Commit |")
    lines.append("|---------|------|----------|-----|-------|----|--------|-------------|")
    for project in data.get("projects", []):
        signals = project.get("signals", {})
        status_percent = project.get("status_percent")
        status_display = (
            f"{status_percent:.0f}%"
            if isinstance(status_percent, (int, float))
            else "TBD"
        )
        last_commit = signals.get("last_commit_short") or signals.get("last_commit") or "unknown"
        lines.append(
            "| {name} | {role} | {status} | {git} | {tests} | {ci} | {readme} | {last} |".format(
                name=project.get("name", "unknown"),
                role=project.get("role", "unknown"),
                status=status_display,
                git="yes" if signals.get("git") else "no",
                tests="yes" if signals.get("tests") else "no",
                ci="yes" if signals.get("ci") else "no",
                readme="yes" if signals.get("readme") else "no",
                last=last_commit,
            )
        )
    return "\n".join(lines) + "\n"


def render_project_markdown(project: Dict[str, Any], generated_at: str) -> str:
    signals = project.get("signals", {})
    status_percent = project.get("status_percent")
    status_display = (
        f"{status_percent:.0f}%"
        if isinstance(status_percent, (int, float))
        else "TBD"
    )
    status_source = project.get("status_source") or "manual"
    last_commit = signals.get("last_commit_short") or signals.get("last_commit") or "unknown"
    lines = [
        "Canonical status from `2026-EXOSKELETON-STATUS.json`.",
        "",
        f"Status: {status_display} (source: {status_source})",
        f"Registry refreshed: {generated_at}",
        (
            "Signals: "
            f"git={'yes' if signals.get('git') else 'no'}, "
            f"tests={'yes' if signals.get('tests') else 'no'}, "
            f"ci={'yes' if signals.get('ci') else 'no'}, "
            f"readme={'yes' if signals.get('readme') else 'no'}, "
            f"last_commit={last_commit}"
        ),
    ]
    return "\n".join(lines) + "\n"


def update_marked_section(path: Path, new_section: str) -> None:
    content = path.read_text(encoding="utf-8")
    if STATUS_START_MARKER not in content or STATUS_END_MARKER not in content:
        raise ValueError(f"Missing status markers in {path}")
    before, remainder = content.split(STATUS_START_MARKER, 1)
    _, after = remainder.split(STATUS_END_MARKER, 1)
    updated = (
        f"{before}{STATUS_START_MARKER}\n"
        f"{new_section}\n"
        f"{STATUS_END_MARKER}{after}"
    )
    path.write_text(updated, encoding="utf-8")


def update_project_readme(
    project: Dict[str, Any],
    generated_at: str,
    create_missing: bool = False,
) -> Optional[Path]:
    root = Path(project.get("location", ""))
    readme_path = root / "README.md"
    if not readme_path.exists():
        if not create_missing:
            return None
        title = project.get("name", "Project")
        readme_path.write_text(f"# {title}\n\n", encoding="utf-8")

    content = readme_path.read_text(encoding="utf-8")
    rendered = render_project_markdown(project, generated_at).strip()

    if STATUS_START_MARKER in content and STATUS_END_MARKER in content:
        update_marked_section(readme_path, rendered)
        return readme_path

    heading = "## Canonical Status\n\n"
    block = f"{heading}{STATUS_START_MARKER}\n{rendered}\n{STATUS_END_MARKER}\n"

    lines = content.splitlines()
    insert_at = 0
    for idx, line in enumerate(lines):
        if line.startswith("# "):
            insert_at = idx + 1
            break
    updated_lines = lines[:insert_at] + ["", block.strip(), ""] + lines[insert_at:]
    readme_path.write_text("\n".join(updated_lines).lstrip("\n"), encoding="utf-8")
    return readme_path


def update_repo_readmes(
    data: Dict[str, Any],
    create_missing: bool = False,
) -> List[Path]:
    generated_at = data.get("generated_at", datetime.now(timezone.utc).isoformat())
    updated: List[Path] = []
    for project in data.get("projects", []):
        path = update_project_readme(project, generated_at, create_missing=create_missing)
        if path is not None:
            updated.append(path)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate exoskeleton status registry and update docs."
    )
    parser.add_argument(
        "--organ-map",
        required=True,
        help="Path to 2026-EXOSKELETON-ORGAN-MAP.md",
    )
    parser.add_argument(
        "--output-json",
        required=True,
        help="Path to canonical status JSON file",
    )
    parser.add_argument(
        "--output-md",
        required=True,
        help="Path to rendered status markdown file",
    )
    parser.add_argument(
        "--update-docs",
        nargs="*",
        default=[],
        help="Doc paths to update between STATUS markers",
    )
    parser.add_argument(
        "--update-repo-readmes",
        action="store_true",
        help="Update each project README with a canonical status block.",
    )
    parser.add_argument(
        "--create-missing-readmes",
        action="store_true",
        help="Create missing README.md files when updating project readmes.",
    )
    args = parser.parse_args()

    organ_map = Path(args.organ_map)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    registry = build_registry(organ_map, output_json)
    write_json(output_json, registry)
    rendered = render_markdown(registry)
    output_md.write_text(rendered, encoding="utf-8")
    for doc in args.update_docs:
        update_marked_section(Path(doc), rendered.strip())
    if args.update_repo_readmes:
        update_repo_readmes(registry, create_missing=args.create_missing_readmes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
