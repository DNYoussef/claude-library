import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_valid_exports(exports) -> bool:
    if not isinstance(exports, list):
        return False
    return all(isinstance(item, str) and item for item in exports)


def extract_components(data: dict[str, Any]) -> list[dict[str, Any]]:
    # Legacy schema: {"components": [...]}
    if isinstance(data.get("components"), list):
        return data["components"]

    # Current schema: {"domains": {"name": {"components": [...]}}}
    domains = data.get("domains")
    if isinstance(domains, dict):
        flattened: list[dict[str, Any]] = []
        for domain_name, domain_data in domains.items():
            if not isinstance(domain_data, dict):
                continue
            for comp in domain_data.get("components", []):
                if isinstance(comp, dict):
                    item = dict(comp)
                    item.setdefault("domain", domain_name)
                    flattened.append(item)
        return flattened

    return []


def has_entrypoint(path: Path) -> bool:
    if path.is_file():
        return True
    if not path.is_dir():
        return False
    return any(
        (path / name).exists()
        for name in (
            "__init__.py",
            "index.ts",
            "index.tsx",
            "component.json",
            "main.py",
            "module.py",
            "service.py",
            "client.py",
        )
    )


def main() -> int:
    default_catalog = "catalog-index.json" if Path("catalog-index.json").exists() else "catalog.json"
    parser = argparse.ArgumentParser(
        description="Validate component catalog path and export metadata."
    )
    parser.add_argument(
        "--catalog",
        default=default_catalog,
        help=f"Path to catalog file (default: {default_catalog})",
    )
    parser.add_argument(
        "--strict-deprecated",
        action="store_true",
        help="Treat deprecated components as errors.",
    )
    parser.add_argument(
        "--require-exports",
        action="store_true",
        help="Require explicit exports metadata for each component.",
    )
    args = parser.parse_args()

    catalog_path = Path(args.catalog).resolve()
    if not catalog_path.exists():
        print(f"ERROR: catalog not found: {catalog_path}")
        return 2

    data = load_catalog(catalog_path)
    components = extract_components(data)
    root = catalog_path.parent
    requires_exports = args.require_exports or isinstance(data.get("components"), list)

    errors = []
    warnings = []

    if not components:
        errors.append("No components found in catalog")

    for comp in components:
        cid = comp.get("id", "<missing id>")
        loc = comp.get("location")
        exports = comp.get("exports")

        if not loc:
            errors.append(f"{cid}: missing location")
        else:
            path = root / loc
            if not path.exists():
                errors.append(f"{cid}: location not found -> {loc}")
            elif not has_entrypoint(path):
                warnings.append(f"{cid}: no obvious entrypoint in location -> {loc}")

        if exports is None:
            if requires_exports:
                warnings.append(f"{cid}: exports not declared")
        elif not is_valid_exports(exports) or len(exports) == 0:
            errors.append(f"{cid}: exports invalid or empty")

        if comp.get("status") == "deprecated":
            msg = f"{cid}: deprecated"
            if args.strict_deprecated:
                errors.append(msg)
            else:
                warnings.append(msg)

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"- {w}")

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("OK: catalog validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
