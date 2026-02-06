#!/usr/bin/env python3
"""
Catalog Update Script for Component Library

Updates catalog-index.json by scanning the components directory.
This is the source of truth for the library.

Usage:
    python update_catalog.py [--scan] [--stats]

Options:
    --scan   Scan components/ directory and add new components
    --stats  Print statistics only
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Use relative path from script location
LIBRARY_ROOT = Path(__file__).parent
CATALOG_FILE = LIBRARY_ROOT / "catalog-index.json"
LEGACY_CATALOG_FILE = LIBRARY_ROOT / "catalog.json"
COMPONENTS_DIR = LIBRARY_ROOT / "components"
PATTERNS_DIR = LIBRARY_ROOT / "patterns"


def load_catalog() -> dict:
    """Load the catalog from disk."""
    if CATALOG_FILE.exists():
        with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "version": "2.0.0",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_components": 0,
        "domains": {},
        "quick_lookup": {}
    }


def _collect_exports_for_location(location: str) -> list[str]:
    """Best-effort export discovery from component.json metadata."""
    path = LIBRARY_ROOT / location
    if path.is_file():
        return []
    metadata_file = path / "component.json"
    if not metadata_file.exists():
        return []
    try:
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    exports = metadata.get("exports", [])
    if isinstance(exports, list):
        return [item for item in exports if isinstance(item, str) and item]
    return []


def build_legacy_catalog(catalog: dict) -> dict:
    """Build legacy catalog.json with flattened component list."""
    components = []
    for domain_name, domain_data in catalog.get("domains", {}).items():
        for component in domain_data.get("components", []):
            location = component.get("location", "")
            components.append(
                {
                    "id": component.get("id"),
                    "name": component.get("name"),
                    "domain": domain_name,
                    "location": location,
                    "quality_score": component.get("quality_score"),
                    "exports": _collect_exports_for_location(location),
                }
            )

    return {
        "version": catalog.get("schema_version", catalog.get("version", "2.0.0")),
        "last_updated": catalog.get("last_updated"),
        "total_components": len(components),
        "components": components,
    }


def save_catalog(catalog: dict) -> None:
    """Save canonical and compatibility catalog files to disk."""
    catalog["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2)
    print(f"Saved catalog to {CATALOG_FILE}")

    legacy_catalog = build_legacy_catalog(catalog)
    with open(LEGACY_CATALOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(legacy_catalog, f, indent=2)
    print(f"Saved compatibility catalog to {LEGACY_CATALOG_FILE}")


def count_components(catalog: dict) -> int:
    """Count total components across all domains."""
    total = 0
    for domain_data in catalog.get("domains", {}).values():
        total += domain_data.get("count", len(domain_data.get("components", [])))
    return total


def get_all_component_ids(catalog: dict) -> set:
    """Get all component IDs from the catalog."""
    ids = set()
    for domain_data in catalog.get("domains", {}).values():
        for component in domain_data.get("components", []):
            ids.add(component.get("id"))
    return ids


def print_stats(catalog: dict) -> None:
    """Print catalog statistics."""
    total = count_components(catalog)
    domains = catalog.get("domains", {})

    print(f"\n=== Catalog Statistics ===")
    print(f"Version: {catalog.get('version', 'unknown')}")
    print(f"Last Updated: {catalog.get('last_updated', 'unknown')}")
    print(f"Total Components: {total}")
    print(f"Total Domains: {len(domains)}")
    print(f"\nComponents by Domain:")

    # Sort by count descending
    sorted_domains = sorted(domains.items(), key=lambda x: x[1].get("count", 0), reverse=True)
    for domain, data in sorted_domains:
        count = data.get("count", len(data.get("components", [])))
        print(f"  {domain}: {count}")


def scan_components(catalog: dict) -> dict:
    """Scan components directory for new components."""
    existing_ids = get_all_component_ids(catalog)
    new_count = 0

    # Scan components/ directory
    if COMPONENTS_DIR.exists():
        for domain_dir in COMPONENTS_DIR.iterdir():
            if not domain_dir.is_dir():
                continue

            domain_name = domain_dir.name

            # Initialize domain if not exists
            if domain_name not in catalog["domains"]:
                catalog["domains"][domain_name] = {
                    "count": 0,
                    "file": f"domains/{domain_name}.json",
                    "components": []
                }

            # Scan for component directories
            for component_dir in domain_dir.iterdir():
                if not component_dir.is_dir():
                    continue

                component_id = f"{domain_name}-{component_dir.name}".replace("_", "-")

                if component_id not in existing_ids:
                    # Add new component
                    new_component = {
                        "id": component_id,
                        "name": component_dir.name.replace("_", " ").title(),
                        "location": f"components/{domain_name}/{component_dir.name}/",
                        "quality_score": 70  # Default score
                    }
                    catalog["domains"][domain_name]["components"].append(new_component)
                    catalog["quick_lookup"][component_id] = {
                        "domain": domain_name,
                        "name": new_component["name"],
                        "location": new_component["location"]
                    }
                    existing_ids.add(component_id)
                    new_count += 1
                    print(f"  Added: {component_id}")

            # Update domain count
            catalog["domains"][domain_name]["count"] = len(catalog["domains"][domain_name]["components"])

    # Update total
    catalog["total_components"] = count_components(catalog)

    if new_count > 0:
        print(f"\nAdded {new_count} new components")
    else:
        print("\nNo new components found")

    return catalog


def main():
    """Main entry point."""
    catalog = load_catalog()

    if "--stats" in sys.argv:
        print_stats(catalog)
        return

    if "--scan" in sys.argv:
        print("Scanning for new components...")
        catalog = scan_components(catalog)
        save_catalog(catalog)

    print_stats(catalog)


if __name__ == "__main__":
    main()
