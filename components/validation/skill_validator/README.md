# Skill Validator

Validate and index SKILL.md files against Claude Code specifications.

Extracted from the Context Cascade plugin for standalone use.

## Features

- **YAML Frontmatter Validation**: Validates required fields (`name`, `description`) against Claude Code specs
- **Trigger Pattern Extraction**: Parses `TRIGGER_POSITIVE` blocks for skill routing
- **Claude Code Compliance**: Enforces spec limits (64-char names, 1024-char descriptions, no XML tags)
- **JSON Index Generation**: Creates searchable indexes for skill discovery
- **PyYAML Optional**: Falls back to regex parser if PyYAML is not installed

## Installation

```bash
# Optional: Install PyYAML for better YAML parsing
pip install pyyaml
```

## Quick Start

### Validation

```python
from skill_validator import SkillValidator

# Validate all skills in a directory
validator = SkillValidator("/path/to/skills")
total, passed, failed = validator.validate_all()

# Print summary
validator.print_summary()

# Generate JSON report
validator.generate_json_report("validation-report.json")
```

### Indexing

```python
from skill_validator import SkillIndexer

# Build searchable index
indexer = SkillIndexer("/path/to/skills")
index = indexer.build_index(verbose=True)

# Write to file
indexer.write_index("skill-index.json")

# Search by keyword
matches = indexer.search_by_keyword("debug")
print(f"Skills matching 'debug': {matches}")
```

### Single File Validation

```python
from skill_validator import validate_single_file
from pathlib import Path

result = validate_single_file(Path("/path/to/SKILL.md"))
if result.valid:
    print(f"Valid: {result.skill_name}")
else:
    print(f"Invalid: {result.errors}")
```

## CLI Usage

### Validate Skills

```bash
# Basic validation
python -m skill_validator.skill_validator /path/to/skills

# Verbose output
python -m skill_validator.skill_validator /path/to/skills -v

# Generate JSON report
python -m skill_validator.skill_validator /path/to/skills --report report.json
```

### Build Index

```bash
# Basic indexing
python -m skill_validator.skill_indexer /path/to/skills

# Custom output file
python -m skill_validator.skill_indexer /path/to/skills -o my-index.json

# Verbose output
python -m skill_validator.skill_indexer /path/to/skills -v
```

## Claude Code Specifications

The validator enforces these Claude Code requirements:

| Field | Requirement |
|-------|-------------|
| `name` | Required, max 64 chars, lowercase letters/numbers/hyphens only |
| `description` | Required, max 1024 chars, no XML tags |

### Best Practices (Warnings)

- Description should include usage triggers (e.g., "Use when...")
- YAML should use spaces, not tabs
- Markdown content should follow frontmatter

## SKILL.md Format

```markdown
---
name: my-skill-name
description: Short description of when to use this skill. Use when debugging.
version: 1.0.0
category: delivery
tags:
  - debug
  - troubleshoot
---

# My Skill

Detailed instructions...

## When to Use

- Debugging issues
- Troubleshooting errors

## TRIGGER_POSITIVE

[define|neutral] TRIGGER_POSITIVE := {
  keywords: ["debug", "troubleshoot", "fix", "error"],
  context: "Use for debugging and troubleshooting"
}
```

## API Reference

### SkillValidator

```python
class SkillValidator:
    """Validates SKILL.md files against Claude Code specifications."""

    def __init__(self, skills_dir: Path):
        """Initialize with skills directory."""

    def find_all_skills(self) -> List[Path]:
        """Find all SKILL.md files."""

    def validate_skill(self, skill_file: Path) -> ValidationResult:
        """Validate a single file."""

    def validate_all(self) -> Tuple[int, int, int]:
        """Validate all skills. Returns (total, passed, failed)."""

    def print_summary(self):
        """Print validation summary."""

    def generate_json_report(self, output_file: Path) -> Dict:
        """Generate JSON report."""

    @property
    def yaml_available(self) -> bool:
        """Check if PyYAML is available."""
```

### SkillIndexer

```python
class SkillIndexer:
    """Builds searchable index from SKILL.md files."""

    def __init__(self, skills_dir: Path):
        """Initialize with skills directory."""

    def build_index(self, additional_dirs=None, verbose=False) -> Dict:
        """Build complete index."""

    def write_index(self, output_path: Path):
        """Write index to JSON file."""

    def search_by_keyword(self, keyword: str) -> List[str]:
        """Find skills matching keyword."""

    def search_by_keywords(self, keywords: List[str]) -> Dict[str, int]:
        """Find skills with scoring."""

    def get_skills_by_category(self, category: str) -> List[str]:
        """Get skills in category."""

    @property
    def yaml_available(self) -> bool:
        """Check if PyYAML is available."""
```

### ValidationResult

```python
@dataclass
class ValidationResult:
    skill_path: str      # Path to SKILL.md file
    skill_name: str      # Extracted skill name
    valid: bool          # Whether validation passed
    errors: List[str]    # Error messages
    warnings: List[str]  # Warning messages
    info: Dict[str, Any] # Additional metadata
```

### SkillData

```python
@dataclass
class SkillData:
    name: str                          # Skill name
    path: str                          # Relative path
    category: str                      # Category from path
    description: str                   # Skill description
    triggers: List[str]                # Positive trigger keywords
    negative_triggers: List[str]       # Negative trigger keywords
    files: List[str]                   # Supporting files
    tags: List[str]                    # Tags from frontmatter
    trigger_positive_raw: Optional[str] # Raw TRIGGER_POSITIVE block
```

## Exported Functions

| Function | Purpose |
|----------|---------|
| `validate_single_file(path)` | Validate one SKILL.md file |
| `parse_yaml_safe(text)` | Parse YAML with fallback |
| `parse_yaml_fallback(text)` | Regex-based YAML parser |
| `parse_yaml_frontmatter(content)` | Extract frontmatter from markdown |
| `extract_trigger_positive(content)` | Extract TRIGGER_POSITIVE block |
| `extract_section(content, name)` | Extract markdown section |
| `extract_keywords(text)` | Extract keywords from text |

## Constants

| Constant | Purpose |
|----------|---------|
| `STOPWORDS` | Words filtered from keyword extraction |
| `DEFAULT_CATEGORY_KEYWORDS` | Category routing keywords |
| `YAML_AVAILABLE` | Whether PyYAML is installed |

## Source

Extracted from:
- `C:\Users\17175\claude-code-plugins\context-cascade\scripts\validate-all-skills.py`
- `C:\Users\17175\claude-code-plugins\context-cascade\scripts\build-skill-index.py`

## License

Part of the Context Cascade ecosystem.
