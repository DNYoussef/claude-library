#!/usr/bin/env python3
"""
Skill Indexer - Build searchable skill index from SKILL.md files

Extracted from Context Cascade plugin for standalone use.

Features:
- YAML frontmatter extraction
- TRIGGER_POSITIVE pattern extraction
- Keyword extraction and indexing
- Category-based organization
- JSON index generation

Requirements:
- Python 3.7+
- PyYAML (optional - falls back to regex parser)

Usage:
    from skill_indexer import SkillIndexer, SkillData

    indexer = SkillIndexer(skills_dir)
    index = indexer.build_index()
    indexer.write_index('skill-index.json')
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Any

# Try to import PyYAML, fall back to regex parser if not available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# M1: Pre-compiled regex patterns for parse_yaml_fallback (avoid re-compilation on every call)
_KV_PATTERN = re.compile(r'^(\w[\w-]*)\s*:\s*(.*)$')
_INLINE_LIST_ITEMS_PATTERN = re.compile(r'"([^"]+)"|\'([^\']+)\'|([^,\[\]]+)')

# H2: Maximum file size for unbounded read protection (1MB)
MAX_FILE_SIZE_BYTES = 1 * 1024 * 1024


# Stopwords to filter from extracted keywords (M2: frozenset for immutability)
STOPWORDS: frozenset = frozenset({
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
    'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
    'through', 'during', 'before', 'after', 'above', 'below', 'between',
    'and', 'or', 'but', 'if', 'then', 'else', 'when', 'where', 'why', 'how',
    'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    'just', 'also', 'now', 'here', 'there', 'this', 'that', 'these', 'those',
    'it', 'its', 'you', 'your', 'we', 'our', 'they', 'their', 'i', 'my',
    'use', 'using', 'used', 'skill', 'skills', 'agent', 'agents', 'task', 'tasks'
})

# Default category keywords for routing
DEFAULT_CATEGORY_KEYWORDS = {
    'delivery': ['feature', 'implement', 'build', 'develop', 'create', 'add', 'new',
                 'frontend', 'backend', 'api', 'sparc', 'bug', 'fix', 'debug'],
    'quality': ['test', 'audit', 'review', 'verify', 'validate', 'check', 'quality',
                'coverage', 'lint', 'style', 'code-review'],
    'security': ['security', 'auth', 'authentication', 'permission', 'vulnerability',
                 'pentest', 'compliance', 'encrypt', 'threat'],
    'research': ['research', 'find', 'discover', 'analyze', 'investigate', 'study',
                 'literature', 'paper', 'synthesis', 'survey'],
    'orchestration': ['coordinate', 'orchestrate', 'swarm', 'parallel', 'workflow',
                      'pipeline', 'cascade', 'hive', 'chain'],
    'operations': ['deploy', 'devops', 'cicd', 'infrastructure', 'docker',
                   'kubernetes', 'terraform', 'monitor', 'release', 'github'],
    'platforms': ['platform', 'database', 'ml', 'neural', 'flow', 'nexus',
                  'codex', 'gemini', 'multi-model', 'agentdb'],
    'foundry': ['create', 'agent', 'skill', 'template', 'forge', 'generator',
                'builder', 'prompt', 'meta'],
    'specialists': ['business', 'finance', 'domain', 'expert', 'specialist',
                    'industry', 'legal', 'medical'],
    'tooling': ['documentation', 'docs', 'github', 'pr', 'issue', 'release',
                'tool', 'integration']
}


@dataclass
class SkillData:
    """Represents extracted data from a SKILL.md file."""
    name: str
    path: str
    category: str
    description: str = ""
    triggers: List[str] = field(default_factory=list)
    negative_triggers: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    trigger_positive_raw: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "path": self.path,
            "category": self.category,
            "description": self.description[:200] if self.description else "",
            "triggers": self.triggers[:30],  # Cap at 30 triggers
            "negativeTriggers": self.negative_triggers[:15],
            "files": self.files,
            "tags": self.tags,
            "hasTriggerPositive": self.trigger_positive_raw is not None
        }


def parse_yaml_fallback(yaml_text: str) -> Dict[str, Any]:
    """
    Fallback YAML parser using regex when PyYAML is not available.

    Note (M3): This function is intentionally duplicated in skill_validator.py
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
        if not line.strip() or line.strip().startswith('#'):
            continue

        # M1: use pre-compiled pattern
        kv_match = _KV_PATTERN.match(line)
        if kv_match:
            if current_key:
                if len(current_values) > 1:
                    result[current_key] = current_values
                elif current_values:
                    result[current_key] = current_values[0]
                else:
                    result[current_key] = ""

            current_key = kv_match.group(1)
            value = kv_match.group(2).strip()

            # M1: use pre-compiled pattern
            if value.startswith('[') and value.endswith(']'):
                items = _INLINE_LIST_ITEMS_PATTERN.findall(value)
                current_values = [
                    next(filter(None, item)).strip()
                    for item in items if any(item)
                ]
            elif value in ['|', '>']:
                current_values = []
            else:
                value = value.strip('"\'')
                current_values = [value] if value else []

        elif line.strip().startswith('-'):
            item = line.strip()[1:].strip().strip('"\'')
            if item:
                current_values.append(item)

        elif line.startswith('  ') and current_key:
            current_values.append(line.strip())

    if current_key:
        if len(current_values) > 1:
            result[current_key] = current_values
        elif current_values:
            result[current_key] = current_values[0]
        else:
            result[current_key] = ""

    return result


def parse_yaml_frontmatter(content: str) -> Dict[str, Any]:
    """Extract and parse YAML frontmatter from markdown content."""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    yaml_text = match.group(1)

    if YAML_AVAILABLE:
        try:
            return yaml.safe_load(yaml_text) or {}
        except yaml.YAMLError:
            pass

    return parse_yaml_fallback(yaml_text)


def extract_trigger_positive(content: str) -> Optional[Dict[str, Any]]:
    """
    Extract TRIGGER_POSITIVE block from SKILL.md content.

    Supports formats:
    - VCL format: [define|neutral] TRIGGER_POSITIVE := { ... }
    - Simple format: TRIGGER_POSITIVE: { ... }
    - Markdown header format: ## TRIGGER_POSITIVE
    """
    patterns = [
        r'\[define\|.*?\]\s*TRIGGER_POSITIVE\s*:=\s*\{([^}]+)\}',
        r'TRIGGER_POSITIVE\s*:\s*\{([^}]+)\}',
        r'##\s*TRIGGER_POSITIVE\s*\n(.*?)(?=##|\Z)'
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            block = match.group(1)
            result: Dict[str, Any] = {"raw": match.group(0)}

            # Extract keywords array
            kw_match = re.search(r'keywords\s*:\s*\[(.*?)\]', block, re.DOTALL)
            if kw_match:
                items = re.findall(r'"([^"]+)"|\'([^\']+)\'', kw_match.group(1))
                result["keywords"] = [next(filter(None, item)) for item in items]

            # Extract context
            ctx_match = re.search(r'context\s*:\s*"([^"]+)"', block)
            if ctx_match:
                result["context"] = ctx_match.group(1)

            return result

    return None


def extract_section(content: str, section_name: str) -> str:
    """Extract content from a markdown section."""
    patterns = [
        rf'##\s*{re.escape(section_name)}[^\n]*\n(.*?)(?=##|\Z)',
        rf'###\s*{re.escape(section_name)}[^\n]*\n(.*?)(?=###|##|\Z)'
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return ""


def extract_keywords(text: str, stopwords: Optional[Set[str]] = None) -> List[str]:
    """
    Extract meaningful keywords from text.

    Args:
        text: Input text
        stopwords: Set of words to filter out (uses STOPWORDS if None)

    Returns:
        List of unique keywords sorted by frequency
    """
    if not text:
        return []

    if stopwords is None:
        stopwords = STOPWORDS

    # Convert to lowercase and extract words
    words = re.sub(r'[^a-z0-9\s-]', ' ', text.lower()).split()

    # Filter stopwords and short words
    filtered = [w for w in words if len(w) > 2 and w not in stopwords]

    # Count occurrences
    counts: Dict[str, int] = {}
    for word in filtered:
        counts[word] = counts.get(word, 0) + 1

    # Return unique keywords sorted by frequency
    return sorted(counts.keys(), key=lambda w: counts[w], reverse=True)


class SkillIndexer:
    """
    Builds searchable index from SKILL.md files.

    Features:
    - Extracts metadata from YAML frontmatter
    - Parses TRIGGER_POSITIVE patterns for keyword matching
    - Builds inverted keyword index for fast search
    - Organizes skills by category

    Error Handling Contract (L1):
        - process_skill_file: Returns None on errors (logged to stdout); never raises
        - build_index: Returns partial index on errors; never raises
        - write_index: May raise IOError on file write failure
        - search methods: Return empty collections on no match; never raise
    """

    def __init__(
        self,
        skills_dir: Path,
        category_keywords: Optional[Dict[str, List[str]]] = None,
        stopwords: Optional[Set[str]] = None
    ):
        """
        Initialize indexer.

        Args:
            skills_dir: Base directory for skills
            category_keywords: Category to keyword mapping (uses defaults if None)
            stopwords: Words to filter from keywords (uses STOPWORDS if None)
        """
        self.skills_dir = Path(skills_dir)
        self.category_keywords = category_keywords or DEFAULT_CATEGORY_KEYWORDS
        self.stopwords = stopwords or STOPWORDS
        self._yaml_available = YAML_AVAILABLE

        self.skills: Dict[str, dict] = {}
        self.keyword_index: Dict[str, List[str]] = {}
        self.categories: Dict[str, dict] = {}

    @property
    def yaml_available(self) -> bool:
        """Check if PyYAML is available."""
        return self._yaml_available

    def find_skill_files(self, root_dir: Optional[Path] = None) -> List[Path]:
        """
        Find all SKILL.md files recursively.

        Args:
            root_dir: Directory to search (uses skills_dir if None)

        Returns:
            List of paths to SKILL.md files
        """
        if root_dir is None:
            root_dir = self.skills_dir

        skill_files = []
        for skill_path in root_dir.rglob("SKILL.md"):
            # Skip backup files
            if ".backup" in str(skill_path) or ".pre-" in str(skill_path):
                continue
            skill_files.append(skill_path)
        return skill_files

    def get_category_from_path(self, skill_path: Path) -> str:
        """Determine category from file path."""
        try:
            rel_path = skill_path.relative_to(self.skills_dir)
            parts = rel_path.parts
            return parts[0] if parts else "unknown"
        except ValueError:
            return "unknown"

    def get_supporting_files(self, skill_dir: Path) -> List[str]:
        """Get list of supporting files in the skill directory."""
        files = []
        try:
            for entry in skill_dir.iterdir():
                if entry.is_file() and entry.suffix == '.md':
                    files.append(entry.name)
                elif entry.is_dir() and entry.name == 'examples':
                    files.append('examples/')
        except PermissionError:
            pass
        return files

    def process_skill_file(self, skill_path: Path) -> Optional[SkillData]:
        """
        Process a single SKILL.md file and extract data.

        Args:
            skill_path: Path to SKILL.md file

        Returns:
            SkillData or None if processing failed

        Security (H2):
            Checks file size before reading to prevent memory exhaustion
            from maliciously large files. Max size: 1MB.

        Error Handling Contract (L1):
            - Returns None on read errors (logged to stdout)
            - Returns None if file exceeds MAX_FILE_SIZE_BYTES
            - Never raises exceptions
        """
        # H2: Check file size before reading to prevent unbounded memory usage
        try:
            file_size = skill_path.stat().st_size
            if file_size > MAX_FILE_SIZE_BYTES:
                print(f"  Skipping {skill_path}: file too large ({file_size} bytes > {MAX_FILE_SIZE_BYTES} max)")
                return None
        except OSError as e:
            print(f"  Error checking size of {skill_path}: {e}")
            return None

        try:
            content = skill_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            print(f"  Error reading {skill_path}: {e}")
            return None

        skill_dir = skill_path.parent
        category = self.get_category_from_path(skill_path)

        # Parse frontmatter
        frontmatter = parse_yaml_frontmatter(content)

        # Get skill name
        name = frontmatter.get('name', skill_dir.name)
        if isinstance(name, list):
            name = name[0] if name else skill_dir.name

        # Get description
        description = frontmatter.get('description', '')
        if isinstance(description, list):
            description = ' '.join(description)

        # Extract TRIGGER_POSITIVE block
        trigger_positive = extract_trigger_positive(content)

        # Collect trigger sources
        trigger_sources = [
            description,
            extract_section(content, 'When to Use'),
            extract_section(content, 'Purpose'),
        ]

        # Add TRIGGER_POSITIVE keywords if found
        if trigger_positive:
            if 'keywords' in trigger_positive:
                trigger_sources.extend(trigger_positive['keywords'])
            if 'context' in trigger_positive:
                trigger_sources.append(trigger_positive['context'])

        # Add tags from frontmatter
        tags = frontmatter.get('x-tags', frontmatter.get('tags', []))
        if isinstance(tags, str):
            tags = [tags]
        trigger_sources.extend(tags)

        # Extract all triggers
        triggers = extract_keywords(' '.join(str(s) for s in trigger_sources), self.stopwords)

        # Add explicit TRIGGER_POSITIVE keywords at the front
        if trigger_positive and 'keywords' in trigger_positive:
            explicit_kw = [k.lower() for k in trigger_positive['keywords']]
            triggers = explicit_kw + [t for t in triggers if t not in explicit_kw]

        # Extract negative triggers
        negative_sources = [
            extract_section(content, 'When NOT to Use'),
            extract_section(content, 'TRIGGER_NEGATIVE'),
            extract_section(content, 'Anti-Patterns')
        ]
        negative_triggers = extract_keywords(' '.join(negative_sources), self.stopwords)

        # Get supporting files
        files = self.get_supporting_files(skill_dir)

        # Calculate relative path
        try:
            rel_path = str(skill_dir.relative_to(self.skills_dir)).replace('\\', '/') + '/'
        except ValueError:
            rel_path = skill_path.stem + '/'

        return SkillData(
            name=name,
            path=rel_path,
            category=category,
            description=description,
            triggers=triggers,
            negative_triggers=negative_triggers,
            files=files,
            tags=tags if isinstance(tags, list) else [tags],
            trigger_positive_raw=trigger_positive.get('raw') if trigger_positive else None
        )

    def build_keyword_index(self) -> Dict[str, List[str]]:
        """
        Build inverted index: keyword -> [skill names].

        Returns:
            Dictionary mapping keywords to skill names
        """
        index: Dict[str, List[str]] = {}

        for name, skill in self.skills.items():
            for keyword in skill.get('triggers', []):
                if keyword not in index:
                    index[keyword] = []
                if name not in index[keyword]:
                    index[keyword].append(name)

        # Sort by specificity (fewer skills = more specific keyword)
        return dict(sorted(index.items(), key=lambda x: len(x[1])))

    def build_category_index(self) -> Dict[str, dict]:
        """
        Build category index with skill lists.

        Returns:
            Dictionary mapping categories to their metadata and skills
        """
        categories: Dict[str, dict] = {}

        for name, skill in self.skills.items():
            cat = skill.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = {
                    'description': '',
                    'skills': [],
                    'keywords': self.category_keywords.get(cat, [])
                }
            categories[cat]['skills'].append(name)

        return categories

    def build_index(
        self,
        additional_dirs: Optional[List[Path]] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Build complete skill index.

        Args:
            additional_dirs: Additional directories to scan for skills
            verbose: Print progress information

        Returns:
            Complete index dictionary
        """
        # Find all skill files
        skill_files = self.find_skill_files()
        if verbose:
            print(f"Found {len(skill_files)} SKILL.md files in {self.skills_dir}")

        # Process additional directories
        supplementary_files = []
        if additional_dirs:
            for add_dir in additional_dirs:
                if add_dir.exists():
                    add_files = self.find_skill_files(add_dir)
                    supplementary_files.extend(add_files)
                    if verbose:
                        print(f"Found {len(add_files)} additional files in {add_dir}")

        all_skill_files = skill_files + supplementary_files

        # Process each skill
        self.skills = {}
        trigger_positive_count = 0
        supplementary_count = 0

        for skill_path in all_skill_files:
            is_supplementary = skill_path not in skill_files
            skill_data = self.process_skill_file(skill_path)

            if not skill_data:
                continue

            if is_supplementary:
                skill_data.tags.append("supplementary")
                supplementary_count += 1

            self.skills[skill_data.name] = skill_data.to_dict()

            if skill_data.trigger_positive_raw:
                trigger_positive_count += 1
                if verbose:
                    print(f"  [TRIGGER+] {skill_data.name}")

        # Build indices
        self.keyword_index = self.build_keyword_index()
        self.categories = self.build_category_index()

        # Build final index
        index = {
            'version': '2.1.0',
            'generated': datetime.utcnow().isoformat() + 'Z',
            'generator': 'skill_indexer.py',
            'total_skills': len(self.skills),
            'core_skills': len(self.skills) - supplementary_count,
            'supplementary_skills': supplementary_count,
            'skills_with_trigger_positive': trigger_positive_count,
            'yaml_parser': 'pyyaml' if self._yaml_available else 'fallback',
            'categories': self.categories,
            'skills': self.skills,
            'keyword_index': self.keyword_index,
            'category_keywords': self.category_keywords
        }

        return index

    def write_index(self, output_path: Path) -> None:
        """
        Write index to JSON file.

        Args:
            output_path: Path for output file
        """
        index = {
            'version': '2.1.0',
            'generated': datetime.utcnow().isoformat() + 'Z',
            'generator': 'skill_indexer.py',
            'total_skills': len(self.skills),
            'yaml_parser': 'pyyaml' if self._yaml_available else 'fallback',
            'categories': self.categories,
            'skills': self.skills,
            'keyword_index': self.keyword_index,
            'category_keywords': self.category_keywords
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)

    def search_by_keyword(self, keyword: str) -> List[str]:
        """
        Find skills matching a keyword.

        Args:
            keyword: Keyword to search for

        Returns:
            List of matching skill names
        """
        keyword = keyword.lower()
        return self.keyword_index.get(keyword, [])

    def search_by_keywords(self, keywords: List[str]) -> Dict[str, int]:
        """
        Find skills matching multiple keywords with scoring.

        Args:
            keywords: List of keywords to search for

        Returns:
            Dictionary mapping skill names to match counts
        """
        scores: Dict[str, int] = {}
        for keyword in keywords:
            for skill_name in self.search_by_keyword(keyword.lower()):
                scores[skill_name] = scores.get(skill_name, 0) + 1
        return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))

    def get_skills_by_category(self, category: str) -> List[str]:
        """
        Get all skills in a category.

        Args:
            category: Category name

        Returns:
            List of skill names
        """
        return self.categories.get(category, {}).get('skills', [])

    def print_summary(self):
        """Print index summary to stdout."""
        print("\n=== Skill Index Summary ===")
        print(f"Total skills: {len(self.skills)}")
        print(f"Keywords indexed: {len(self.keyword_index)}")
        print(f"Categories: {len(self.categories)}")
        if not self._yaml_available:
            print("Note: Using fallback YAML parser")

        print("\nSkills per category:")
        for cat, data in sorted(
            self.categories.items(),
            key=lambda x: len(x[1]['skills']),
            reverse=True
        ):
            print(f"  {cat}: {len(data['skills'])}")


def main() -> int:
    """
    CLI entry point.

    Returns (M4):
        Exit code: 0 on success, 1 if directory not found.
        Returns exit code instead of calling sys.exit() to allow library use.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Build searchable skill index from SKILL.md files'
    )
    parser.add_argument(
        'skills_dir',
        type=str,
        nargs='?',
        default='.',
        help='Directory containing SKILL.md files (default: current directory)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='skill-index.json',
        help='Output JSON file path (default: skill-index.json)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    skills_dir = Path(args.skills_dir)
    if not skills_dir.exists():
        print(f"Error: Directory not found: {skills_dir}")
        return 1

    indexer = SkillIndexer(skills_dir)

    print(f"Building skill index...")
    print(f"Skills directory: {skills_dir}")
    if not indexer.yaml_available:
        print("Note: PyYAML not found, using fallback parser")

    indexer.build_index(verbose=args.verbose)

    output_path = Path(args.output)
    indexer.write_index(output_path)
    print(f"\nIndex written to {output_path}")

    indexer.print_summary()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
