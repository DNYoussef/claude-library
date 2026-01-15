# Cognitive Configuration Manager

Standalone component extracted from Context Cascade `cognitive-architecture/core/config.py`.

Provides configuration dataclasses for cognitive architecture including VERILINGUA frames, VERIX epistemic notation, and multi-objective optimization via 14-dimensional vector encoding.

## Installation

Copy this directory to your project or add to Python path:

```python
import sys
sys.path.append("/path/to/cognitive-config")
from cognitive_config import FullConfig, VectorCodec
```

## Dependencies

**None** - This is a fully standalone component using only Python standard library:
- `dataclasses`
- `typing`
- `enum`

## Quick Start

```python
from cognitive_config import (
    FullConfig,
    FrameworkConfig,
    PromptConfig,
    VerixStrictness,
    CompressionLevel,
    VectorCodec,
    get_named_mode,
)

# Create default configuration
config = FullConfig()
print(config.summary())
# Output: Frames: [evidential, aspectual, morphological, compositional] | VERIX: MODERATE | Compression: L1_AI_HUMAN

# Check active frames
print(config.framework.active_frames())
# Output: ['evidential', 'aspectual', 'morphological', 'compositional']

# Get frames sorted by weight
print(config.framework.get_weighted_frames())
# Output: [('evidential', 0.95), ('aspectual', 0.8), ('morphological', 0.65), ('compositional', 0.6)]
```

## Components

### Enums

#### `VerixStrictness`
VERIX compliance strictness levels:
- `RELAXED` (0): Only illocution required
- `MODERATE` (1): Illocution + confidence required
- `STRICT` (2): All fields required

#### `CompressionLevel`
VERIX output compression levels:
- `L0_AI_AI` (0): Emoji shorthand (machine-to-machine)
- `L1_AI_HUMAN` (1): Annotated format (human inspector)
- `L2_HUMAN` (2): Natural language (end user, lossy)

### Constants

#### `DEFAULT_FRAME_WEIGHTS`
Default weights for all 7 cognitive frames:
```python
{
    "evidential": 0.95,      # Turkish -mis/-di: "How do you know?"
    "aspectual": 0.80,       # Russian aspect: "Complete or ongoing?"
    "morphological": 0.65,   # Arabic roots: semantic decomposition
    "compositional": 0.60,   # German compounding: primitives to compounds
    "honorific": 0.35,       # Japanese keigo: audience calibration
    "classifier": 0.45,      # Chinese measure words: object comparison
    "spatial": 0.40,         # Guugu Yimithirr: absolute positioning
}
```

#### `DEFAULT_EVIDENTIAL_MINIMUM`
Minimum weight for evidential frame: `0.30`

### Dataclasses

#### `FrameworkConfig`
Configuration for which cognitive frames are active.

**Fields:**
- `evidential: bool = True` - Turkish -mis/-di (how do you know?)
- `aspectual: bool = True` - Russian pfv/ipfv (complete or ongoing?)
- `morphological: bool = True` - Arabic trilateral roots
- `compositional: bool = True` - German compounding
- `honorific: bool = False` - Japanese keigo
- `classifier: bool = False` - Chinese measure words
- `spatial: bool = False` - Guugu Yimithirr positioning
- `frame_weights: Dict[str, float]` - Weight overrides
- `evidential_minimum: float = 0.30` - Minimum evidential weight
- `max_frame_depth: int = 3` - Hofstadter recursion limit
- `frame_step_policy: str = "simpler"` - Nesting policy

**Methods:**
- `active_frames() -> List[str]` - Get list of active frame names
- `frame_count() -> int` - Get number of active frames
- `get_weighted_frames() -> List[Tuple[str, float]]` - Get frames sorted by weight
- `validate_weights() -> List[str]` - Validate weight configuration
- `set_frame_weight(name, weight)` - Set weight for a frame
- `validate_nesting(frame_stack) -> bool` - Validate frame nesting

#### `PromptConfig`
Configuration for VERIX epistemic notation.

**Fields:**
- `verix_strictness: VerixStrictness = MODERATE`
- `compression_level: CompressionLevel = L1_AI_HUMAN`
- `require_ground: bool = True` - Require evidence citations
- `require_confidence: bool = True` - Require confidence values
- `max_claim_depth: int = 3` - Maximum nested ground depth
- `require_confidence_decrease: bool = True` - Confidence must decrease

**Methods:**
- `is_strict() -> bool` - Check if strict mode
- `is_relaxed() -> bool` - Check if relaxed mode

#### `FullConfig`
Complete configuration combining framework and prompt settings.

**Fields:**
- `framework: FrameworkConfig`
- `prompt: PromptConfig`

**Methods:**
- `summary() -> str` - Human-readable summary

### VectorCodec Class

Stable mapping between FullConfig and 14-dimensional float vectors for multi-objective optimization.

**Vector Format (14 dimensions):**
- `[0-6]`: Frame toggles (evidential, aspectual, morphological, compositional, honorific, classifier, spatial)
- `[7]`: verix_strictness (0, 1, 2)
- `[8]`: compression_level (0, 1, 2)
- `[9]`: require_ground (0, 1)
- `[10]`: require_confidence (0, 1)
- `[11-13]`: Reserved for expansion

**Class Constants:**
- `VECTOR_SIZE = 14`
- `IDX_EVIDENTIAL = 0` through `IDX_RESERVED_3 = 13`

**Static Methods:**
- `encode(config: FullConfig) -> List[float]` - Config to vector
- `decode(vector: List[float]) -> FullConfig` - Vector to config
- `cluster_key(config: FullConfig) -> str` - Cache key for DSPy
- `distance(v1, v2) -> float` - Euclidean distance between vectors
- `interpolate(v1, v2, t) -> List[float]` - Linear interpolation

### Preset Configurations

- `DEFAULT_CONFIG` - Default (moderate strictness, common frames)
- `MINIMAL_CONFIG` - Minimal (evidential only, relaxed)
- `STRICT_CONFIG` - Strict (all frames, maximum strictness)

### Named Modes (Pareto-Optimal)

| Mode | Accuracy | Efficiency | Use Case |
|------|----------|------------|----------|
| `audit` | 0.960 | 0.763 | Code review, compliance |
| `speed` | 0.734 | 0.950 | Quick tasks, prototyping |
| `research` | 0.980 | 0.824 | Content analysis, deep work |
| `robust` | 0.960 | 0.769 | Production code, critical paths |
| `balanced` | 0.882 | 0.928 | General purpose |

**Functions:**
- `get_named_mode(name: str) -> FullConfig` - Get mode by name
- `create_audit_config() -> FullConfig`
- `create_speed_config() -> FullConfig`
- `create_research_config() -> FullConfig`
- `create_robust_config() -> FullConfig`
- `create_balanced_config() -> FullConfig`

**Dictionary:**
- `NAMED_MODES: Dict[str, FullConfig]` - All named modes

## Usage Examples

### Basic Configuration

```python
from cognitive_config import FullConfig, FrameworkConfig, PromptConfig

# Create custom config
config = FullConfig(
    framework=FrameworkConfig(
        evidential=True,
        aspectual=True,
        morphological=False,
        compositional=False,
        honorific=True,
        classifier=False,
        spatial=False,
    ),
    prompt=PromptConfig(
        verix_strictness=VerixStrictness.STRICT,
        compression_level=CompressionLevel.L1_AI_HUMAN,
        require_ground=True,
        require_confidence=True,
    ),
)
```

### Named Modes

```python
from cognitive_config import get_named_mode, NAMED_MODES

# Get specific mode
audit_config = get_named_mode("audit")

# List all modes
for name, config in NAMED_MODES.items():
    print(f"{name}: {config.summary()}")
```

### Multi-Objective Optimization

```python
from cognitive_config import FullConfig, VectorCodec

# Encode config for optimization
config = FullConfig()
vector = VectorCodec.encode(config)
print(f"14D vector: {vector}")

# Decode from optimization result
optimized_vector = [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0]
restored = VectorCodec.decode(optimized_vector)

# Find similar configurations
v1 = VectorCodec.encode(get_named_mode("audit"))
v2 = VectorCodec.encode(get_named_mode("speed"))
distance = VectorCodec.distance(v1, v2)
print(f"Distance between audit and speed: {distance}")

# Explore between configurations
midpoint = VectorCodec.interpolate(v1, v2, 0.5)
mid_config = VectorCodec.decode(midpoint)
```

### DSPy Caching

```python
from cognitive_config import FullConfig, VectorCodec

config = FullConfig()
cache_key = VectorCodec.cluster_key(config)
print(f"Cache key: {cache_key}")
# Output: frames:aspectual+compositional+evidential+morphological|strict:1|compress:1
```

### Frame Weight Management

```python
from cognitive_config import FrameworkConfig

framework = FrameworkConfig()

# Get weighted frames
weighted = framework.get_weighted_frames()
for name, weight in weighted:
    print(f"{name}: {weight}")

# Validate weights
errors = framework.validate_weights()
if errors:
    print(f"Validation errors: {errors}")

# Set custom weight
framework.set_frame_weight("aspectual", 0.90)

# Attempting to set evidential below minimum raises ValueError
try:
    framework.set_frame_weight("evidential", 0.20)
except ValueError as e:
    print(f"Error: {e}")
```

### Hofstadter Recursion Control

```python
from cognitive_config import FrameworkConfig

framework = FrameworkConfig(max_frame_depth=3, frame_step_policy="simpler")

# Valid nesting (complexity decreases)
valid_stack = ["compositional", "morphological", "evidential"]
print(framework.validate_nesting(valid_stack))  # True

# Invalid nesting (too deep)
deep_stack = ["compositional", "morphological", "aspectual", "evidential"]
print(framework.validate_nesting(deep_stack))  # False
```

## VERILINGUA Frame Reference

| Frame | Source Language | Cognitive Force | Markers |
|-------|-----------------|-----------------|---------|
| evidential | Turkish -mis/-di | "How do you know?" | `[witnessed]`, `[reported:src]`, `[inferred]`, `[assumed:conf]` |
| aspectual | Russian pfv/ipfv | "Complete or ongoing?" | `[complete]`, `[ongoing]`, `[habitual]` |
| morphological | Arabic roots | "What are components?" | `[root:X]`, `[derived:X->Y]` |
| compositional | German compounding | "Build from primitives" | `[primitive:X]`, `[compound:A+B]` |
| honorific | Japanese keigo | "Who is audience?" | `[audience:X]`, `[formality:level]` |
| classifier | Chinese measure words | "What type/count?" | `[type:X]`, `[measure:unit]` |
| spatial | Guugu Yimithirr | "Absolute position?" | `[path:file:line]`, `[direction:upstream]` |

## VERIX Grammar Reference

```
CLAIM := [illocution|affect] content [ground:source] [conf:X.XX] [state:status]
```

**Illocution Types:**
- `assert` - Factual claim
- `query` - Question
- `direct` - Instruction
- `commit` - Promise
- `express` - Attitude

**Affect Types:**
- `neutral`, `positive`, `negative`, `emphatic`, `uncertain`

**Ground Types:**
- `witnessed` - Direct observation
- `reported:source` - Secondhand
- `inferred` - Deduced
- `assumed:confidence` - Assumption

**Confidence Ceilings:**
- definition: 0.95
- observation: 0.95
- policy: 0.90
- research: 0.85
- report: 0.70
- inference: 0.70

**States:**
- `provisional` - May revise
- `confirmed` - Verified
- `retracted` - Withdrawn

## License

Extracted from Context Cascade. Use freely in any project.
