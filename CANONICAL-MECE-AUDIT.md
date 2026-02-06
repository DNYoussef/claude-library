# Canonical MECE Audit - Claude Library (Copy-Paste Mode)

Date: 2026-02-04
Scope: C:\Users\17175\.claude\library (components, patterns, catalog, tooling)
Intent: Identify all issues that reduce copy-paste interoperability, token savings, or portability.

Assumptions (from user):
- This is a copy-paste library (not an installable package).
- Memory MCP is optional and should not be required by default.
- Legacy paths and legacy exports should be deleted (no backward-compat burden).

Summary Metrics (observed)
- Catalog index reports 81 components.
- README reports 69 components.
- Unique component locations in catalog index: 80.
- Component dirs with README.md: 78.
- Missing README for 4 components:
  - components/cognitive_architecture/modes/library.py
  - components/cognitive_architecture/core/vcl_validator.py
  - components/cognitive_architecture/optimization/two_stage_optimizer.py
  - components/cognitive_architecture/evals/cli_evaluator.py
- Missing tests for 2 components:
  - components/banking/models.py
  - components/governance/guard_lane_base/
- Repo hygiene: 134 __pycache__ dirs, 231 .pyc files, plus node_modules.

-----------------------------------------------------------------------
MECE FINDINGS (Grouped by Category)
-----------------------------------------------------------------------

A. Portability and Copy-Paste Readiness

A1. Hard-coded absolute paths
- Severity: High
- Evidence:
  - update_catalog.py uses C:/Users/17175/.claude/library/catalog.json
  - restructure_catalog.py uses C:\Users\17175\.claude\library
  - scripts/deploy_component.py hard-codes project paths
  - README files include absolute C:\Users\17175 paths
- Impact: Breaks copy-paste portability. Forces local-only execution and invalidates docs for other machines.
- Dependencies/Blockers: Blocks any scripted reuse outside this device.
- Recommendation: Replace absolute paths with relative paths and/or env vars. Provide a single config file for root paths.

A2. Import-time side effects in components
- Severity: High
- Evidence: components/cognitive_architecture/optimization/two_stage_optimizer.py modifies sys.path and loads .env at import.
- Impact: Copy-paste use causes hidden side effects, surprising users and contaminating runtime state.
- Dependencies/Blockers: Blocks safe reuse in production code.
- Recommendation: Move side effects behind __main__ or explicit functions. Keep imports pure.

A3. Project-coupled dependencies in components
- Severity: High
- Evidence: components/governance/guard_lane_base depends on src.schema.council.enums from life-os-dashboard.
- Impact: Not portable. Copy-paste fails without that project.
- Dependencies/Blockers: Blocks cross-project reuse unless dependency is removed or abstracted.
- Recommendation: Extract dependent enums into this component or provide minimal local stubs.

B. Interoperability Contract (Shared Types and Protocols)

B1. Shared types are duplicated across components
- Severity: Critical
- Evidence:
  - components/api/pydantic_base/base_models.py
  - components/analysis/violation_factory/violation_factory.py
  - components/reporting/report_generator/report_generator.py
  - components/auth/fastapi_jwt/jwt_auth.py
  - components/banking/mercury/client.py
  - components/payments/stripe/client.py
- Impact: Severity and Money instances become incompatible across components. Violates INTERFACE-MAPPING.md and breaks "LEGO" composition.
- Dependencies/Blockers: Blocks reliable interop between analysis, validation, reporting, finance.
- Recommendation: Remove fallback duplicates. For copy-paste, include common/types.py alongside any component that needs shared types.

B2. Tagging protocol fork (canonical vs Memory MCP variant)
- Severity: Critical
- Evidence:
  - components/observability/tagging_protocol/tagging_protocol.py (canonical)
  - components/memory/memory_mcp_client/tagging_protocol.py (fork)
- Impact: Divergent enums and payload shapes. Cross-component metadata becomes inconsistent.
- Dependencies/Blockers: Blocks unified logging, audit, and memory indexing.
- Recommendation: Keep a single canonical tagging protocol. Add a thin Memory MCP adapter layer instead of a fork.

C. Module Layout and Naming (Importability)

C1. Hyphenated Python directories
- Severity: Critical
- Evidence:
  - components/compute/two-stage-optimizer/
  - components/testing/pytest-fixtures/
- Impact: Invalid Python identifiers; cannot be imported without path hacks. Copy-paste causes broken imports.
- Dependencies/Blockers: Blocks any import-based reuse.
- Recommendation: Rename to snake_case (two_stage_optimizer, pytest_fixtures) and update references.

C2. Missing __init__.py in many package dirs
- Severity: High
- Evidence: 60 dirs with .py files but no __init__.py (includes core dirs like components/cognitive_architecture/core).
- Impact: Inconsistent packaging. Some tools and IDEs fail to resolve imports reliably.
- Dependencies/Blockers: Blocks consistent import paths for copy-paste usage.
- Recommendation: Add __init__.py to all Python package directories that are intended to be importable.

C3. No top-level components package
- Severity: Medium
- Evidence: .claude/library/components/__init__.py does not exist.
- Impact: Library-wide import patterns are inconsistent (README uses library.components.*).
- Dependencies/Blockers: Makes integration patterns ambiguous.
- Recommendation: Provide components/__init__.py that defines public exports for copy-paste users.

C4. Duplicate or legacy component variants
- Severity: Medium
- Evidence:
  - React hooks: useLocalStorage.ts and use-local-storage.ts; useAsyncState.ts and use-async-state.ts; legacy exports in components/react_hooks/index.ts.
  - React auth: components/react_auth and components/react_auth/context both export similar APIs.
  - Two-stage optimizer appears in compute and cognitive_architecture with different implementations.
- Impact: Drift risk, unclear canonical sources, larger token footprint.
- Dependencies/Blockers: Blocks single-source-of-truth usage and increases maintenance.
- Recommendation: Delete legacy variants; declare a single canonical path per component.

D. Catalog, Inventory, and Documentation Integrity

D1. Catalog/README mismatch
- Severity: High
- Evidence: README reports 69 components; catalog-index.json reports 81; unique catalog locations: 80.
- Impact: Users cannot trust counts or completeness.
- Dependencies/Blockers: Blocks reliable discovery of components for copy-paste use.
- Recommendation: Choose catalog-index.json as source of truth; regenerate README and INVENTORY from it.

D2. Broken catalog scripts
- Severity: High
- Evidence: update_catalog.py and restructure_catalog.py expect catalog.json which does not exist.
- Impact: Automation is dead; future updates are manual and error-prone.
- Dependencies/Blockers: Blocks repeatable updates and auditing.
- Recommendation: Update scripts to use catalog-index.json and catalog-full-backup.json, or regenerate catalog.json.

D3. INVENTORY.md export noise
- Severity: Medium
- Evidence: INVENTORY.md includes junk export strings like "export {" and "export type {", not valid API lists.
- Impact: Inventory is not actionable for users.
- Dependencies/Blockers: Blocks quick copy-paste selection.
- Recommendation: Regenerate inventory via static analysis with clean export lists.

D4. Docs include device-specific commands and paths
- Severity: Medium
- Evidence: Multiple READMEs include absolute C:\Users\17175 paths.
- Impact: Copy-paste instructions do not work on other machines.
- Dependencies/Blockers: Blocks portability.
- Recommendation: Replace with relative or environment-variable based paths.

E. Dependency Management (Python and TS)

E1. Python extras incomplete or mismatched
- Severity: High
- Evidence:
  - banking/mercury uses httpx but banking extra lacks httpx
  - realtime/messaging require redis but no messaging extra
  - cognitive_architecture/optimization uses numpy but no numpy dependency
  - "cache" extra name does not match domain "caching"
- Impact: Copy-paste users install wrong dependencies and hit runtime errors.
- Dependencies/Blockers: Blocks quick adoption.
- Recommendation: Align extras with component domains and actual imports.

E2. TS dependencies missing
- Severity: High
- Evidence: package.json lists only vitest, but components use React and likely Radix UI.
- Impact: TS components are not runnable out of the box.
- Dependencies/Blockers: Blocks use of UI components.
- Recommendation: Add minimal peer dependency list and a tsconfig.json.

F. Repo Hygiene and Tooling Stability

F1. Reserved device file breaks tooling
- Severity: High
- Evidence: components/nul causes rg errors on Windows.
- Impact: Tooling fails; audits and scripts break.
- Dependencies/Blockers: Blocks automated scanning and QA.
- Recommendation: Delete components/nul immediately.

F2. Build artifacts in repo
- Severity: High
- Evidence: node_modules, __pycache__, .pyc, .pytest_cache, .benchmarks.
- Impact: Bloats repo, slows tools, and introduces platform-specific noise.
- Dependencies/Blockers: Blocks clean copy-paste and audit reproducibility.
- Recommendation: Remove artifacts and add to .gitignore or cleanup script.

G. Testing and Coverage

G1. Missing tests for some components
- Severity: Medium
- Evidence: banking/models.py and governance/guard_lane_base have no tests.
- Impact: Lower confidence for reuse; portability risk.
- Dependencies/Blockers: Not a hard blocker, but reduces trust.
- Recommendation: Add minimal smoke tests for each component.

G2. Integration tests cover only a subset
- Severity: Low
- Evidence: README integration tests cover 7 components out of 80.
- Impact: False sense of completeness.
- Dependencies/Blockers: Not a blocker, but misleading.
- Recommendation: Expand integration test suite or scope statements.

-----------------------------------------------------------------------
DEPENDENCIES AND BLOCKERS (Fix Order)
-----------------------------------------------------------------------

Blockers (must fix first)
1) Remove components/nul (tooling break).
2) Remove hyphenated Python dirs or rename them (import break).
3) Eliminate shared type duplicates and tagging protocol fork (interop break).

Phase 1 (Portability core)
- Replace absolute paths with relative paths or env config.
- Remove import-time side effects in components.
- Remove project-coupled dependencies or isolate them behind adapters.

Phase 2 (Structure and Canon)
- Add missing __init__.py where package imports are intended.
- Add components/__init__.py with canonical exports.
- Delete legacy variants and duplicate implementations.

Phase 3 (Catalog and Docs)
- Make catalog-index.json the single source of truth.
- Regenerate README and INVENTORY from catalog-index.json.
- Update scripts to use current catalog files.

Phase 4 (Dependencies and Tests)
- Align Python extras with imports; add missing deps.
- Add tsconfig.json and peer dependency list for TS/React components.
- Add minimal tests for missing components.

-----------------------------------------------------------------------
GAP ANALYSIS (Target vs Current)
-----------------------------------------------------------------------

Target: Copy-paste components require no machine-specific paths.
Current: Hard-coded absolute paths in scripts and READMEs.
Gap: Portability broken.
Action: Replace with relative paths and a single config file.

Target: One canonical shared-types contract.
Current: Severity and Money are duplicated in multiple components.
Gap: Interop broken.
Action: Remove fallbacks and bundle common/types.py with each component.

Target: One canonical tagging protocol with optional memory adapter.
Current: Two divergent tagging protocols ship.
Gap: Metadata inconsistency.
Action: Merge into canonical, add adapter for memory MCP.

Target: Importable Python components with standard naming.
Current: Hyphenated dirs and missing __init__.py.
Gap: Imports unreliable.
Action: Rename dirs and add __init__.py.

Target: Accurate catalog and discovery.
Current: README vs catalog mismatch; catalog.json missing.
Gap: User confusion and broken scripts.
Action: Regenerate README/INVENTORY from catalog-index.json and update scripts.

Target: Minimal deps documented and installable.
Current: Python extras and TS deps incomplete.
Gap: Runtime failures on copy-paste.
Action: Align extras and add TS peer deps plus tsconfig.

Target: Clean repo suitable for copying.
Current: node_modules, __pycache__, .pyc, .pytest_cache, .benchmarks present.
Gap: Bloat and noise.
Action: Cleanup and ignore artifacts.

-----------------------------------------------------------------------
SUGGESTIONS (Concrete and Copy-Paste Oriented)
-----------------------------------------------------------------------

Short-term (Quick Wins)
- Delete components/nul and all build artifacts.
- Rename hyphenated Python component dirs.
- Remove legacy React hook files and legacy exports.
- Remove Memory MCP tagging fork; replace with adapter.

Medium-term (Structure and Stability)
- Add __init__.py to intended Python packages.
- Add components/__init__.py to expose canonical exports.
- Update all READMEs to use relative paths and copy instructions.
- Replace absolute path usage in scripts with a shared config.

Long-term (Maintainability)
- Build a single "component registry" generator that:
  - Validates README existence
  - Validates tests presence
  - Checks imports against common/types.py
  - Emits catalog-index.json and README table

-----------------------------------------------------------------------
NOTES
-----------------------------------------------------------------------

- This audit assumes copy-paste use. If you later decide to package this, the same blockers apply but will be more severe.
- Memory MCP should remain optional. Treat it as an adapter layer on top of the canonical tagging protocol.
- Legacy paths should be deleted per user direction. This will reduce token footprint and avoid drift.

