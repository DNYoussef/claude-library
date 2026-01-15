"""
Skill Validator - Validate and index SKILL.md files for Claude Code

This package provides tools for:
- Validating SKILL.md files against Claude Code specifications
- Building searchable indexes from skill collections
- Extracting YAML frontmatter and trigger patterns

Installation:
    PyYAML is optional but recommended for better YAML parsing:
    pip install pyyaml

Usage:
    from skill_validator import SkillValidator, SkillIndexer

    # Validate skills
    validator = SkillValidator(skills_dir)
    total, passed, failed = validator.validate_all()
    validator.print_summary()

    # Build index
    indexer = SkillIndexer(skills_dir)
    index = indexer.build_index()
    indexer.write_index('skill-index.json')

CLI Usage:
    # Validate skills
    python -m skill_validator.skill_validator /path/to/skills --report report.json

    # Build index
    python -m skill_validator.skill_indexer /path/to/skills -o skill-index.json
"""

__version__ = "1.0.0"
__author__ = "Context Cascade"

# Validation classes and functions
from .skill_validator import (
    SkillValidator,
    ValidationResult,
    validate_single_file,
    parse_yaml_safe,
    parse_yaml_fallback,
)

# Indexer classes and functions
from .skill_indexer import (
    SkillIndexer,
    SkillData,
    parse_yaml_frontmatter,
    extract_trigger_positive,
    extract_section,
    extract_keywords,
    STOPWORDS,
    DEFAULT_CATEGORY_KEYWORDS,
)

# Check YAML availability
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


__all__ = [
    # Version info
    "__version__",
    "__author__",
    "YAML_AVAILABLE",

    # Validation
    "SkillValidator",
    "ValidationResult",
    "validate_single_file",
    "parse_yaml_safe",
    "parse_yaml_fallback",

    # Indexing
    "SkillIndexer",
    "SkillData",
    "parse_yaml_frontmatter",
    "extract_trigger_positive",
    "extract_section",
    "extract_keywords",
    "STOPWORDS",
    "DEFAULT_CATEGORY_KEYWORDS",
]
