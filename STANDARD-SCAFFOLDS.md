# Standard Scaffolds

This file defines the canonical repo layouts used across the exoskeleton. Use
these structures as the baseline for new repos and when normalizing legacy
ones. The library remains the single source of truth for scaffolds and shared
UI base.

## Backend service (Python/FastAPI)

Required:
- `README.md` with status block and run instructions
- `pyproject.toml` + lockfile
- `src/` with application package
- `tests/` with unit tests
- `.github/workflows/ci.yml`
- `.env.example`

Preferred:
- `docs/` with API and architecture notes
- `scripts/` for local dev tasks

Library references:
- Router template: `components/api/fastapi_router/`
- Quality gate: `components/utilities/quality_gate/quality_gate.py`
- Audit logging: `components/observability/audit_logging/`
- Telemetry bridge: `components/cognitive_architecture/integration/telemetry_bridge.py`
- Tagging protocol: `components/observability/tagging_protocol/`
- Memory MCP client v2: `components/memory/memory_mcp_client/`

## Frontend app (React/Tailwind)

Required:
- `README.md` with status block and run instructions
- `package.json` + lockfile
- `src/` with app code
- `tests/` for UI/unit tests (or `__tests__/`)
- `.github/workflows/ci.yml`

Preferred:
- `src/styles/` for tokens and theme
- `public/` for static assets

Library references:
- UI base: `components/ui/design_system/`
- Theme tokens: `components/ui/design_system/theme.css`
- Tagging protocol for client-side memory writes

## CLI tool

Required:
- `README.md` with status block and usage examples
- `package.json` or `pyproject.toml`
- `src/` + `tests/`
- `.github/workflows/ci.yml`

Preferred:
- `docs/` for commands, flags, and configuration

Library references:
- Audit logging
- Quality gate

## Worker/service (background jobs)

Required:
- `README.md`
- `src/` + `tests/`
- `.github/workflows/ci.yml`
- Observability hooks (audit logging + telemetry bridge)

## UI consolidation rule

All product UIs should use the shared design system and theme tokens from the
library. The only exception is `D:\Projects\dnyoussef-portfolio`, which must
remain isolated as the business site.
