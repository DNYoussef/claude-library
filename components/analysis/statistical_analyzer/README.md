# Statistical Analyzer

A standalone text analysis component for calculating statistical metrics that help identify patterns in text.

## Source

Extracted from: `D:\Projects\slop-detector\backend\analyzers\statistical.py`

## Dependencies

**Zero external dependencies** - uses only Python standard library:
- `re` - Regular expressions for text parsing
- `math` - Mathematical functions (log2)
- `collections` - Counter for frequency analysis
- `dataclasses` - Structured result objects
- `typing` - Type hints

## Installation

Copy the `statistical-analyzer` directory to your project:

```bash
cp -r ~/.claude/library/components/analysis/statistical-analyzer ./your_project/
```

## Usage

### Basic Usage

```python
from statistical_analyzer import StatisticalAnalyzer

analyzer = StatisticalAnalyzer()
result = analyzer.analyze("Your text to analyze goes here...")

print(f"Score: {result.score}/{result.max_score}")
print(f"Summary: {result.summary}")
```

### Accessing Individual Metrics

```python
result = analyzer.analyze(text)

# Entropy (word predictability)
print(f"Normalized Entropy: {result.entropy.value}")
print(f"Raw Entropy: {result.entropy.raw_entropy}")
print(f"Assessment: {result.entropy.assessment}")

# Burstiness (sentence length variance)
print(f"CV: {result.burstiness.value}")
print(f"Mean sentence length: {result.burstiness.mean_length}")
print(f"Std Dev: {result.burstiness.std_dev}")

# Lexical Diversity (TTR)
print(f"TTR: {result.lexical_diversity.value}")
print(f"Unique words: {result.lexical_diversity.unique_words}")

# Hapax Legomena
print(f"Hapax ratio: {result.hapax.value}")
print(f"Words appearing once: {result.hapax.hapax_count}")

# Sentence Structure
print(f"Start diversity: {result.sentence_starts.value}")
print(f"Most common starts: {result.sentence_starts.most_common}")
```

### Dictionary Output (Legacy Compatibility)

```python
result_dict = analyzer.analyze_dict(text)
print(result_dict['metrics']['entropy']['value'])
```

### Standalone Utility Functions

```python
from statistical_analyzer import (
    calculate_shannon_entropy,
    calculate_coefficient_of_variation,
    calculate_type_token_ratio,
    calculate_hapax_ratio,
)

words = ["the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"]

entropy = calculate_shannon_entropy(words)
ttr = calculate_type_token_ratio(words)
hapax = calculate_hapax_ratio(words)

sentence_lengths = [12.0, 8.0, 15.0, 6.0, 20.0]
cv = calculate_coefficient_of_variation(sentence_lengths)
```

## Metrics Explained

### 1. Shannon Entropy

Measures word distribution predictability.

| Value Range | Interpretation |
|-------------|----------------|
| < 0.55 | Very low - highly predictable (10 pts) |
| 0.55-0.65 | Low - somewhat predictable (7 pts) |
| 0.65-0.75 | Moderate (4 pts) |
| 0.75-0.85 | Good - natural variation (1 pt) |
| > 0.85 | High - varied word choice (0 pts) |

Human text typically: 0.7-0.9
AI text tends toward: 0.5-0.7

### 2. Burstiness (Coefficient of Variation)

Measures variance in sentence lengths.

| CV Value | Interpretation |
|----------|----------------|
| < 0.2 | Very uniform - AI pattern (10 pts) |
| 0.2-0.3 | Low variation (7 pts) |
| 0.3-0.4 | Moderate variation (4 pts) |
| 0.4-0.5 | Good variation (1 pt) |
| > 0.5 | Natural variation (0 pts) |

Human writing typically: CV > 0.4
AI writing tends toward: CV 0.15-0.3

### 3. Type-Token Ratio (TTR)

Measures lexical diversity (unique words / total words).

| TTR Value | Interpretation |
|-----------|----------------|
| < 0.3 | Very low diversity - repetitive (8 pts) |
| 0.3-0.4 | Limited variation (4 pts) |
| 0.4-0.7 | Natural diversity (0 pts) |
| > 0.8 (long text) | Suspiciously high - thesaurus pattern (6 pts) |

Uses MSTTR (Mean Segmental TTR) for texts over 100 words.

### 4. Hapax Legomena

Ratio of words appearing exactly once.

| Hapax Ratio | Interpretation |
|-------------|----------------|
| < 0.3 | Low - repetitive vocabulary (6 pts) |
| 0.3-0.4 | Below average uniqueness (3 pts) |
| 0.4-0.75 | Natural pattern (0 pts) |
| > 0.75 | Unusually high - may be artificial (4 pts) |

Human text typically: 40-60% hapax

### 5. Sentence Start Diversity

Analyzes variety in sentence openings (first 1-2 words).

| Diversity | Interpretation |
|-----------|----------------|
| < 0.5 or repeat > 30% | Repetitive openings (6 pts) |
| 0.5-0.7 | Limited variety (3 pts) |
| > 0.7 | Good variety (0 pts) |

## Scoring

Maximum score: **40 points**

Higher scores indicate more AI-like statistical patterns.

| Score Range | Interpretation |
|-------------|----------------|
| 0-10 | Natural, human-like patterns |
| 10-20 | Some deviations from typical human writing |
| 20-30 | Significant statistical anomalies |
| 30-40 | Strong indicators of AI-generated text |

## Dataclass Reference

### StatisticalMetrics

Main result container:

```python
@dataclass
class StatisticalMetrics:
    score: float              # Final score (0-40)
    max_score: float          # Maximum possible (40)
    word_count: int           # Words analyzed
    sentence_count: int       # Sentences analyzed
    entropy: EntropyMetrics
    burstiness: BurstinessMetrics
    lexical_diversity: LexicalDiversityMetrics
    hapax: HapaxMetrics
    sentence_starts: SentenceStartMetrics
    summary: str              # Human-readable summary
```

### Metric-Specific Dataclasses

Each metric has its own dataclass with:
- `value`: Primary metric value
- `points`: Score contribution
- `assessment`: Human-readable interpretation
- Additional metric-specific fields

## API Reference

### Classes

| Class | Description |
|-------|-------------|
| `StatisticalAnalyzer` | Main analyzer class |
| `StatisticalMetrics` | Complete analysis results |
| `EntropyMetrics` | Shannon entropy results |
| `BurstinessMetrics` | Sentence variance results |
| `LexicalDiversityMetrics` | TTR results |
| `HapaxMetrics` | Hapax Legomena results |
| `SentenceStartMetrics` | Sentence opening results |

### Functions

| Function | Description |
|----------|-------------|
| `calculate_shannon_entropy(words)` | Normalized entropy (0-1) |
| `calculate_coefficient_of_variation(values)` | CV calculation |
| `calculate_type_token_ratio(words, segment_size)` | TTR with MSTTR |
| `calculate_hapax_ratio(words)` | Hapax ratio (0-1) |

## Version

1.0.0

## License

Internal component - part of the Context Cascade ecosystem.
