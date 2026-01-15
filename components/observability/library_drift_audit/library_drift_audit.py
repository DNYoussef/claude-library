from __future__ import annotations

import argparse
import hashlib
import json
import re
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


TEXT_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".md",
    ".yml",
    ".yaml",
    ".json",
}
IMPORT_REGEX = re.compile(r"library\.components\.([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_]+)")
IGNORE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    ".tox",
    "__pycache__",
    "site-packages",
    ".mypy_cache",
    ".pytest_cache",
    ".cache",
}
MAX_FILE_BYTES = 1_000_000


@dataclass
class Component:
    component_id: str
    domain: str
    location: str
    path: Path
    name: str
    is_dir: bool
    parent_dir: Optional[str] = None


@dataclass
class DriftResult:
    component_id: str
    component_name: str
    location: str
    import_used: bool
    copy_found: bool
    drifted: bool
    missing_files: List[str]
    extra_files: List[str]
    mismatched_files: List[str]
    matched_path: Optional[str]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _iter_files(root: Path, max_depth: int = 4) -> Iterable[Path]:
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        rel_parts = Path(dirpath).relative_to(root).parts
        if len(rel_parts) > max_depth:
            dirnames[:] = []
            continue
        filtered: List[str] = []
        for d in dirnames:
            lower = d.lower()
            if d in IGNORE_DIRS:
                continue
            if "venv" in lower or "site-packages" in lower:
                continue
            filtered.append(d)
        dirnames[:] = filtered
        current_dir = Path(dirpath)
        yield current_dir
        for filename in filenames:
            yield current_dir / filename


def _load_catalog(catalog_path: Path) -> Dict:
    return json.loads(catalog_path.read_text(encoding="utf-8-sig"))


def _load_status(status_path: Path) -> Dict:
    return json.loads(status_path.read_text(encoding="utf-8"))


def _library_root(catalog_path: Path) -> Path:
    return catalog_path.parent


def _build_components(catalog: Dict, library_root: Path) -> List[Component]:
    components: List[Component] = []
    for comp in catalog.get("components", []):
        location = comp.get("location")
        if not location:
            continue
        path = (library_root / location).resolve()
        name = Path(location).name
        is_dir = path.is_dir()
        parent_dir = Path(location).parent.name if not is_dir else None
        components.append(
            Component(
                component_id=comp.get("id", name),
                domain=comp.get("domain", "unknown"),
                location=location,
                path=path,
                name=name if is_dir else Path(location).stem,
                is_dir=is_dir,
                parent_dir=parent_dir,
            )
        )
    return components


def _scan_imports(repo_root: Path) -> Set[Tuple[str, str]]:
    hits: Set[Tuple[str, str]] = set()
    rg_cmd = [
        "rg",
        "-o",
        "-N",
        "library\\.components\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_]+",
        str(repo_root),
    ]
    for ext in TEXT_EXTENSIONS:
        rg_cmd.extend(["-g", f"*{ext}"])
    for ignore_dir in IGNORE_DIRS:
        rg_cmd.extend(["-g", f"!**/{ignore_dir}/**"])
    try:
        result = subprocess.run(
            rg_cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode in (0, 1):
            for line in result.stdout.splitlines():
                match = IMPORT_REGEX.search(line)
                if match:
                    hits.add(match.group(1, 2))
            return hits
    except OSError:
        pass

    for path in _iter_files(repo_root, max_depth=6):
        if not path.is_file() or path.suffix not in TEXT_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in IMPORT_REGEX.findall(content):
            hits.add(match)
    return hits


def _index_repo_paths(repo_root: Path) -> Tuple[Dict[str, List[Path]], Dict[str, List[Path]]]:
    dir_index: Dict[str, List[Path]] = {}
    file_index: Dict[str, List[Path]] = {}
    for path in _iter_files(repo_root, max_depth=5):
        if path.is_dir():
            dir_index.setdefault(path.name, []).append(path)
        elif path.is_file():
            file_index.setdefault(path.name, []).append(path)
    return dir_index, file_index


def _diff_directory(source_dir: Path, target_dir: Path) -> Tuple[List[str], List[str], List[str]]:
    missing: List[str] = []
    extra: List[str] = []
    mismatched: List[str] = []

    source_files = [p for p in source_dir.rglob("*") if p.is_file()]
    target_files = [p for p in target_dir.rglob("*") if p.is_file()]
    target_rel_map = {p.relative_to(target_dir).as_posix(): p for p in target_files}

    for src in source_files:
        rel = src.relative_to(source_dir).as_posix()
        dst = target_rel_map.get(rel)
        if dst is None:
            missing.append(rel)
            continue
        if _sha256(src) != _sha256(dst):
            mismatched.append(rel)

    source_rel_set = {p.relative_to(source_dir).as_posix() for p in source_files}
    for dst in target_files:
        rel = dst.relative_to(target_dir).as_posix()
        if rel not in source_rel_set:
            extra.append(rel)

    return missing, extra, mismatched


def _diff_file(source_file: Path, target_file: Path) -> Tuple[List[str], List[str], List[str]]:
    if not target_file.exists():
        return [source_file.name], [], []
    if _sha256(source_file) != _sha256(target_file):
        return [], [], [source_file.name]
    return [], [], []


def _match_component_copy(
    component: Component,
    repo_root: Path,
    dir_index: Dict[str, List[Path]],
    file_index: Dict[str, List[Path]],
) -> Tuple[Optional[Path], List[str], List[str], List[str]]:
    if component.is_dir:
        candidates = dir_index.get(component.name, [])
        best: Optional[Path] = None
        best_score = -1
        best_missing: List[str] = []
        best_extra: List[str] = []
        best_mismatch: List[str] = []
        for candidate in candidates:
            missing, extra, mismatched = _diff_directory(component.path, candidate)
            score = -(len(missing) + len(mismatched) + len(extra))
            if score > best_score:
                best_score = score
                best = candidate
                best_missing = missing
                best_extra = extra
                best_mismatch = mismatched
        if best is None:
            return None, [], [], []
        return best, best_missing, best_extra, best_mismatch

    candidates = file_index.get(component.path.name, [])
    if not candidates:
        return None, [], [], []
    if component.parent_dir:
        narrowed = [
            path
            for path in candidates
            if component.parent_dir in {part for part in path.parts}
        ]
        candidates = narrowed
        if not candidates:
            return None, [], [], []
    best = candidates[0]
    missing, extra, mismatched = _diff_file(component.path, best)
    return best, missing, extra, mismatched


def _repo_signals(repo_root: Path) -> Dict[str, bool]:
    tests = any((repo_root / name).exists() for name in ["tests", "test", "__tests__"])
    ci = (repo_root / ".github" / "workflows").exists() or any(
        (repo_root / name).exists()
        for name in [".gitlab-ci.yml", "azure-pipelines.yml", ".circleci", "appveyor.yml"]
    )
    readme = (repo_root / "README.md").exists()
    git = (repo_root / ".git").exists()
    return {"tests": tests, "ci": ci, "readme": readme, "git": git}


def audit_repo(
    repo_root: Path,
    components: List[Component],
    import_hits: Set[Tuple[str, str]],
) -> List[DriftResult]:
    dir_index, file_index = _index_repo_paths(repo_root)
    results: List[DriftResult] = []
    for component in components:
        import_used = (component.domain, component.name) in import_hits
        matched_path, missing, extra, mismatched = _match_component_copy(
            component, repo_root, dir_index, file_index
        )
        copy_found = matched_path is not None
        drifted = bool(missing or extra or mismatched)
        results.append(
            DriftResult(
                component_id=component.component_id,
                component_name=component.name,
                location=component.location,
                import_used=import_used,
                copy_found=copy_found,
                drifted=drifted,
                missing_files=sorted(missing),
                extra_files=sorted(extra),
                mismatched_files=sorted(mismatched),
                matched_path=str(matched_path) if matched_path else None,
            )
        )
    return results


def build_report(
    status_data: Dict,
    components: List[Component],
) -> Dict:
    report = {"repos": [], "summary": {}}
    total_drifted = 0
    total_missing = 0
    total_imported = 0

    for repo in status_data.get("projects", []):
        repo_root = Path(repo.get("location", ""))
        if not repo_root.exists():
            report["repos"].append(
                {
                    "name": repo.get("name"),
                    "location": str(repo_root),
                    "error": "missing_path",
                }
            )
            continue
        import_hits = _scan_imports(repo_root)
        results = audit_repo(repo_root, components, import_hits)
        drifted = [r for r in results if r.drifted]
        missing = [r for r in results if r.import_used and not r.copy_found]
        imported = [r for r in results if r.import_used]
        signals = _repo_signals(repo_root)
        report["repos"].append(
            {
                "name": repo.get("name"),
                "location": str(repo_root),
                "signals": signals,
                "imports": sorted([f"{d}.{c}" for d, c in import_hits]),
                "drifted": drifted,
                "missing_deployments": missing,
                "imported": imported,
            }
        )
        total_drifted += len(drifted)
        total_missing += len(missing)
        total_imported += len(imported)

    report["summary"] = {
        "total_repos": len(report["repos"]),
        "components_scanned": len(components),
        "total_imported_components": total_imported,
        "total_drifted_components": total_drifted,
        "total_missing_deployments": total_missing,
    }
    return report


def _render_drift_report(report: Dict) -> str:
    lines: List[str] = []
    summary = report.get("summary", {})
    lines.append("# Library Drift Audit")
    lines.append("")
    lines.append(
        "Components scanned: {components_scanned} | Imported: {total_imported_components} | "
        "Drifted: {total_drifted_components} | Missing deployments: {total_missing_deployments}".format(
            **summary
        )
    )
    lines.append("")
    for repo in report.get("repos", []):
        lines.append(f"## {repo.get('name')}")
        lines.append(f"Location: `{repo.get('location')}`")
        if repo.get("error"):
            lines.append(f"Error: {repo['error']}")
            lines.append("")
            continue
        signals = repo.get("signals", {})
        lines.append(
            "Signals: "
            f"git={'yes' if signals.get('git') else 'no'}, "
            f"tests={'yes' if signals.get('tests') else 'no'}, "
            f"ci={'yes' if signals.get('ci') else 'no'}, "
            f"readme={'yes' if signals.get('readme') else 'no'}"
        )
        imports = repo.get("imports", [])
        if imports:
            lines.append("Imports:")
            for item in imports:
                lines.append(f"- {item}")
        drifted = repo.get("drifted", [])
        if drifted:
            lines.append("Drifted components:")
            for item in drifted:
                lines.append(
                    f"- {item.component_id} ({item.location}) -> {item.matched_path or 'missing'}"
                )
                if item.mismatched_files:
                    lines.append(f"  mismatched: {', '.join(item.mismatched_files)}")
                if item.missing_files:
                    lines.append(f"  missing: {', '.join(item.missing_files)}")
                if item.extra_files:
                    lines.append(f"  extra: {', '.join(item.extra_files)}")
        missing = repo.get("missing_deployments", [])
        if missing:
            lines.append("Missing deployments (import used but no copy found):")
            for item in missing:
                lines.append(f"- {item.component_id} ({item.location})")
        lines.append("")
    return "\n".join(lines)


def _render_checklists(report: Dict) -> str:
    lines: List[str] = []
    lines.append("# Deployment Checklists")
    lines.append("")
    lagging = []
    for repo in report.get("repos", []):
        signals = repo.get("signals", {})
        location = (repo.get("location") or "").lower()
        if repo.get("name") == "Library" or ".claude\\library" in location:
            continue
        if signals and (not signals.get("tests") or not signals.get("ci")):
            score = 0
            if not signals.get("tests"):
                score += 2
            if not signals.get("ci"):
                score += 1
            lagging.append((score, repo))

    lagging_sorted = [r for _, r in sorted(lagging, key=lambda item: item[0], reverse=True)]
    priority = lagging_sorted[:7]
    remaining = lagging_sorted[7:]

    if priority:
        lines.append("## Priority: Missing CI/Test Scaffolding")
        for repo in priority:
            signals = repo.get("signals", {})
            name = repo.get("name")
            lines.append(f"- {name}:")
            if not signals.get("tests"):
                lines.append("  - Add tests directory + baseline runner config")
            if not signals.get("ci"):
                lines.append("  - Add CI workflow for lint/test")
        lines.append("")
    if remaining:
        lines.append("## Additional CI/Test Gaps")
        for repo in remaining:
            signals = repo.get("signals", {})
            name = repo.get("name")
            lines.append(f"- {name}:")
            if not signals.get("tests"):
                lines.append("  - Add tests directory + baseline runner config")
            if not signals.get("ci"):
                lines.append("  - Add CI workflow for lint/test")
        lines.append("")

    for repo in report.get("repos", []):
        lines.append(f"## {repo.get('name')}")
        lines.append(f"Location: `{repo.get('location')}`")
        if repo.get("error"):
            lines.append(f"- Fix missing path: {repo['error']}")
            lines.append("")
            continue
        signals = repo.get("signals", {})
        if not signals.get("readme"):
            lines.append("- Add README")
        if not signals.get("git"):
            lines.append("- Initialize git")
        if not signals.get("tests"):
            lines.append("- Add tests scaffold")
        if not signals.get("ci"):
            lines.append("- Add CI workflow")
        missing = repo.get("missing_deployments", [])
        if missing:
            lines.append("- Deploy missing library components:")
            for item in missing:
                lines.append(f"  - {item.component_id} ({item.location})")
        drifted = repo.get("drifted", [])
        if drifted:
            lines.append("- Resolve drifted components:")
            for item in drifted:
                lines.append(f"  - {item.component_id} -> {item.matched_path or 'missing'}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Library drift audit.")
    parser.add_argument("--catalog", required=True, help="Path to catalog.json")
    parser.add_argument("--status", required=True, help="Path to status JSON")
    parser.add_argument("--output-report", required=True, help="Markdown report path")
    parser.add_argument(
        "--output-checklists", required=True, help="Markdown checklist path"
    )
    args = parser.parse_args()

    catalog_path = Path(args.catalog)
    status_path = Path(args.status)
    library_root = _library_root(catalog_path)
    catalog = _load_catalog(catalog_path)
    components = _build_components(catalog, library_root)
    status_data = _load_status(status_path)
    report = build_report(status_data, components)

    Path(args.output_report).write_text(_render_drift_report(report), encoding="utf-8")
    Path(args.output_checklists).write_text(
        _render_checklists(report), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
