# Component Library Inventory

Generated from `catalog-index.json` - the single source of truth.

**Total Components**: 80 | **Domains**: 32 | **Last Updated**: 2026-02-04

---

## Python Components

| Module | Purpose | Domain | Quality Score |
|--------|---------|--------|---------------|
| accounting/categorizer | Transaction Categorizer | accounting | 84 |
| accounting/transactions | Transaction Store | accounting | 85 |
| analysis/ast_visitor | AST Visitor Base | analysis | 93 |
| analysis/ast_visitor_base | AST Visitor Base Pattern | analysis | 88 |
| analysis/metric_collector | Metric Collector | analysis | 91 |
| analysis/pattern_matcher | Pattern Matcher | analysis | 90 |
| analysis/scoring_aggregator | Scoring Aggregator | analysis | 86 |
| analysis/statistical_analyzer | Statistical Analyzer | analysis | 86 |
| analysis/violation_factory | Violation Factory | analysis | 88 |
| api/fastapi_router | FastAPI CRUD Router | api | 88 |
| api/pydantic_base | Pydantic Base Models | api | 92 |
| auth/fastapi_jwt | FastAPI JWT Authentication | authentication | 88 |
| banking/mercury | Mercury Bank Integration | banking | 85 |
| banking/plaid | Plaid Banking Integration | banking | 85 |
| caching/redis_cache | Redis Cache Layer | caching | 88 |
| cognitive/agent_base | Agent Base Class | cognitive | 90 |
| cognitive/cognitive_config | Cognitive Frame Configuration | cognitive | 86 |
| cognitive/command_base | Command Base Class | cognitive | 88 |
| cognitive/hook_base | Hook Base Class | cognitive | 87 |
| cognitive/playbook_base | Playbook Base Class | cognitive | 89 |
| cognitive/script_base | Script Base Class | cognitive | 85 |
| cognitive/skill_base | Skill Base Class | cognitive | 92 |
| cognitive/verix_parser | VERIX Epistemic Parser | cognitive | 90 |
| cognitive_architecture/core | VCL Validator | cognitive | 90 |
| cognitive_architecture/evals | CLI Evaluator | cognitive | 70 |
| cognitive_architecture/integration | Integration Bridges | cognitive | 70-75 |
| cognitive_architecture/loopctl | FrozenHarness Evaluation | cognitive | 80 |
| cognitive_architecture/modes | Mode Library | cognitive | 85 |
| cognitive_architecture/optimization | Two-Stage Optimizer | cognitive | 75 |
| database/connection_pool | Database Connection Pool | database | 85 |
| governance/guard_lane_base | Guard Lane Base ABC | governance | 95 |
| memory/memory_mcp_client | Memory MCP Client v2 | memory | 90 |
| messaging/redis_pubsub | Redis Pub/Sub Manager | messaging | 90 |
| multi_entity/isolation | Multi-Entity Tenant Isolation | multi-entity | 91 |
| observability/audit_logging | Audit Logging System | observability | 86 |
| observability/library_drift_audit | Library Drift Audit | observability | 85 |
| observability/opentelemetry_lite | OpenTelemetry Lite Wrapper | observability | 82 |
| observability/status_registry | Status Registry | observability | 85 |
| observability/tagging_protocol | WHO/WHEN/PROJECT/WHY Tagging | observability | 88 |
| orchestration/pipeline_executor | Pipeline Executor | orchestration | 90 |
| parsing/markdown_metadata | Markdown Metadata Parser | parsing | 88 |
| patterns/auditor_base | Auditor Base Pattern | patterns | 85 |
| patterns/image_generator_base | Image Generator Base Pattern | patterns | 82 |
| payments/stripe | Stripe Payment Integration | payments | 90 |
| pipelines/content_pipeline | Content Pipeline Template | integrations | 70 |
| reporting/report_generator | Report Generator | reporting | 84 |
| scheduling/task_scheduler | Task Scheduler | scheduling | 88 |
| security/jwt_auth | Security JWT Authentication | security | 92 |
| testing/backtest_harness | Backtest Harness | testing | 88 |
| testing/pytest_fixtures | Pytest Fixtures Collection | testing | 90-100 |
| trading/circuit_breakers | Trading Circuit Breakers | trading | 92 |
| trading/gate_system | Gate System Manager | trading | 90 |
| trading/position_sizing | Kelly Criterion Calculator | trading | 94 |
| utilities/circuit_breaker | Circuit Breaker Pattern | utilities | 90 |
| utilities/health_monitor | Health Check Monitor | utilities | 80 |
| utilities/io_helpers | YAML Safe Write | utilities | 95 |
| utilities/quality_gate | Quality Gate System | utilities | 85 |
| validation/quality_validator | Quality Validator | validation | 90 |
| validation/skill_validator | Skill Validator | validation | 84 |
| validation/spec_validation | Spec Validation Framework | validation | 92 |

---

## TypeScript Components

| Module | Purpose | Domain | Quality Score |
|--------|---------|--------|---------------|
| ai/consensus_display | LLM Council Consensus Display | ai | 78 |
| ai/model_router | Multi-Model Router | integrations | 82 |
| auth/jwt_middleware_ts | JWT Authentication Middleware | authentication | 90 |
| http/api_services | API Service Layer | http | 82 |
| http/fetch_api_client | Fetch API Client | http | 88 |
| middleware/express_chain | Express Middleware Chain | api | 85 |
| react_auth/context | React Auth Context | react-auth | 89 |
| react_hooks | React Hooks Library | react | 88 |
| realtime/websocket_manager | WebSocket Connection Manager | realtime | 88-90 |
| state/kanban_store | Kanban Store (Zustand) | state | 85 |
| testing/jest_setup | Jest Setup Collection | testing | 88-100 |
| ui/design_system | Design System Components | ui-components | 80 |
| ui/radix_dialog | Radix Dialog Component | ui-components | 85 |
| ui/radix_dropdown | Radix Dropdown Menu Component | ui-components | 85 |

---

## Top-Level Patterns

| Pattern | Location | Purpose | Quality Score |
|---------|----------|---------|---------------|
| money_handling | patterns/money_handling/ | Decimal-only money handling | 95 |
| webhook_idempotency | patterns/webhook_idempotency/ | Idempotent webhook processing | 90 |

---

## Key Exports by Category

### Shared Types (common/types.py)
```python
from library.common.types import (
    Severity,           # CRITICAL, HIGH, MEDIUM, LOW, INFO
    Money,              # Decimal-based monetary values
    Violation,          # Standard violation format
    ValidationResult,   # Validation outcomes
    QualityResult,      # Quality analysis results
    TaggedEntry,        # WHO/WHEN/PROJECT/WHY tagged entries
    ConfidenceLevel,    # CERTAIN, HIGHLY_CONFIDENT, CONFIDENT, UNCERTAIN
    InputContract,      # Input contract dataclass
    OutputContract,     # Output contract dataclass
)
```

### Analysis Components
```python
from library.components.analysis.pattern_matcher.pattern_matcher import PatternMatcher
from library.components.analysis.violation_factory.violation_factory import ViolationFactory, Location
from library.components.analysis.scoring_aggregator.scoring_aggregator import ScoringAggregator
from library.components.analysis.metric_collector.metric_collector import MetricCollector
```

### Trading Components
```python
from library.components.trading.circuit_breakers.circuit_breaker import CircuitBreaker, CircuitBreakerManager
from library.components.trading.gate_system.gate_manager import GateManager
from library.components.trading.position_sizing.kelly import KellyCriterion
```

### Cognitive Components
```python
from library.components.cognitive.skill_base.skill_base import SkillBase
from library.components.cognitive.agent_base.agent_base import AgentBase
from library.components.cognitive.verix_parser.verix_parser import VerixParser
```

### Observability Components
```python
from library.components.observability.tagging_protocol.tagging_protocol import (
    TaggingProtocol,
    Intent,
    AgentCategory,
    create_tagger,
)
```

### Validation Components
```python
from library.components.validation.quality_validator.quality_validator import QualityValidator
from library.components.validation.spec_validation.spec_validation import SpecValidator
```

---

## Notes

- All Python components use shared types from `common/types.py`
- TypeScript components use types from `common/types.ts`
- Quality scores are from catalog-index.json (0-100 scale)
- Components follow LEGO pattern (self-contained, copy-ready)
