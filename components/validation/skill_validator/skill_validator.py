#!/usr/bin/env python3
"""
Skill Validator - Validates SKILL.md files against Claude Code specifications

Extracted from Context Cascade plugin for standalone use.

Features:
- YAML frontmatter extraction and validation
- Trigger pattern validation
- Claude Code spec compliance checks
- JSON report generation

Requirements:
- Python 3.7+
- PyYAML (optional - falls back to regex parser)

Usage:
    from skill_validator import SkillValidator, ValidationResult

    validator = SkillValidator(skills_dir)
    results = validator.validate_all()
    validator.print_summary()
"""

import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, ClassVar
from dataclasses import dataclass, asdict

# Try to import PyYAML, fall back to regex parser if not available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# LEGO Import: Use shared types from library for common validation types
try:
    from library.common.types import ValidationResult as BaseValidationResult, Violation, Severity
except ImportError:
    try:
        from common.types import ValidationResult as BaseValidationResult, Violation, Severity
    except ImportError:
        # Fallback for standalone use - BaseValidationResult not needed, using SkillValidationResult
        BaseValidationResult = None  # type: ignore
        Violation = None  # type: ignore
        Severity = None  # type: ignore

# M1: Pre-compiled regex patterns for parse_yaml_fallback (avoid re-compilation on every call)
_KV_PATTERN = re.compile(r'^(\w[\w-]*)\s*:\s*(.*)$')
_INLINE_LIST_ITEMS_PATTERN = re.compile(r'"([^"]+)"|\'([^\']+)\'|([^,\[\]]+)')


# NOTE: This module uses a specialized SkillValidationResult with skill-specific fields.
# For simple validation needs, use library.common.types.ValidationResult.

@dataclass
class SkillValidationResult:
    """
    Result of validating a single skill file.

    This is a specialized validation result for SKILL.md files that includes
    skill-specific context like path and name. For simple validation,
    use library.common.types.ValidationResult instead.
    """
    skill_path: str
    skill_name: str
    valid: bool
    errors: List[str]
    warnings: List[str]
    info: Dict[str, Any]

    def __bool__(self) -> bool:
        return self.valid

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# Backward compatibility alias - prefer SkillValidationResult for new code
ValidationResult = SkillValidationResult


def parse_yaml_fallback(yaml_text: str) -> Dict[str, Any]:
    """
    Fallback YAML parser using regex when PyYAML is not available.
    Handles simple key-value pairs and lists.

    Note (M3): This function is intentionally duplicated in skill_indexer.py
    to allow standalone use of each module without cross-dependencies.

    Error Handling Contract (L1):
        - Returns empty dict on empty input
        - Silently skips malformed lines (best-effort parsing)
        - Never raises exceptions; returns partial results on parse errors
    """
    result: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_values: List[str] = []

    for line in yaml_text.split('\n'):
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith('#'):
            continue

        # Key-value pair (M1: use pre-compiled pattern)
        kv_match = _KV_PATTERN.match(line)
        if kv_match:
            # Save previous key
            if current_key:
                if len(current_values) > 1:
                    result[current_key] = current_values
                elif current_values:
                    result[current_key] = current_values[0]
                else:
                    result[current_key] = ""

            current_key = kv_match.group(1)
            value = kv_match.group(2).strip()

            # Check for inline list: [item1, item2] (M1: use pre-compiled pattern)
            if value.startswith('[') and value.endswith(']'):
                items = _INLINE_LIST_ITEMS_PATTERN.findall(value)
                current_values = [
                    next(filter(None, item)).strip()
                    for item in items if any(item)
                ]
            elif value in ['|', '>']:
                # Multi-line value indicator
                current_values = []
            else:
                # Remove quotes
                value = value.strip('"\'')
                current_values = [value] if value else []

        # List item
        elif line.strip().startswith('-'):
            item = line.strip()[1:].strip().strip('"\'')
            if item:
                current_values.append(item)

        # Continuation (indented line)
        elif line.startswith('  ') and current_key:
            current_values.append(line.strip())

    # Save last key
    if current_key:
        if len(current_values) > 1:
            result[current_key] = current_values
        elif current_values:
            result[current_key] = current_values[0]
        else:
            result[current_key] = ""

    return result


def parse_yaml_safe(yaml_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse YAML text with fallback to regex parser.

    Returns:
        Tuple of (parsed_dict, error_message)
        If successful, error_message is None
    """
    if YAML_AVAILABLE:
        try:
            result = yaml.safe_load(yaml_text)
            return result, None
        except yaml.YAMLError as e:
            return None, str(e)
    else:
        try:
            result = parse_yaml_fallback(yaml_text)
            return result, None
        except Exception as e:
            return None, str(e)


class SkillValidator:
    """
    Validates SKILL.md files against Claude Code specifications.

    Claude Code Specs (from https://code.claude.com/docs/en/skills):
    - name: max 64 chars, lowercase letters, numbers, hyphens only
    - description: max 1024 chars, no XML tags
    - XML tags not allowed in frontmatter fields

    Error Handling Contract (L1):
        - validate_skill: Returns ValidationResult with errors list; never raises
        - validate_all: Returns tuple of counts; never raises
        - File read errors are captured in ValidationResult.errors
        - YAML parse errors are captured in ValidationResult.errors
    """

    # L2: Type hints for class attributes
    # Official Claude Code specs
    MAX_NAME_LENGTH: ClassVar[int] = 64
    MAX_DESCRIPTION_LENGTH: ClassVar[int] = 1024
    NAME_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[a-z0-9-]+$')

    # XML tags are not allowed
    XML_PATTERN: ClassVar[re.Pattern] = re.compile(r'<[^>]+>')

    # Usage trigger keywords (best practice)
    USAGE_KEYWORDS: ClassVar[List[str]] = ['use when', 'use this', 'use for', 'activate when', 'trigger']

    def __init__(self, skills_dir: Path):
        """
        Initialize validator with skills directory.

        Args:
            skills_dir: Path to directory containing SKILL.md files
        """
        self.skills_dir = Path(skills_dir)
        self.results: List[ValidationResult] = []
        self._yaml_available = YAML_AVAILABLE

    @property
    def yaml_available(self) -> bool:
        """Check if PyYAML is available."""
        return self._yaml_available

    def find_all_skills(self) -> List[Path]:
        """
        Find all SKILL.md files in the skills directory.

        Returns:
            Sorted list of paths to SKILL.md files
        """
        skill_files = []
        for skill_file in self.skills_dir.rglob("SKILL.md"):
            # Skip backup files
            if ".backup" in str(skill_file) or ".pre-" in str(skill_file):
                continue
            skill_files.append(skill_file)
        return sorted(skill_files)

    def extract_frontmatter(self, content: str) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Extract YAML frontmatter from markdown content.

        Args:
            content: Full file content

        Returns:
            Tuple of (frontmatter_text, markdown_content, errors)
        """
        errors = []

        # Check for opening delimiter
        if not content.startswith('---'):
            errors.append("Missing opening '---' delimiter on line 1")
            return None, None, errors

        # Split on delimiters
        parts = content.split('---', 2)
        if len(parts) < 3:
            errors.append("Missing closing '---' delimiter for YAML frontmatter")
            return None, None, errors

        frontmatter_text = parts[1].strip()
        markdown_content = parts[2].strip()

        return frontmatter_text, markdown_content, errors

    def validate_name(self, name: str) -> List[str]:
        """
        Validate skill name against Claude Code specs.

        Args:
            name: Skill name from frontmatter

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if len(name) > self.MAX_NAME_LENGTH:
            errors.append(
                f"Name exceeds {self.MAX_NAME_LENGTH} characters: {len(name)} chars"
            )

        if not self.NAME_PATTERN.match(name):
            errors.append(
                f"Name must use lowercase letters, numbers, and hyphens only: '{name}'"
            )

        if self.XML_PATTERN.search(name):
            errors.append("Name contains XML tags (not allowed)")

        return errors

    def validate_description(self, description: str) -> Tuple[List[str], List[str]]:
        """
        Validate skill description against Claude Code specs.

        Args:
            description: Skill description from frontmatter

        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []

        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            errors.append(
                f"Description exceeds {self.MAX_DESCRIPTION_LENGTH} characters: "
                f"{len(description)} chars"
            )

        if self.XML_PATTERN.search(description):
            errors.append("Description contains XML tags (not allowed)")

        # Check for usage triggers (best practice, not required)
        has_usage_trigger = any(
            keyword in description.lower()
            for keyword in self.USAGE_KEYWORDS
        )
        if not has_usage_trigger:
            warnings.append(
                "Description should include usage triggers (e.g., 'Use when...')"
            )

        return errors, warnings

    def validate_skill(self, skill_file: Path) -> ValidationResult:
        """
        Validate a single SKILL.md file.

        Args:
            skill_file: Path to SKILL.md file

        Returns:
            ValidationResult with validation details

        Security (H1):
            Validates that skill_file is within skills_dir to prevent
            path traversal attacks via symlinks or .. components.
        """
        errors: List[str] = []
        warnings: List[str] = []
        info: Dict[str, Any] = {}

        # H1: Path traversal protection - ensure file is within skills_dir
        try:
            resolved_skill = skill_file.resolve()
            resolved_base = self.skills_dir.resolve()
            # Check if skill file is within the skills directory
            resolved_skill.relative_to(resolved_base)
        except ValueError:
            return ValidationResult(
                skill_path=str(skill_file),
                skill_name="UNKNOWN",
                valid=False,
                errors=[f"Path traversal detected: {skill_file} is outside skills directory {self.skills_dir}"],
                warnings=[],
                info={}
            )

        # Read file content
        try:
            content = skill_file.read_text(encoding='utf-8')
        except Exception as e:
            return ValidationResult(
                skill_path=str(skill_file),
                skill_name="UNKNOWN",
                valid=False,
                errors=[f"Failed to read file: {e}"],
                warnings=[],
                info={}
            )

        # Extract frontmatter
        frontmatter_text, markdown_content, extract_errors = self.extract_frontmatter(content)
        if extract_errors:
            return ValidationResult(
                skill_path=str(skill_file),
                skill_name="UNKNOWN",
                valid=False,
                errors=extract_errors,
                warnings=warnings,
                info=info
            )

        # Parse YAML
        frontmatter, parse_error = parse_yaml_safe(frontmatter_text)
        if parse_error:
            errors.append(f"Invalid YAML syntax: {parse_error}")
            return ValidationResult(
                skill_path=str(skill_file),
                skill_name="UNKNOWN",
                valid=False,
                errors=errors,
                warnings=warnings,
                info=info
            )

        # Validate frontmatter is a dict
        if not isinstance(frontmatter, dict):
            errors.append("Frontmatter must be a YAML object")
            return ValidationResult(
                skill_path=str(skill_file),
                skill_name="UNKNOWN",
                valid=False,
                errors=errors,
                warnings=warnings,
                info=info
            )

        # Validate name field (required)
        name = frontmatter.get('name')
        if not name:
            errors.append("Missing required field: 'name'")
        else:
            info['name'] = name
            errors.extend(self.validate_name(name))

        # Validate description field (required)
        description = frontmatter.get('description')
        if not description:
            errors.append("Missing required field: 'description'")
        else:
            info['description'] = description
            desc_errors, desc_warnings = self.validate_description(description)
            errors.extend(desc_errors)
            warnings.extend(desc_warnings)

        # Collect optional fields (L3: renamed loop variable to avoid shadowing 'field' import)
        optional_fields = {}
        for opt_field in ['version', 'category', 'tags', 'author', 'x-tags']:
            if opt_field in frontmatter:
                optional_fields[opt_field] = frontmatter[opt_field]

        if optional_fields:
            info['optional_fields'] = optional_fields

        # Check for tabs in frontmatter
        if '\t' in frontmatter_text:
            warnings.append(
                "YAML frontmatter uses tabs (should use spaces for indentation)"
            )

        # Check markdown content
        if not markdown_content:
            warnings.append("No markdown content after frontmatter")
        else:
            info['content_length'] = len(markdown_content)

        # Determine validity
        valid = len(errors) == 0

        return ValidationResult(
            skill_path=str(skill_file),
            skill_name=name or "UNKNOWN",
            valid=valid,
            errors=errors,
            warnings=warnings,
            info=info
        )

    def validate_all(self) -> Tuple[int, int, int]:
        """
        Validate all skills in the directory.

        Returns:
            Tuple of (total, passed, failed)
        """
        skill_files = self.find_all_skills()
        total = len(skill_files)

        self.results = []
        for skill_file in skill_files:
            result = self.validate_skill(skill_file)
            self.results.append(result)

        passed = sum(1 for r in self.results if r.valid)
        failed = total - passed

        return total, passed, failed

    def get_failed_results(self) -> List[ValidationResult]:
        """Get list of failed validation results."""
        return [r for r in self.results if not r.valid]

    def get_passed_results(self) -> List[ValidationResult]:
        """Get list of passed validation results."""
        return [r for r in self.results if r.valid]

    def analyze_optional_fields(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze usage of optional YAML fields across all skills.

        Returns:
            Dictionary mapping field names to usage statistics
        """
        field_usage: Dict[str, Dict[str, Any]] = {
            'version': {'count': 0, 'skills': []},
            'category': {'count': 0, 'skills': []},
            'tags': {'count': 0, 'skills': []},
            'author': {'count': 0, 'skills': []},
        }

        for result in self.results:
            if not result.valid or 'optional_fields' not in result.info:
                continue
            for field_name in field_usage.keys():
                if field_name not in result.info['optional_fields']:
                    continue
                field_usage[field_name]['count'] += 1
                field_usage[field_name]['skills'].append(result.skill_name)

        return field_usage

    def print_summary(self):
        """Print validation summary to stdout."""
        total = len(self.results)
        if total == 0:
            print("No skills found to validate.")
            return

        passed = sum(1 for r in self.results if r.valid)
        failed = total - passed

        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Total Skills:  {total}")
        print(f"Passed:        {passed} ({100 * passed / total:.1f}%)")
        print(f"Failed:        {failed} ({100 * failed / total:.1f}%)")
        if not self._yaml_available:
            print("Note: Using fallback YAML parser (PyYAML not installed)")
        print("=" * 80)

        if failed > 0:
            print("\nFAILED SKILLS:")
            print("-" * 80)
            for result in self.results:
                if not result.valid:
                    print(f"\n{result.skill_name} - {result.skill_path}")
                    for error in result.errors:
                        print(f"  ERROR: {error}")
                    for warning in result.warnings:
                        print(f"  WARN:  {warning}")

        # Count warnings
        total_warnings = sum(len(r.warnings) for r in self.results)
        if total_warnings > 0:
            print(f"\nTotal Warnings: {total_warnings}")
            print("(Skills with warnings still pass validation)")

    def print_detailed_results(self):
        """Print detailed results for all skills."""
        print("\n" + "=" * 80)
        print("DETAILED RESULTS")
        print("=" * 80)

        for result in self.results:
            status = "PASS" if result.valid else "FAIL"
            print(f"\n[{status}] {result.skill_name}")
            print(f"       {result.skill_path}")

            if result.errors:
                for error in result.errors:
                    print(f"  ERROR: {error}")

            if result.warnings:
                for warning in result.warnings:
                    print(f"  WARN:  {warning}")

            if result.info and result.valid:
                if 'optional_fields' in result.info:
                    fields = ', '.join(result.info['optional_fields'].keys())
                    print(f"  INFO:  Optional fields: {fields}")

    def generate_json_report(self, output_file: Path) -> Dict[str, Any]:
        """
        Generate JSON validation report.

        Args:
            output_file: Path to write JSON report

        Returns:
            Report dictionary
        """
        report = {
            'summary': {
                'total': len(self.results),
                'passed': sum(1 for r in self.results if r.valid),
                'failed': sum(1 for r in self.results if not r.valid),
                'warnings': sum(len(r.warnings) for r in self.results),
                'yaml_parser': 'pyyaml' if self._yaml_available else 'fallback'
            },
            'field_usage': self.analyze_optional_fields(),
            'results': [r.to_dict() for r in self.results]
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(report, indent=2))

        return report


def validate_single_file(skill_file: Path) -> ValidationResult:
    """
    Convenience function to validate a single skill file.

    Args:
        skill_file: Path to SKILL.md file

    Returns:
        ValidationResult
    """
    validator = SkillValidator(skill_file.parent)
    return validator.validate_skill(skill_file)


def main() -> int:
    """
    CLI entry point.

    Returns (M4):
        Exit code: 0 if all validations pass, 1 if any fail or errors occur.
        Returns exit code instead of calling sys.exit() to allow library use.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate SKILL.md files against Claude Code specifications'
    )
    parser.add_argument(
        'skills_dir',
        type=str,
        nargs='?',
        default='.',
        help='Directory containing SKILL.md files (default: current directory)'
    )
    parser.add_argument(
        '--report',
        type=str,
        help='Generate JSON report to specified file'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed results for all skills'
    )

    args = parser.parse_args()

    skills_dir = Path(args.skills_dir)
    if not skills_dir.exists():
        print(f"Error: Directory not found: {skills_dir}")
        return 1

    validator = SkillValidator(skills_dir)

    print("Claude Code SKILL.md Validator")
    print(f"Skills Directory: {skills_dir}")
    if not validator.yaml_available:
        print("Note: PyYAML not found, using fallback parser")
    print()

    total, passed, failed = validator.validate_all()

    if args.verbose:
        validator.print_detailed_results()

    validator.print_summary()

    if args.report:
        report_file = Path(args.report)
        validator.generate_json_report(report_file)
        print(f"\nJSON report saved to: {report_file}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
