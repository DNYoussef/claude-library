# Phase 0B Library Extraction Sprint Plan

**Generated**: 2026-01-10
**Strategy**: Extract with integrated Codex audit cycles
**Target**: 30 -> 58 components (+28 new)

---

## Executive Summary

This plan extracts 28 components from 5 projects in 5 groups, with a Codex audit after each group to ensure code quality before proceeding.

| Group | Source | Components | Audit After | Est. Time |
|-------|--------|------------|-------------|-----------|
| 1 | Trader AI | 4 | Yes | 2.5h |
| 2 | Life-OS Dashboard | 8 | Yes | 4h |
| 3 | Life-OS Frontend | 5 | Yes | 2h |
| 4 | Context Cascade | 5 | Yes | 3h |
| 5 | Connascence + Slop | 6 | Yes | 3h |
| **TOTAL** | | **28** | **5 audits** | **14.5h** |

---

## GROUP 1: TRADER AI EXTRACTIONS

**Source**: `D:\Projects\trader-ai`
**Components**: 4
**Focus**: Trading safety and position sizing

### Components to Extract

| Component | Target Path | Description |
|-----------|-------------|-------------|
| circuit-breaker-trading | `components/trading/circuit-breakers/` | 6-type circuit breaker (-2% daily, 10% drawdown) |
| gate-system-manager | `components/trading/gate-system/` | G0-G12 capital tier management |
| kelly-criterion-calculator | `components/trading/position-sizing/` | Kelly criterion position sizing |
| backtest-harness | `components/testing/backtest-harness/` | Backtesting framework |

### Files to Find
```bash
find D:/Projects/trader-ai -name "circuit*.py" -o -name "*gate*.py" -o -name "*kelly*.py"
grep -r "circuit_breaker\|CircuitBreaker" D:/Projects/trader-ai --include="*.py" -l
```

### Codex Audit Focus
- Decimal-only money handling (no floats)
- Thread safety for gate transitions
- Circuit breaker threshold logic
- Edge cases (zero balance, negative returns)

---

## GROUP 2: LIFE-OS DASHBOARD EXTRACTIONS

**Source**: `D:\Projects\life-os-dashboard\backend\`
**Components**: 8
**Focus**: API patterns, real-time, AI orchestration

### Components to Extract

| Component | Target Path | Description |
|-----------|-------------|-------------|
| websocket-connection-manager | `components/websocket/connection-manager/` | Redis-backed WS manager |
| ai-dispatcher | `components/ai/dispatcher/` | Multi-provider AI routing |
| consensus-orchestrator | `components/ai/consensus/` | Byzantine consensus validation |
| crud-audit-pattern | `patterns/crud-audit/` | CRUD with audit logging |
| redis-pubsub-handler | `components/websocket/redis-pubsub/` | Redis pub/sub for events |
| cron-task-scheduler | `components/scheduling/cron-tasks/` | Cron-based task scheduling |
| memory-mcp-client | `components/memory/mcp-client/` | Memory MCP integration |
| worktree-service | `components/git/worktree-service/` | Git worktree management |

### Files to Find
```bash
find D:/Projects/life-os-dashboard -path "*/services/*.py" -o -path "*/websocket/*.py"
grep -r "WebSocket\|ConsensusOrchestrator\|AIDispatcher" D:/Projects/life-os-dashboard --include="*.py" -l
```

### Codex Audit Focus
- Async patterns (no blocking calls)
- Redis connection pooling
- JWT handling in WS manager
- Consensus calculation edge cases
- Audit logging completeness

---

## GROUP 3: LIFE-OS FRONTEND EXTRACTIONS

**Source**: `D:\Projects\life-os-frontend\src\`
**Components**: 5
**Focus**: React UI components, state management

### Components to Extract

| Component | Target Path | Description |
|-----------|-------------|-------------|
| kanban-board | `ui/kanban/` | Drag-and-drop Kanban with dnd-kit |
| kanban-card | `ui/kanban/` | Task card component |
| kanban-column | `ui/kanban/` | Column component with sortable |
| zustand-kanban-store | `stores/kanban-store/` | Zustand state management |
| pipeline-designer-canvas | `ui/pipeline-designer/` | ReactFlow workflow builder |

### Files to Find
```bash
find D:/Projects/life-os-frontend -path "*/kanban/*.tsx"
grep -r "useKanban\|PipelineDesigner" D:/Projects/life-os-frontend --include="*.tsx" -l
```

### Codex Audit Focus
- Accessibility (keyboard navigation)
- Drag-drop event handling
- Mobile responsiveness
- Store state mutations

---

## GROUP 4: CONTEXT CASCADE EXTRACTIONS

**Source**: `C:\Users\17175\claude-code-plugins\context-cascade\`
**Components**: 5
**Focus**: Cognitive architecture patterns

### Components to Extract

| Component | Target Path | Description |
|-----------|-------------|-------------|
| skill-template-pattern | `patterns/skill-template/` | Standard skill structure |
| agent-template-pattern | `patterns/agent-template/` | Standard agent structure |
| workflow-executor | `components/orchestration/workflow-executor/` | Async workflow engine |
| parallel-executor | `components/orchestration/parallel-executor/` | Parallel task execution |
| codex-iterative-fixer | `components/ci/codex-iterator/` | Test-fix loop automation |

### Files to Find
```bash
find C:/Users/17175/claude-code-plugins/context-cascade -path "*/resources/scripts/*.py"
grep -r "workflow_executor\|parallel_exec\|codex_iterate" claude-code-plugins/context-cascade -l
```

### Codex Audit Focus
- Subprocess handling security
- Error propagation patterns
- Timeout handling
- Parallel execution limits

---

## GROUP 5: CONNASCENCE + SLOP DETECTOR EXTRACTIONS

**Source**: `D:\Projects\connascence` + `D:\Projects\slop-detector`
**Components**: 6
**Focus**: Analysis and text processing

### Components to Extract

**From Connascence**:
| Component | Target Path | Description |
|-----------|-------------|-------------|
| sarif-formatter | `components/quality/sarif-formatter/` | SARIF report generation |
| ast-cache | `components/caching/ast-cache/` | AST parsing cache |
| detector-base-pattern | `patterns/detector-template/` | Base class for detectors |

**From Slop Detector**:
| Component | Target Path | Description |
|-----------|-------------|-------------|
| lexical-analyzer | `components/text-analysis/lexical-analyzer/` | AI vocabulary detection |
| structural-analyzer | `components/text-analysis/structural-analyzer/` | AI structural detection |
| scoring-engine | `components/text-analysis/scoring/` | Multi-dimensional scoring |

### Files to Find
```bash
find D:/Projects/connascence -path "*/formatters/*.py" -o -path "*/caching/*.py"
find D:/Projects/slop-detector -path "*/analyzers/*.py" -o -name "*scoring*.py"
```

### Codex Audit Focus
- Regex patterns for edge cases
- Unicode handling
- Large text performance
- SARIF schema compliance

---

## CODEX AUDIT TEMPLATE

After each group, run this audit:

```
Skill("codex-audit", "Audit components at:
  [list of component paths]

Check for:
1. BUGS: Logic errors, edge cases, null handling
2. ERRORS: Type mismatches, import issues
3. INCOMPATIBILITY: Cross-platform, dependencies
4. TECHNICAL DEBT: Code smells, duplication
5. ELEGANCE: Simplify, testable, modular

Output: Detailed report with severity levels")
```

### Fix Process
1. Read audit report
2. Prioritize CRITICAL > HIGH > MEDIUM
3. Fix each issue
4. Re-run tests
5. Mark audit complete

---

## FINAL VALIDATION

After all groups complete:

1. **Catalog Update**: Add all 28 components to catalog.json
2. **Import Test**: `python -c "from library.components import *"`
3. **Full Test Suite**: `pytest library/ -v`
4. **No Project Deps**: `grep -r "from trader_ai\|from life_os" library/`
5. **Generate Report**: Summary with metrics

---

## ESTIMATED TIMELINE

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Group 1 + Audit + Fix | 3h | 3h |
| Group 2 + Audit + Fix | 5h | 8h |
| Group 3 + Audit + Fix | 2.5h | 10.5h |
| Group 4 + Audit + Fix | 4h | 14.5h |
| Group 5 + Audit + Fix | 4h | 18.5h |
| Final Validation | 1.5h | 20h |

**Total Estimated Time**: 20 hours (can be parallelized across sessions)

---

## SUCCESS CRITERIA

- [ ] 28 new components extracted
- [ ] 5 Codex audits completed with fixes
- [ ] All components have tests
- [ ] All components have README
- [ ] catalog.json updated (58 total)
- [ ] No project-specific imports
- [ ] Final validation passes

---

<promise>PHASE_0B_EXTRACTION_PLAN_READY_2026_01_10</promise>
