# Pattern Matcher

A generic, reusable text pattern detection engine. Originally extracted from the Slop Detector lexical analyzer.

## Features

- **Zero external dependencies** - Uses only Python standard library
- **Flexible pattern types** - Literal strings, word boundaries, and regex
- **Configurable scoring** - Weights, multiplier caps, and max score limits
- **Signal levels** - CRITICAL, HIGH, MEDIUM, LOW, INFO categorization
- **Detailed results** - Match positions, counts, categories, and statistics
- **Injectable database** - Patterns are not hardcoded; fully customizable
- **Serialization support** - Load/export patterns as dictionaries (JSON-compatible)

## Installation

Copy the `pattern-matcher` directory to your project:

```
pattern-matcher/
    __init__.py
    pattern_matcher.py
    README.md
```

## Quick Start

```python
from pattern_matcher import (
    PatternMatcher,
    PatternDatabase,
    PatternConfig,
    SignalLevel
)

# Create a pattern database
db = PatternDatabase()

# Add word patterns (matched at word boundaries)
db.add_word("delve", weight=3.0, signal_level=SignalLevel.HIGH)
db.add_word("leverage", weight=2.0, signal_level=SignalLevel.HIGH)
db.add_word("utilize", weight=2.0, signal_level=SignalLevel.MEDIUM)

# Add regex patterns
db.add_regex(
    r"In today's (?:ever-evolving|fast-paced|digital) world",
    weight=2.5,
    signal_level=SignalLevel.HIGH,
    description="AI opener pattern"
)

# Configure the matcher
config = PatternConfig(
    max_score=25.0,        # Cap total score
    score_precision=1,     # Decimal places
    include_positions=True # Track match positions
)

# Create matcher and analyze text
matcher = PatternMatcher(db, config)
result = matcher.analyze("Let's delve into today's digital world to leverage AI.")

print(f"Score: {result.score}/{result.max_score}")
print(f"Summary: {result.summary}")
```

## API Reference

### Core Classes

#### PatternDatabase

Container for pattern definitions. Supports method chaining.

```python
db = PatternDatabase()

# Add patterns with fluent API
db.add_word("word", weight=1.0, signal_level=SignalLevel.MEDIUM)
db.add_literal("exact phrase", weight=1.5)
db.add_regex(r"pattern\s+here", weight=2.0, description="Description")

# Or add PatternDefinition objects directly
db.add_pattern(PatternDefinition(
    pattern="test",
    weight=1.0,
    signal_level=SignalLevel.LOW,
    pattern_type=PatternType.WORD_BOUNDARY
))

# Load from dictionary (JSON-compatible)
db.load_from_dict({
    "words": {"delve": 3.0, "leverage": 2.0},
    "phrases": [
        {"pattern": r"In today's .+? world", "weight": 2.5, "description": "AI opener"}
    ]
})

# Export to dictionary
data = db.to_dict()
```

#### PatternMatcher

Main analysis engine.

```python
matcher = PatternMatcher(database, config)
result = matcher.analyze(text)
```

#### PatternConfig

Configuration options for the matcher.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_score` | `float` | `None` | Maximum total score (no cap if None) |
| `score_precision` | `int` | `1` | Decimal places for rounding |
| `include_positions` | `bool` | `True` | Track character positions of matches |
| `merge_overlapping` | `bool` | `False` | Merge overlapping matches |
| `summary_generator` | `Callable` | `None` | Custom summary function |

### Data Classes

#### PatternDefinition

Defines a single pattern to match.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pattern` | `str` | required | Pattern string |
| `weight` | `float` | `1.0` | Base score when matched |
| `signal_level` | `SignalLevel` | `MEDIUM` | Severity level |
| `pattern_type` | `PatternType` | `WORD_BOUNDARY` | How to match |
| `description` | `str` | `""` | Human-readable description |
| `case_sensitive` | `bool` | `False` | Case sensitivity |
| `max_multiplier` | `float` | `2.0` | Max score multiplier for repeats |
| `category` | `str` | `""` | Grouping category |
| `metadata` | `Dict` | `{}` | Additional data |

#### PatternMatch

Result of a single pattern match.

| Field | Type | Description |
|-------|------|-------------|
| `pattern` | `str` | The matched pattern |
| `matched_text` | `str` | Actual text that matched |
| `count` | `int` | Number of occurrences |
| `positions` | `List[int]` | Character positions |
| `signal_level` | `SignalLevel` | Severity level |
| `score` | `float` | Calculated score |
| `description` | `str` | Pattern description |
| `category` | `str` | Pattern category |

#### MatchResult

Complete analysis result.

| Field | Type | Description |
|-------|------|-------------|
| `score` | `float` | Total score |
| `max_score` | `float` | Maximum possible score |
| `matches` | `List[PatternMatch]` | All matches |
| `summary` | `str` | Human-readable summary |
| `categories` | `Dict[str, List]` | Matches by category |
| `statistics` | `Dict` | Match statistics |

### Enums

#### SignalLevel

```python
class SignalLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
```

#### PatternType

```python
class PatternType(Enum):
    LITERAL = "literal"       # Exact string match
    REGEX = "regex"           # Full regex pattern
    WORD_BOUNDARY = "word_boundary"  # Word with \b boundaries
```

### Factory Functions

#### create_matcher_from_wordlist

Quick setup from a simple word dictionary.

```python
from pattern_matcher import create_matcher_from_wordlist, SignalLevel, PatternConfig

words = {
    "delve": 3.0,
    "leverage": 2.0,
    "utilize": 1.5
}

matcher = create_matcher_from_wordlist(
    words,
    signal_level=SignalLevel.HIGH,
    config=PatternConfig(max_score=25.0)
)

result = matcher.analyze("We must leverage and utilize these tools.")
```

## Advanced Usage

### Custom Summary Generator

```python
def my_summary(matches: List[PatternMatch], score: float) -> str:
    if score > 20:
        return f"High pattern density detected ({len(matches)} patterns, score: {score})"
    elif score > 10:
        return f"Moderate patterns detected ({len(matches)} patterns)"
    else:
        return "Clean text"

config = PatternConfig(summary_generator=my_summary)
```

### Loading Patterns from JSON

```python
import json

# patterns.json
{
    "patterns": [
        {
            "pattern": "delve",
            "weight": 3.0,
            "signal_level": "HIGH",
            "pattern_type": "word_boundary",
            "description": "AI-typical word",
            "category": "vocabulary"
        }
    ]
}

with open("patterns.json") as f:
    data = json.load(f)

db = PatternDatabase().load_from_dict(data)
```

### Categorized Analysis

```python
db = PatternDatabase()
db.add_word("delve", weight=3.0, category="ai_words")
db.add_word("leverage", weight=2.0, category="ai_words")
db.add_regex(r"In conclusion", weight=1.0, category="structure")

result = matcher.analyze(text)

# Access by category
for category, matches in result.categories.items():
    print(f"{category}: {len(matches)} matches")
```

### Statistics Access

```python
result = matcher.analyze(text)

print(f"Total patterns matched: {result.statistics['pattern_count']}")
print(f"Total occurrences: {result.statistics['total_occurrences']}")
print(f"Match density: {result.statistics['match_density']}")

# By signal level
for level, stats in result.statistics['by_signal_level'].items():
    print(f"  {level}: {stats['count']} patterns, score: {stats['total_score']}")
```

## Original Source

Extracted from: `D:\Projects\slop-detector\backend\analyzers\lexical.py`

The original `LexicalAnalyzer` class was refactored to:
1. Separate pattern storage (database) from matching logic (matcher)
2. Make patterns injectable rather than hardcoded
3. Add configuration options
4. Create reusable data classes
5. Support serialization for pattern management

## License

MIT License - Part of the Claude Code Library ecosystem.
