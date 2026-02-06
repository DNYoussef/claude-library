"""
Restructure catalog.json into lightweight index + domain sub-files
"""
import json
from pathlib import Path
from datetime import datetime

LIBRARY_ROOT = Path(r"C:\Users\17175\.claude\library")
CATALOG_PATH = LIBRARY_ROOT / "catalog.json"

def main():
    # Load existing catalog
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Group by domain
    domains = {}
    for comp in catalog["components"]:
        domain = comp.get("domain", "uncategorized")
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(comp)

    # Create lightweight index
    index = {
        "version": "2.0.0",
        "last_updated": datetime.now().isoformat(),
        "total_components": len(catalog["components"]),
        "domains": {},
        "quick_lookup": {}
    }

    # Build index and domain files
    for domain, components in sorted(domains.items()):
        # Add to index
        index["domains"][domain] = {
            "count": len(components),
            "file": f"domains/{domain}.json",
            "components": []
        }

        for comp in components:
            # Lightweight entry for index
            index["domains"][domain]["components"].append({
                "id": comp["id"],
                "name": comp["name"],
                "location": comp.get("location", ""),
                "quality_score": comp.get("quality_score", 0)
            })

            # Quick lookup by id
            index["quick_lookup"][comp["id"]] = {
                "domain": domain,
                "name": comp["name"],
                "location": comp.get("location", "")
            }

        # Write domain file with full details
        domain_dir = LIBRARY_ROOT / "domains"
        domain_dir.mkdir(exist_ok=True)

        domain_file = {
            "domain": domain,
            "count": len(components),
            "components": components
        }

        with open(domain_dir / f"{domain}.json", "w", encoding="utf-8") as f:
            json.dump(domain_file, f, indent=2)

        print(f"  {domain}: {len(components)} components")

    # Write lightweight index
    with open(LIBRARY_ROOT / "catalog-index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    # Rename old catalog
    backup_path = LIBRARY_ROOT / "catalog-full-backup.json"
    if not backup_path.exists():
        CATALOG_PATH.rename(backup_path)
        print(f"\nBackup: catalog.json -> catalog-full-backup.json")

    # Print summary
    print(f"\nCreated catalog-index.json ({len(catalog['components'])} components)")
    print(f"Domain files in: {LIBRARY_ROOT / 'domains'}/")

    # Show token estimate
    index_size = len(json.dumps(index))
    print(f"\nIndex size: ~{index_size // 4} tokens (was ~37K)")

if __name__ == "__main__":
    main()
