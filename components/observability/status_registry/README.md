# Status Registry Component

Canonical status registry for the AI Exoskeleton doc set. Generates a JSON
source of truth from repo metadata and renders a markdown summary that can be
embedded into docs.

## Features

- Parses the 18-project table from `2026-EXOSKELETON-ORGAN-MAP.md`
- Scans repo signals (git, tests, CI, README, last commit)
- Writes a canonical JSON registry and a rendered markdown summary
- Updates docs between `<!-- STATUS:START -->` and `<!-- STATUS:END -->` markers

## Installation

```python
from library.components.observability.status_registry import (
    build_registry,
    render_markdown,
    update_marked_section,
)
```

## Usage

### CLI

```bash
python C:\Users\17175\.claude\library\components\observability\status_registry\status_registry.py ^
  --organ-map C:\Users\17175\Desktop\2026-AI-EXOSKELETON\2026-EXOSKELETON-ORGAN-MAP.md ^
  --output-json C:\Users\17175\Desktop\2026-AI-EXOSKELETON\2026-EXOSKELETON-STATUS.json ^
  --output-md C:\Users\17175\Desktop\2026-AI-EXOSKELETON\2026-EXOSKELETON-STATUS.md ^
  --update-docs C:\Users\17175\Desktop\2026-AI-EXOSKELETON\README.md ^
  C:\Users\17175\Desktop\2026-AI-EXOSKELETON\2026-AI-EXOSKELETON-TODO.md ^
  C:\Users\17175\Desktop\2026-AI-EXOSKELETON\2026-IMPLEMENTATION-PLAN.md ^
  --update-repo-readmes ^
  --create-missing-readmes
```

### Python

```python
import json
from pathlib import Path
from library.components.observability.status_registry import (
    build_registry,
    render_markdown,
    update_marked_section,
)

organ_map = Path(r"C:\Users\17175\Desktop\2026-AI-EXOSKELETON\2026-EXOSKELETON-ORGAN-MAP.md")
output_json = Path(r"C:\Users\17175\Desktop\2026-AI-EXOSKELETON\2026-EXOSKELETON-STATUS.json")
output_md = Path(r"C:\Users\17175\Desktop\2026-AI-EXOSKELETON\2026-EXOSKELETON-STATUS.md")

registry = build_registry(organ_map, output_json)
output_json.write_text(json.dumps(registry, indent=2), encoding="utf-8")
rendered = render_markdown(registry)
output_md.write_text(rendered, encoding="utf-8")
update_marked_section(Path(r"C:\Users\17175\Desktop\2026-AI-EXOSKELETON\README.md"), rendered.strip())
```

## Notes

- Manual status values can be added in the JSON file and are preserved on
  subsequent runs.
- If markers are missing from a doc, the update step fails fast so the doc
  layout stays explicit.

## Source

Canonical status registry for the AI Exoskeleton doc set.
