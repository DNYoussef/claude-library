import argparse
import json
import sys
from pathlib import Path


def load_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_valid_exports(exports) -> bool:
    if not isinstance(exports, list):
        return False
    return all(isinstance(item, str) and item for item in exports)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate .claude/library/catalog.json for path + exports correctness."
    )
    parser.add_argument(
        "--catalog",
        default="catalog.json",
        help="Path to catalog.json (default: catalog.json in cwd)",
    )
    parser.add_argument(
        "--strict-deprecated",
        action="store_true",
        help="Treat deprecated components as errors.",
    )
    args = parser.parse_args()

    catalog_path = Path(args.catalog).resolve()
    if not catalog_path.exists():
        print(f"ERROR: catalog not found: {catalog_path}")
        return 2

    data = load_catalog(catalog_path)
    components = data.get("components", [])
    root = catalog_path.parent

    errors = []
    warnings = []

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

        if not is_valid_exports(exports) or len(exports) == 0:
            errors.append(f"{cid}: exports missing or empty")

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
