# Replacement Map (Non-Standard -> Library Standard)

Use this table to replace custom or legacy modules with canonical library
components. This is the authoritative mapping for standardization passes.

| Legacy or custom module | Replace with | Library location | Notes |
| --- | --- | --- | --- |
| custom memory client | memory-mcp-client-v2 | `components/memory/memory_mcp_client/` | Required for all MCP write/read integrations |
| ad-hoc tagging schema | tagging-protocol | `components/observability/tagging_protocol/` | Enforce WHO/WHEN/PROJECT/WHY metadata |
| bespoke quality gate | quality-gate | `components/utilities/quality_gate/quality_gate.py` | Standard validation and release gate |
| custom audit logger | audit-logging | `components/observability/audit_logging/` | Unified structured audit events |
| custom telemetry hooks | telemetry-bridge | `components/cognitive_architecture/integration/telemetry_bridge.py` | Bridge runtime metrics to observability |
| custom connascence link | connascence-bridge | `components/cognitive_architecture/integration/connascence_bridge.py` | Required for code repos with connascence analysis |
| bespoke metrics collection | metric-collector | `components/analysis/metric_collector/` | Standard metrics + aggregation |
| custom violation builders | violation-factory | `components/analysis/violation_factory/` | Standardize compliance/quality findings |
| custom FastAPI routers | fastapi-router-template | `components/api/fastapi_router/` | Base API router template |
| custom pipelines | content-pipeline-template | `components/pipelines/content_pipeline/` | Base pipeline template |

## Replacement rules

1. Prefer replacement over patching legacy modules.
2. If a module is shared across multiple repos, replace it in the library
   first, then propagate downstream.
3. Record any unavoidable deviations in the repo README and keep the delta
   minimal.
