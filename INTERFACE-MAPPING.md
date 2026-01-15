# Library Interface Mapping - LEGO Compatibility Spec

## Core Principle
Every component MUST import shared types from `library/common/types.py`.
NO component defines its own Severity, Money, or other shared types.

---

## SHARED TYPES MODULE (`library/common/types.py`)

### 1. Severity Enum (Used by: analysis, validation, reporting)
```python
class Severity(Enum):
    CRITICAL = "critical"  # P0 - Must fix immediately
    HIGH = "high"          # P1 - Fix before release
    MEDIUM = "medium"      # P2 - Fix soon
    LOW = "low"            # P3 - Nice to have
    INFO = "info"          # Informational only

    @property
    def weight(self) -> int:
        return {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}[self.value]

    def __lt__(self, other) -> bool:
        return self.weight < other.weight
```

### 2. Money Type (Used by: trading, banking, accounting)
```python
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self):
        if isinstance(self.amount, float):
            raise FloatNotAllowedError("Use Decimal, not float")
```

### 3. Result Types (Used by: all validation components)
```python
@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QualityResult:
    passed: bool
    score: float
    violations: List["Violation"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 4. Violation Type (Used by: analysis, quality, reporting)
```python
@dataclass
class Violation:
    severity: Severity
    message: str
    file_path: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    rule_id: Optional[str] = None
    suggestion: Optional[str] = None
```

### 5. Tagged Entry (Used by: memory, observability)
```python
@dataclass
class TaggedEntry:
    who: str                    # Agent identifier
    when: datetime              # ISO8601 timestamp
    project: str                # Project name
    why: str                    # Reason category
    content: Any                # The actual data
```

---

## COMPONENT TOUCH POINTS

### Analysis Domain
```
pattern-matcher -----> Violation (from common/types)
       |
       v
scoring-aggregator --> QualityResult (from common/types)
       |
       v
violation-factory ---> Violation, Severity (from common/types)
       |
       v
statistical-analyzer -> (standalone, no shared deps)
```

### Validation Domain
```
quality-validator ---> Severity, Violation, QualityResult (from common/types)
       |
       v
spec-validation -----> ValidationResult (from common/types)
       |
       v
skill-validator -----> ValidationResult (from common/types)
```

### Reporting Domain
```
report-generator ----> Severity, Violation (from common/types)
                       (imports FROM analysis components, not defines own)
```

### Trading Domain
```
circuit-breaker-trading --> Money (from common/types)
       |
       v
gate-system-manager -----> Money (from common/types)
       |
       v
kelly-criterion ---------> Money, Decimal (from common/types)
       |
       v
backtest-harness --------> Money (from common/types)
```

### Banking Domain
```
banking-models -------> Money (from common/types)
       |
       v
banking-plaid --------> Money, BankAccount (from banking-models)
       |
       v
stripe-integration ---> Money (from common/types)
       |
       v
mercury-integration --> Money (from common/types)
```

### Accounting Domain
```
accounting-transactions --> Money (from common/types)
       |
       v
accounting-categorizer --> Transaction (from accounting-transactions)
```

### Observability Domain
```
tagging-protocol -------> TaggedEntry (from common/types)
       |
       v
audit-logging ----------> TaggedEntry (from common/types)
       |
       v
opentelemetry-lite -----> (standalone OpenTelemetry types)
```

### Memory Domain
```
memory-mcp-client ------> TaggedEntry (from common/types)
```

---

## IMPORT RULES

### Rule 1: Shared types come from common/types
```python
# CORRECT
from library.common.types import Severity, Violation, Money

# WRONG - Never define locally
class Severity(Enum):  # NO!
```

### Rule 2: Domain components import from domain __init__
```python
# CORRECT
from library.components.trading import CircuitBreaker, GateManager

# WRONG - Direct file imports
from library.components.trading.circuit_breakers.trading_breakers import ...
```

### Rule 3: Cross-domain imports go through common/types
```python
# CORRECT - analysis uses common types
from library.common.types import Severity, Violation

# WRONG - importing another domain's internal types
from library.components.validation.quality_validator import Severity
```

---

## MISSING COMPONENTS TO EXTRACT

### From Trader AI (HIGH PRIORITY - Financial)
| Component | Location | Dependencies | Status |
|-----------|----------|--------------|--------|
| stripe-integration | components/payments/stripe/ | Money | DONE |
| mercury-integration | components/banking/mercury/ | Money | DONE |
| accounting/categorizer | components/accounting/categorizer/ | Transaction | DONE |
| multi-entity/isolation | components/multi-entity/isolation/ | None | DONE |

### From Life-OS Dashboard
| Component | Location | Dependencies | Status |
|-----------|----------|--------------|--------|
| pipeline-executor | components/orchestration/pipeline/ | None | DONE |
| task-scheduler | components/scheduling/tasks/ | None | DONE |
| websocket-manager | components/realtime/websocket-manager/ | None | DONE |

### From Life-OS Frontend
| Component | Location | Dependencies | Status |
|-----------|----------|--------------|--------|
| use-async-state | components/react-hooks/use-async-state/ | None | DONE |
| use-local-storage | components/react-hooks/use-local-storage/ | None | DONE |
| auth-context | components/react-auth/context/ | None | DONE |

### From Context Cascade
| Component | Location | Dependencies | Status |
|-----------|----------|--------------|--------|
| skill-base-class | components/cognitive/skill-base/ | None | DONE |
| agent-base-class | components/cognitive/agent-base/ | None | DONE |
| hook-system | components/cognitive/hook-base/ | None | DONE |
| command-parser | components/cognitive/command-base/ | None | DONE |
| playbook-base | components/cognitive/playbook-base/ | None | DONE |
| script-base | components/cognitive/script-base/ | None | DONE |

### From Connascence
| Component | Location | Dependencies | Status |
|-----------|----------|--------------|--------|
| ast-visitor-base | components/analysis/ast-visitor/ | Severity, Violation | DONE |
| metric-collector | components/analysis/metric-collector/ | Violation | DONE |

---

## FIX ORDER (Dependency-Aware)

1. **Create common/types.py** (no dependencies)
2. **Fix analysis components** (depend on common/types)
3. **Fix validation components** (depend on common/types)
4. **Fix reporting components** (depend on common/types + analysis)
5. **Fix trading components** (depend on common/types)
6. **Extract missing components** (all depend on common/types)

---

## VALIDATION CHECKLIST

Before marking any component DONE:
- [ ] Imports Severity from common/types (if uses severity)
- [ ] Imports Money from common/types (if uses money)
- [ ] Imports Violation from common/types (if uses violations)
- [ ] No local enum definitions that duplicate common/types
- [ ] __init__.py exports public interface
- [ ] Tests pass
- [ ] No circular imports
