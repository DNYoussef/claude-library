# Component Library

## Canonical Status

<!-- STATUS:START -->
Canonical status from `2026-EXOSKELETON-STATUS.json`.

Status: TBD (source: manual)
Registry refreshed: 2026-01-14T07:37:15.658148+00:00
Signals: git=no, tests=yes, ci=no, readme=yes, last_commit=unknown
<!-- STATUS:END -->


A collection of reusable, production-ready components extracted from multiple projects.

**Version**: 1.3.0
**Last Updated**: 2026-01-10
**Components**: 69 | **Patterns**: 2 | **Total**: 71

---

## Quick Start

```python
# Trading components
from library.components.trading.circuit_breakers.circuit_breaker import CircuitBreaker
from library.components.trading.gate_system.gate_manager import GateManager
from library.components.trading.position_sizing.kelly_criterion import KellyCriterion

# Analysis components
from library.components.analysis.pattern_matcher.pattern_matcher import PatternMatcher
from library.components.validation.quality_validator.quality_validator import QualityValidator

# Security components
from library.components.security.jwt_auth.jwt_auth import JWTAuth

# Shared types (LEGO compatibility)
from library.common.types import Money, Severity, Violation, ValidationResult
```

---

## Component Categories

| Category | Count | Description |
|----------|-------|-------------|
| trading | 3 | Circuit breakers, gate system, Kelly criterion |
| analysis | 7 | Pattern matching, scoring, AST visitors, metrics |
| validation | 3 | Quality, spec, skill validators |
| cognitive | 8 | Skill/agent/command bases, VERIX parser, config |
| cognitive_architecture | 6 | Loopctl, modes, optimization, evals, integration |
| observability | 5 | Tagging, audit logging, OpenTelemetry, status registry, drift audit |
| security | 1 | JWT authentication |
| api | 2 | FastAPI router, Pydantic base models |
| auth | 2 | FastAPI JWT, Express JWT middleware |
| database | 2 | Connection pool, Prisma setup |
| http | 2 | Fetch API client, API services |
| ui | 3 | Radix dialog, dropdown, design system |
| testing | 3 | Backtest harness, pytest fixtures, jest setup |
| banking | 2 | Plaid client, Mercury integration |
| accounting | 2 | Transaction store, categorizer |
| payments | 1 | Stripe client |
| memory | 1 | Memory MCP client with circuit breaker |
| caching | 1 | Redis cache |
| messaging | 1 | Redis pub/sub |
| middleware | 1 | Express middleware chain |
| orchestration | 1 | Pipeline executor |
| pipelines | 1 | Content pipeline template |
| ai | 2 | Model router, consensus display |
| realtime | 1 | WebSocket connection manager |
| state | 1 | Kanban store (React) |
| react_auth | 1 | Auth context (React) |
| reporting | 1 | Report generator |
| parsing | 1 | Markdown metadata |
| scheduling | 1 | Task scheduler |
| multi_entity | 1 | Entity isolation |
| utilities | 4 | Quality gate, circuit breaker, health monitor, IO |
| patterns | 4 | Money handling, webhook idempotency, auditor base, image gen |

**Total**: 69 components + 2 top-level patterns = 71

---

## Architecture Principles

### LEGO Pattern
Each component is designed to be:
- **Self-contained**: All dependencies bundled locally
- **Copy-ready**: Can be extracted and used independently
- **Interface-compatible**: Uses shared types from `common/types.py`

### Shared Types
All components use types from `library/common/types.py`:
- `Severity`: CRITICAL, HIGH, MEDIUM, LOW, INFO
- `Money`: Decimal-based monetary values (NO FLOATS!)
- `Violation`: Standard violation format
- `ValidationResult`: Validation outcomes
- `QualityResult`: Quality analysis results
- `TaggedEntry`: WHO/WHEN/PROJECT/WHY tagged entries

### Thread Safety
Trading components use `threading.RLock` for thread-safe operations.

---

## Component Index

### Trading (Financial Systems)

| Component | Path | Purpose |
|-----------|------|---------|
| circuit_breakers | trading/circuit_breakers/ | 6-type protection triggers |
| gate_system | trading/gate_system/ | G0-G12 capital progression |
| position_sizing | trading/position_sizing/ | Kelly criterion calculator |

### Analysis (Code Quality)

| Component | Path | Purpose |
|-----------|------|---------|
| pattern_matcher | analysis/pattern_matcher/ | Regex/word boundary matching |
| ast_visitor | analysis/ast_visitor/ | Python AST visitors |
| ast_visitor_base | analysis/ast_visitor_base/ | Base AST analysis visitors |
| scoring_aggregator | analysis/scoring_aggregator/ | Score aggregation |
| statistical_analyzer | analysis/statistical_analyzer/ | Statistical metrics |
| violation_factory | analysis/violation_factory/ | SARIF violation creation |
| metric_collector | analysis/metric_collector/ | Metric collection |

### Validation

| Component | Path | Purpose |
|-----------|------|---------|
| quality_validator | validation/quality_validator/ | Evidence-based quality gates |
| spec_validation | validation/spec_validation/ | Spec file validation |
| skill_validator | validation/skill_validator/ | Skill/command validation |

### Cognitive (AI/LLM)

| Component | Path | Purpose |
|-----------|------|---------|
| skill_base | cognitive/skill_base/ | Skill base class |
| agent_base | cognitive/agent_base/ | Agent base class |
| command_base | cognitive/command_base/ | Command base class |
| playbook_base | cognitive/playbook_base/ | Playbook base class |
| hook_base | cognitive/hook_base/ | Hook base class |
| script_base | cognitive/script_base/ | Script base class |
| verix_parser | cognitive/verix_parser/ | VERIX notation parser |
| cognitive_config | cognitive/cognitive_config/ | Cognitive frame config |

### Security & Auth

| Component | Path | Purpose |
|-----------|------|---------|
| jwt_auth | security/jwt_auth/ | JWT tokens with refresh |
| fastapi_jwt | auth/fastapi_jwt/ | FastAPI JWT auth |
| jwt_middleware_ts | auth/jwt_middleware_ts/ | Express JWT middleware |

### Observability

| Component | Path | Purpose |
|-----------|------|---------|
| tagging_protocol | observability/tagging_protocol/ | WHO/WHEN/PROJECT/WHY tagging |
| audit_logging | observability/audit_logging/ | Structured audit logs |
| opentelemetry_lite | observability/opentelemetry_lite/ | Lightweight OTel |
| status_registry | observability/status_registry/ | Canonical project status |
| library_drift_audit | observability/library_drift_audit/ | Component drift audit |

### Memory

| Component | Path | Purpose |
|-----------|------|---------|
| memory_mcp_client | memory/memory_mcp_client/ | Memory MCP with circuit breaker |

### HTTP (Network)

| Component | Path | Purpose |
|-----------|------|---------|
| fetch_api_client | http/fetch_api_client/ | TypeScript fetch with retry |
| api_services | http/api_services/ | API service abstractions |

### Patterns (Base Classes)

| Component | Path | Purpose |
|-----------|------|---------|
| auditor_base | patterns/auditor_base/ | Abstract auditor pattern |
| image_generator_base | patterns/image_generator_base/ | Image gen abstraction |
| money_handling | patterns/money_handling/ | Decimal-only money |
| webhook_idempotency | patterns/webhook_idempotency/ | Idempotent webhook processing |

### Realtime

| Component | Path | Purpose |
|-----------|------|---------|
| websocket_manager | realtime/websocket_manager/ | WebSocket connections |

---

## Integration Testing

Run the integration test suite:

```bash
cd C:\Users\17175\.claude\library
python test_integration.py
```

**Expected Output**:
```
Results: 7 passed, 0 failed
All integration tests passed!
```

---

## Documentation

- [AUDIT-REPORT.md](AUDIT-REPORT.md) - Component audit findings
- [DEDUPLICATION-PLAN.md](DEDUPLICATION-PLAN.md) - Cross-project deduplication  
- [INTERFACE-MAPPING.md](INTERFACE-MAPPING.md) - Type mappings
- [STANDARD-SCAFFOLDS.md](STANDARD-SCAFFOLDS.md) - Canonical repo scaffolds
- [REPLACEMENT-MAP.md](REPLACEMENT-MAP.md) - Non-standard to standard mapping

---

## Contributing

When adding new components:
1. Follow LEGO pattern (self-contained)
2. Use types from `common/types.py`
3. Add README.md to component directory
4. Add tests in `tests/` subdirectory
5. Update this index
