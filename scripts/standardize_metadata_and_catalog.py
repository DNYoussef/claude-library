from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog-index.json"
DOMAINS_DIR = ROOT / "domains"


def normalize_location(location: str) -> str:
    p = Path(location)
    if p.suffix:
        p = p.parent
    loc = p.as_posix().strip("/")
    return f"{loc}/"


def sanitize_exports(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        candidate = value.strip()
        match = re.match(r"[A-Za-z_][A-Za-z0-9_]*", candidate)
        if not match:
            continue
        name = match.group(0)
        if name not in seen:
            cleaned.append(name)
            seen.add(name)
    return cleaned


def exports_from_python_test(test_path: Path) -> list[str]:
    try:
        tree = ast.parse(test_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    exports: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "EXPORTS":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for element in node.value.elts:
                            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                                exports.append(element.value)
    return sanitize_exports(exports)


def exports_from_tests(component_dir: Path) -> list[str]:
    for test_path in sorted(component_dir.glob("tests/test_*.py")):
        exports = exports_from_python_test(test_path)
        if exports:
            return exports

    ts_patterns = [
        re.compile(r"exportsList\s*=\s*\[(.*?)\]", re.S),
        re.compile(r"EXPORTS\s*=\s*\[(.*?)\]", re.S),
    ]
    for test_path in sorted(component_dir.glob("*.test.ts")) + sorted(component_dir.glob("tests/*.test.ts")):
        text = test_path.read_text(encoding="utf-8", errors="ignore")
        for pattern in ts_patterns:
            match = pattern.search(text)
            if not match:
                continue
            raw = match.group(1)
            names = re.findall(r"['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]", raw)
            names = sanitize_exports(names)
            if names:
                return names
    return []


def exports_from_python_all(component_dir: Path) -> list[str]:
    init_path = component_dir / "__init__.py"
    if not init_path.exists():
        return []
    try:
        tree = ast.parse(init_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        names = [
                            elt.value
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                        ]
                        return sanitize_exports(names)
    return []


def exports_from_typescript_index(component_dir: Path) -> list[str]:
    for index_name in ("index.ts", "index.tsx"):
        index_path = component_dir / index_name
        if not index_path.exists():
            continue
        text = index_path.read_text(encoding="utf-8", errors="ignore")
        exports: list[str] = []

        for body in re.findall(r"export\s*\{(.*?)\}\s*from", text, re.S):
            parts = [part.strip() for part in body.split(",")]
            for part in parts:
                part = re.sub(r"\btype\b", "", part).strip()
                if not part:
                    continue
                if " as " in part:
                    part = part.split(" as ", 1)[0].strip()
                exports.append(part)

        for name in re.findall(r"export\s+(?:const|function|class|type|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)", text):
            exports.append(name)

        exports = sanitize_exports(exports)
        if exports:
            return exports

    return []


def exports_from_file(file_path: Path) -> list[str]:
    if not file_path.exists():
        return []
    if file_path.suffix == ".py":
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        names: list[str] = []
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    names.append(node.name)
        return sanitize_exports(names)
    if file_path.suffix in {".ts", ".tsx"}:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        names = re.findall(r"export\s+(?:const|function|class|type|interface|enum)\s+([A-Za-z_][A-Za-z0-9_]*)", text)
        return sanitize_exports(names)
    return []


def select_exports(component_dir: Path, raw_path: Path, fallback: list[str]) -> list[str]:
    for producer in (
        lambda: exports_from_tests(component_dir),
        lambda: exports_from_python_all(component_dir),
        lambda: exports_from_typescript_index(component_dir),
        lambda: exports_from_file(raw_path),
    ):
        exports = producer()
        if exports:
            return exports
    return sanitize_exports(fallback)


def load_domain_component_map() -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    if not DOMAINS_DIR.exists():
        return mapping

    for domain_file in DOMAINS_DIR.glob("*.json"):
        try:
            data = json.loads(domain_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        for component in data.get("components", []):
            cid = component.get("id")
            if isinstance(cid, str):
                mapping[cid] = component
    return mapping


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    domain_component_map = load_domain_component_map()

    changed_locations = 0
    created_component_json = 0

    for domain_name, domain_data in catalog.get("domains", {}).items():
        for component in domain_data.get("components", []):
            cid = component["id"]
            original_location = component["location"]
            normalized_location = normalize_location(original_location)
            if normalized_location != original_location:
                component["location"] = normalized_location
                changed_locations += 1

            quick_entry = catalog.get("quick_lookup", {}).get(cid)
            if isinstance(quick_entry, dict):
                quick_entry["location"] = normalized_location

            raw_path = ROOT / original_location
            component_dir = ROOT / normalized_location
            component_dir.mkdir(parents=True, exist_ok=True)

            existing_metadata_path = component_dir / "component.json"
            existing_metadata: dict[str, Any] = {}
            if existing_metadata_path.exists():
                try:
                    existing_metadata = json.loads(existing_metadata_path.read_text(encoding="utf-8"))
                except Exception:
                    existing_metadata = {}

            domain_metadata = domain_component_map.get(cid, {})
            fallback_exports = domain_metadata.get("exports", []) if isinstance(domain_metadata, dict) else []
            if not isinstance(fallback_exports, list):
                fallback_exports = []

            exports = select_exports(component_dir, raw_path, [str(item) for item in fallback_exports])

            merged = {}
            merged.update(domain_metadata if isinstance(domain_metadata, dict) else {})
            merged.update(existing_metadata)
            merged.update(
                {
                    "id": cid,
                    "name": component.get("name", merged.get("name", cid)),
                    "domain": domain_name,
                    "location": normalized_location,
                    "quality_score": component.get("quality_score", merged.get("quality_score", 0)),
                    "exports": exports,
                }
            )
            if "description" not in merged:
                merged["description"] = f"Reusable component for {domain_name}."
            if "version" not in merged:
                merged["version"] = "1.0.0"

            if not existing_metadata_path.exists():
                created_component_json += 1

            existing_metadata_path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")

    # Keep domain files in sync with normalized locations.
    for domain_file in DOMAINS_DIR.glob("*.json"):
        try:
            data = json.loads(domain_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        modified = False
        for component in data.get("components", []):
            cid = component.get("id")
            if not isinstance(cid, str):
                continue
            quick = catalog.get("quick_lookup", {}).get(cid)
            if isinstance(quick, dict):
                new_location = quick.get("location")
                if isinstance(new_location, str) and component.get("location") != new_location:
                    component["location"] = new_location
                    modified = True

            target_meta = ROOT / component.get("location", "") / "component.json"
            if target_meta.exists():
                try:
                    meta = json.loads(target_meta.read_text(encoding="utf-8"))
                except Exception:
                    meta = {}
                exports = meta.get("exports")
                if isinstance(exports, list) and component.get("exports") != exports:
                    component["exports"] = exports
                    modified = True

        if modified:
            domain_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    CATALOG_PATH.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

    print(f"normalized_locations={changed_locations}")
    print(f"created_component_json={created_component_json}")


if __name__ == "__main__":
    main()
