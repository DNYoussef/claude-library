# Component Library

## Canonical Status

<!-- STATUS:START -->
Canonical status from `2026-EXOSKELETON-STATUS.json`.

Status: TBD (source: manual)
Registry refreshed: 2026-02-04T00:00:00+00:00
Signals: git=yes, tests=yes, ci=yes, readme=yes
<!-- STATUS:END -->


A collection of reusable, production-ready components extracted from multiple projects.

**Version**: 2.0.0
**Last Updated**: 2026-02-04
**Components**: 80 | **Domains**: 32

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
| cognitive | 15 | Skill/agent/command bases, VERIX parser, optimizer, modes, evals |
| analysis | 7 | Pattern matching, scoring, AST visitors, metrics, violations |
| testing | 5 | Backtest harness, pytest fixtures, jest setup |
| observability | 5 | Tagging protocol, audit logging, OpenTelemetry, status registry |
| patterns | 4 | Money handling, webhook idempotency, auditor base, image gen |
| utilities | 4 | Quality gate, circuit breaker, health monitor, IO helpers |
| trading | 3 | Circuit breakers, gate system, Kelly criterion |
| banking | 3 | Plaid client, Mercury integration, banking models |
| validation | 3 | Quality, spec, skill validators |
| api | 3 | FastAPI router, Pydantic base models, Express middleware |
| ui-components | 3 | Radix dialog, dropdown, design system |
| authentication | 2 | FastAPI JWT, Express JWT middleware |
| http | 2 | Fetch API client, API services |
| integrations | 2 | Content pipeline template, multi-model router |
| accounting | 2 | Transaction store, categorizer |
| realtime | 2 | WebSocket connection manager |
| ai | 1 | LLM Council consensus display |
| caching | 1 | Redis cache |
| database | 1 | Connection pool |
| governance | 1 | Guard lane base ABC |
| memory | 1 | Memory MCP client with circuit breaker |
| messaging | 1 | Redis pub/sub |
| multi-entity | 1 | Tenant isolation |
| orchestration | 1 | Pipeline executor |
| parsing | 1 | Markdown metadata parser |
| payments | 1 | Stripe client |
| react | 1 | React hooks library |
| react-auth | 1 | Auth context (React) |
| reporting | 1 | Report generator |
| scheduling | 1 | Task scheduler |
| security | 1 | JWT authentication |
| state | 1 | Kanban store (Zustand) |

**Total**: 80 components across 32 domains

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

### Cognitive Architecture (15 components)

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
| frozen_harness | cognitive_architecture/loopctl/ | Evaluation system |
| mode_library | cognitive_architecture/modes/ | Configuration modes |
| two_stage_optimizer | cognitive_architecture/optimization/ | Multi-objective optimizer |
| vcl_validator | cognitive_architecture/core/ | VCL validation |
| cli_evaluator | cognitive_architecture/evals/ | CLI evaluation |
| telemetry_bridge | cognitive_architecture/integration/ | Memory MCP bridge |
| connascence_bridge | cognitive_architecture/integration/ | Quality analyzer bridge |

### Analysis (7 components)

| Component | Path | Purpose |
|-----------|------|---------|
| pattern_matcher | analysis/pattern_matcher/ | Regex/word boundary matching |
| ast_visitor | analysis/ast_visitor/ | Python AST visitors |
| ast_visitor_base | analysis/ast_visitor_base/ | Base AST analysis visitors |
| scoring_aggregator | analysis/scoring_aggregator/ | Score aggregation |
| statistical_analyzer | analysis/statistical_analyzer/ | Statistical metrics |
| violation_factory | analysis/violation_factory/ | SARIF violation creation |
| metric_collector | analysis/metric_collector/ | Metric collection |

### Trading (3 components)

| Component | Path | Purpose |
|-----------|------|---------|
| circuit_breakers | trading/circuit_breakers/ | 6-type protection triggers |
| gate_system | trading/gate_system/ | G0-G12 capital progression |
| position_sizing | trading/position_sizing/ | Kelly criterion calculator |

### Validation (3 components)

| Component | Path | Purpose |
|-----------|------|---------|
| quality_validator | validation/quality_validator/ | Evidence-based quality gates |
| spec_validation | validation/spec_validation/ | Spec file validation |
| skill_validator | validation/skill_validator/ | Skill/command validation |

### Observability (5 components)

| Component | Path | Purpose |
|-----------|------|---------|
| tagging_protocol | observability/tagging_protocol/ | WHO/WHEN/PROJECT/WHY tagging |
| audit_logging | observability/audit_logging/ | Structured audit logs |
| opentelemetry_lite | observability/opentelemetry_lite/ | Lightweight OTel |
| status_registry | observability/status_registry/ | Canonical project status |
| library_drift_audit | observability/library_drift_audit/ | Component drift audit |

### Security & Auth (3 components)

| Component | Path | Purpose |
|-----------|------|---------|
| jwt_auth | security/jwt_auth/ | JWT tokens with refresh |
| fastapi_jwt | auth/fastapi_jwt/ | FastAPI JWT auth |
| jwt_middleware_ts | auth/jwt_middleware_ts/ | Express JWT middleware |

### Testing (5 components)

| Component | Path | Purpose |
|-----------|------|---------|
| backtest_harness | testing/backtest_harness/ | Trading backtest harness |
| pytest_fixtures | testing/pytest_fixtures/ | Python test fixtures |
| jest_setup | testing/jest_setup/ | JavaScript test setup |

### Memory & Caching (2 components)

| Component | Path | Purpose |
|-----------|------|---------|
| memory_mcp_client | memory/memory_mcp_client/ | Memory MCP with circuit breaker |
| redis_cache | caching/redis_cache/ | Redis cache layer |

### HTTP & Realtime (4 components)

| Component | Path | Purpose |
|-----------|------|---------|
| fetch_api_client | http/fetch_api_client/ | TypeScript fetch with retry |
| api_services | http/api_services/ | API service abstractions |
| websocket_manager | realtime/websocket_manager/ | WebSocket connections |

### Patterns (4 components)

| Component | Path | Purpose |
|-----------|------|---------|
| auditor_base | patterns/auditor_base/ | Abstract auditor pattern |
| image_generator_base | patterns/image_generator_base/ | Image gen abstraction |
| money_handling | patterns/money_handling/ | Decimal-only money |
| webhook_idempotency | patterns/webhook_idempotency/ | Idempotent webhook processing |

### Utilities (4 components)

| Component | Path | Purpose |
|-----------|------|---------|
| quality_gate | utilities/quality_gate/ | Quality gate system |
| circuit_breaker | utilities/circuit_breaker/ | Generic circuit breaker |
| health_monitor | utilities/health_monitor/ | Health check monitor |
| yaml_safe_write | utilities/io_helpers/ | Safe YAML operations |

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

- [CANONICAL-MECE-AUDIT.md](CANONICAL-MECE-AUDIT.md) - MECE audit and cleanup plan
- [catalog-index.json](catalog-index.json) - Component catalog (source of truth)
- [INTERFACE-MAPPING.md](INTERFACE-MAPPING.md) - Type mappings
- [STANDARD-SCAFFOLDS.md](STANDARD-SCAFFOLDS.md) - Canonical repo scaffolds

---

## Contributing

When adding new components:
1. Follow LEGO pattern (self-contained)
2. Use types from `common/types.py`
3. Add README.md to component directory
4. Add tests in `tests/` subdirectory
5. Run `python update_catalog.py` to update catalog-index.json
