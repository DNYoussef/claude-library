# VERIX Epistemic Notation Parser

A standalone Python library for parsing, validating, and creating VERIX-formatted epistemic claims.

## Overview

VERIX (VERIfied eXpression) is a structured notation system for expressing claims with explicit:
- **Confidence levels** (0.0 - 1.0)
- **Evidence sources** (ground)
- **Speech act types** (illocution)
- **Emotional valence** (affect)
- **Claim lifecycle states** (provisional, confirmed, retracted)

**Important:** This is a notation system for epistemic claims, NOT a formal verification system using SMT solvers.

## Installation

Copy this directory to your project or add to your Python path:

```python
import sys
sys.path.append('/path/to/verix-parser')
from verix_parser import VerixParser, create_claim
```

No external dependencies required - stdlib only.

## Quick Start

```python
from verix_parser import (
    VerixParser, VerixValidator, create_claim, format_claim,
    Illocution, Affect, State, Agent, CompressionLevel
)

# Parse existing VERIX text
parser = VerixParser()
claims = parser.parse("[assert|neutral] The API is stable [ground:tests] [conf:0.9] [state:confirmed]")

# Create new claims
claim = create_claim(
    content="The database connection is healthy",
    confidence=0.95,
    ground="health check endpoint",
    agent=Agent.PROCESS
)

# Format at different compression levels
print(format_claim(claim, CompressionLevel.L0_AI_AI))   # PA.95:The database conne...
print(format_claim(claim, CompressionLevel.L1_AI_HUMAN)) # [agent:process] [assert|neutral] ...
print(format_claim(claim, CompressionLevel.L2_HUMAN))   # Process output shows I'm highly confident that...

# Validate claims
validator = VerixValidator()
is_valid, violations = validator.validate(claims)
score = validator.compliance_score(claims)
```

## Grammar Specification

### Full VERIX Statement Grammar

```
STATEMENT := [META]? [AGENT]? [ID]? ILLOCUTION AFFECT CONTENT [GROUND]? [CONFIDENCE]? [STATE]?

META       := "[meta]" | "[meta:verix]"
AGENT      := "[agent:" AGENT_TYPE "]"
ID         := "[id:" IDENTIFIER "]"
ILLOCUTION := "[" SPEECH_ACT "|" VALENCE "]"
CONTENT    := <any text>
GROUND     := "[ground:" SOURCE "]"
CONFIDENCE := "[conf:" NUMBER "]"
STATE      := "[state:" LIFECYCLE "]"
```

### L1 Format (Annotated - Human Inspector)

Full format with all markers:

```
[meta:verix] [agent:model] [id:claim-1] [assert|neutral] This is my claim [ground:test-suite] [conf:0.85] [state:confirmed]
```

Minimal valid L1:

```
[assert|neutral] This is my claim
```

### L0 Format (Shorthand - Machine Communication)

Compact format: `{AGENT?}{ILLOCUTION}{AFFECT}{CONF%}:{CONTENT}`

```
MA+85:This is my claim...
```

Where:
- Agent: M=model, U=user, S=system, D=doc, P=process (optional)
- Illocution: A=assert, ?=query, !=direct, C=commit, E=express
- Affect: .=neutral, +=positive, -=negative, ~=uncertain
- Confidence: 0-100 (percentage)

### L2 Format (Natural Language - End User)

Human-readable prose (cannot be parsed back):

```
I'm fairly confident that this is my claim (based on test-suite).
```

## Component Reference

### Illocution Types (Speech Acts)

| Value | Description | Use Case |
|-------|-------------|----------|
| `ASSERT` | Making a factual claim | "The function returns 42" |
| `QUERY` | Asking a question | "What is the return value?" |
| `DIRECT` | Giving an instruction | "Run the test suite" |
| `COMMIT` | Making a promise | "I will fix this bug" |
| `EXPRESS` | Expressing emotion | "This code is elegant" |

### Affect Types (Emotional Valence)

| Value | Description | L0 Symbol |
|-------|-------------|-----------|
| `NEUTRAL` | No emotional loading | `.` |
| `POSITIVE` | Favorable stance | `+` |
| `NEGATIVE` | Unfavorable stance | `-` |
| `UNCERTAIN` | Epistemic uncertainty | `~` |

### Ground Types (Evidence Sources)

Ground values are free-form strings describing the evidence source:

| Pattern | Meaning |
|---------|---------|
| `witnessed` | Direct observation |
| `reported:SOURCE` | Secondhand from source |
| `inferred` | Deduced from evidence |
| `assumed:CONF` | Assumption with confidence |
| `test-suite` | Test results |
| `documentation` | From docs |
| `user-input` | User provided |

### Confidence Scoring

Confidence is a float from 0.0 to 1.0:

| Range | L2 Phrase | Use Case |
|-------|-----------|----------|
| 0.0 - 0.3 | "I'm quite uncertain, but" | Speculation |
| 0.3 - 0.5 | "I think" | Low confidence |
| 0.5 - 0.7 | "I believe" | Moderate confidence |
| 0.7 - 0.9 | "I'm fairly confident that" | High confidence |
| 0.9 - 1.0 | "I'm highly confident that" | Very high confidence |

**Confidence Ceilings by Agent Type:**

| Agent | Ceiling | Rationale |
|-------|---------|-----------|
| MODEL | 0.95 | AI epistemic humility |
| DOC | 0.98 | Documentation authority |
| PROCESS | 0.99 | Computed precision |
| SYSTEM | 0.95 | System reliability |
| USER | 1.0 | Human unrestricted |

### State Lifecycle

| Value | Description |
|-------|-------------|
| `PROVISIONAL` | Initial claim, may be revised |
| `CONFIRMED` | Verified, high confidence |
| `RETRACTED` | Withdrawn/invalidated |

### Agent Types

| Value | Description | L0 Symbol |
|-------|-------------|-----------|
| `MODEL` | AI model claim | `M` |
| `USER` | User stated | `U` |
| `SYSTEM` | System generated | `S` |
| `DOC` | Documentation | `D` |
| `PROCESS` | Computed/process | `P` |

### Meta Levels (Hofstadter Self-Reference)

| Level | Value | Description |
|-------|-------|-------------|
| 1 | `OBJECT` | Claims about the world (default) |
| 2 | `META` | Claims about other claims |
| 3 | `META_VERIX` | Claims about VERIX itself |

## API Reference

### Classes

#### `VerixParser`

Parse VERIX-formatted text into claim objects.

```python
parser = VerixParser(config=None)
claims = parser.parse(text)           # Parse multiple claims
claim = parser.parse_single(text)     # Parse single claim
```

#### `VerixValidator`

Validate claims against configuration requirements.

```python
validator = VerixValidator(config=None)
is_valid, violations = validator.validate(claims)
score = validator.compliance_score(claims)
cycles = validator.detect_ground_cycles(claims)
```

#### `VerixClaim`

Data class representing a parsed claim.

```python
claim.illocution      # Illocution enum
claim.affect          # Affect enum
claim.content         # str
claim.ground          # Optional[str]
claim.confidence      # float
claim.state           # State enum
claim.agent           # Optional[Agent]
claim.meta_level      # MetaLevel enum
claim.claim_id        # Optional[str]

claim.is_high_confidence(threshold=0.8)  # bool
claim.is_grounded()                       # bool
claim.is_meta()                           # bool
claim.is_meta_verix()                     # bool
claim.to_l0()                             # str
claim.to_l1()                             # str
claim.to_l2()                             # str
claim.to_dict()                           # dict
```

#### `PromptConfig`

Configuration for validation strictness.

```python
config = PromptConfig(
    verix_strictness=VerixStrictness.MODERATE,
    compression_level=CompressionLevel.L1_AI_HUMAN,
    require_ground=True,
    require_confidence=True,
    max_claim_depth=3,
    require_confidence_decrease=True
)
```

### Functions

#### `create_claim()`

Create a new VERIX claim with defaults.

```python
claim = create_claim(
    content="My assertion",
    illocution=Illocution.ASSERT,
    affect=Affect.NEUTRAL,
    ground="evidence",
    confidence=0.8,
    state=State.PROVISIONAL,
    agent=Agent.MODEL,
    meta_level=MetaLevel.OBJECT,
    claim_id="claim-1"
)
```

#### `create_meta_claim()`

Create a meta-level claim about another claim.

```python
meta = create_meta_claim(
    content="This claim is well-supported",
    about_claim=original_claim,
    confidence=0.7
)
```

#### `create_meta_verix_claim()`

Create a claim about VERIX notation itself.

```python
meta_verix = create_meta_verix_claim(
    content="VERIX enables epistemic hygiene",
    ground="verix-spec-v1.0",
    confidence=0.8
)
```

#### `format_claim()`

Format a claim at a specified compression level.

```python
l0 = format_claim(claim, CompressionLevel.L0_AI_AI)
l1 = format_claim(claim, CompressionLevel.L1_AI_HUMAN)
l2 = format_claim(claim, CompressionLevel.L2_HUMAN)
```

## Examples

### Parsing L1 Format

```python
from verix_parser import VerixParser

parser = VerixParser()

# Full L1 format
text = """
[agent:model] [assert|neutral] The API returns JSON [ground:api-docs] [conf:0.95] [state:confirmed]
[agent:user] [query|uncertain] Does it support pagination? [conf:0.6] [state:provisional]
"""

claims = parser.parse(text)
for claim in claims:
    print(f"{claim.illocution.value}: {claim.content} [{claim.confidence}]")
```

### Creating and Validating Claims

```python
from verix_parser import (
    create_claim, VerixValidator, PromptConfig,
    VerixStrictness, Agent, State
)

# Create claims
claim1 = create_claim(
    "Database connection pooling is enabled",
    confidence=0.9,
    ground="config file inspection",
    agent=Agent.PROCESS,
    state=State.CONFIRMED
)

claim2 = create_claim(
    "This improves performance",
    confidence=0.7,
    agent=Agent.MODEL
)

# Validate with strict config
config = PromptConfig(
    verix_strictness=VerixStrictness.STRICT,
    require_ground=True
)
validator = VerixValidator(config)

is_valid, violations = validator.validate([claim1, claim2])
print(f"Valid: {is_valid}")
for v in violations:
    print(f"  - {v}")
```

### Cycle Detection

```python
from verix_parser import create_claim, VerixValidator

# Create claims with circular ground references
claim_a = create_claim("Claim A", ground="claim-b", claim_id="claim-a")
claim_b = create_claim("Claim B", ground="claim-a", claim_id="claim-b")

validator = VerixValidator()
cycles = validator.detect_ground_cycles([claim_a, claim_b])
print(f"Cycles detected: {cycles}")
# Output: ['claim-a -> claim-b -> claim-a']
```

### Meta-Level Claims

```python
from verix_parser import create_claim, create_meta_claim, create_meta_verix_claim

# Object-level claim
base_claim = create_claim(
    "The cache hit rate is 95%",
    confidence=0.98,
    ground="metrics dashboard",
    claim_id="perf-1"
)

# Meta-level claim about the base claim
meta = create_meta_claim(
    "This performance metric is reliable",
    about_claim=base_claim,
    confidence=0.85
)

# Meta-VERIX claim about the notation itself
meta_verix = create_meta_verix_claim(
    "VERIX meta-levels enable reasoning about reasoning",
    ground="hofstadter-geb",
    confidence=0.75
)

print(base_claim.to_l1())
print(meta.to_l1())
print(meta_verix.to_l1())
```

## Exported Symbols

### Enums
- `Illocution` - Speech act types (ASSERT, QUERY, DIRECT, COMMIT, EXPRESS)
- `Affect` - Emotional valence (NEUTRAL, POSITIVE, NEGATIVE, UNCERTAIN)
- `State` - Claim lifecycle (PROVISIONAL, CONFIRMED, RETRACTED)
- `Agent` - Claim source (MODEL, USER, SYSTEM, DOC, PROCESS)
- `MetaLevel` - Self-reference level (OBJECT, META, META_VERIX)
- `VerixStrictness` - Validation strictness (RELAXED, MODERATE, STRICT)
- `CompressionLevel` - Output format (L0_AI_AI, L1_AI_HUMAN, L2_HUMAN)

### Data Classes
- `VerixClaim` - Parsed claim with all components
- `PromptConfig` - Validation configuration

### Classes
- `VerixParser` - Parse VERIX text to claims
- `VerixValidator` - Validate claims against requirements

### Functions
- `create_claim()` - Create new claims with defaults
- `create_meta_claim()` - Create meta-level claims
- `create_meta_verix_claim()` - Create claims about VERIX
- `format_claim()` - Format claims at compression levels

## Version

Current version: 1.0.0

## License

MIT License - Part of the Context Cascade cognitive architecture.
