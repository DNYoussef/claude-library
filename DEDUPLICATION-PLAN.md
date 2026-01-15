# Cross-Project Deduplication Plan

**Date**: 2026-01-10
**Phase**: 7 (Cross-project deduplication)

---

## Summary

| Project | Duplicate File | Library Component | LOC Savings | Priority |
|---------|----------------|-------------------|-------------|----------|
| life-os-dashboard | memory_mcp_circuit_breaker.py | trading/circuit-breakers | 196 | HIGH |
| life-os-dashboard | tagging_protocol.py | observability/tagging-protocol | 231 | HIGH |
| life-os-frontend | api.ts | http/fetch-api-client | 205 | MEDIUM |
| **Internal Library** | memory/tagging_protocol.py | observability/tagging-protocol | 200 | HIGH |

**Total Potential LOC Reduction**: ~832 lines

---

## Duplicate #1: Circuit Breaker (HIGH Priority)

### Current State
- **Dashboard**: `D:\Projects\life-os-dashboard\backend\app\utils\memory_mcp_circuit_breaker.py` (196 LOC)
- **Library**: `C:\Users\17175\.claude\library\components\trading\circuit-breakers\circuit_breaker.py`

### Comparison

| Feature | Dashboard Version | Library Version |
|---------|-------------------|-----------------|
| States | CLOSED, OPEN, HALF_OPEN | Same |
| Async Support | Yes (asyncio.Lock) | Yes (threading.RLock + asyncio) |
| Metrics | None | Full CircuitBreakerMetrics |
| Callbacks | None | Trip/recovery callbacks |
| Manager | None | CircuitBreakerManager |
| Configuration | Hardcoded | CircuitBreakerConfig dataclass |

### Migration Path
1. Update dashboard to import from library:
   ```python
   # Before
   from app.utils.memory_mcp_circuit_breaker import CircuitBreaker

   # After
   from library.components.trading.circuit_breakers.circuit_breaker import (
       CircuitBreaker,
       CircuitBreakerConfig
   )
   ```
2. Create thin adapter if needed for async-only usage
3. Delete `memory_mcp_circuit_breaker.py`

### Files to Update
- `D:\Projects\life-os-dashboard\backend\app\utils\memory_mcp.py`
- `D:\Projects\life-os-dashboard\backend\app\utils\memory_mcp_client.py`

---

## Duplicate #2: Tagging Protocol (HIGH Priority)

### Current State
- **Dashboard**: `D:\Projects\life-os-dashboard\backend\app\utils\tagging_protocol.py` (231 LOC)
- **Library**: `C:\Users\17175\.claude\library\components\observability\tagging-protocol\tagging_protocol.py` (696 LOC)
- **Also**: `C:\Users\17175\.claude\library\components\memory\memory-mcp-client\tagging_protocol.py` (200 LOC) - INTERNAL DUPLICATE

### Comparison

| Feature | Dashboard Version | Library Version |
|---------|-------------------|-----------------|
| Intent Enum | 8 values | 8 values + more |
| AgentCategory | 10 values | 15+ values |
| WHO/WHEN/PROJECT/WHY | Basic | Full with nested structure |
| Flat Tags | No | Yes (for logging systems) |
| Factory Functions | No | create_simple_tagger() |

### Migration Path
1. Update dashboard to import from library:
   ```python
   # Before
   from app.utils.tagging_protocol import TaggingProtocol, Intent, AgentCategory

   # After
   from library.components.observability.tagging_protocol.tagging_protocol import (
       TaggingProtocol,
       Intent,
       AgentCategory,
       create_simple_tagger
   )
   ```
2. Delete `D:\Projects\life-os-dashboard\backend\app\utils\tagging_protocol.py`
3. ALSO: Delete internal library duplicate at `memory/memory-mcp-client/tagging_protocol.py`

### Files to Update
- `D:\Projects\life-os-dashboard\backend\app\utils\memory_mcp.py`
- `D:\Projects\life-os-dashboard\backend\app\utils\memory_mcp_client.py`

---

## Duplicate #3: Fetch API Client (MEDIUM Priority)

### Current State
- **Frontend**: `D:\Projects\life-os-frontend\src\services\api.ts` (205 LOC)
- **Library**: `C:\Users\17175\.claude\library\components\http\fetch-api-client\fetch_api_client.ts` (554 LOC)

### Comparison

| Feature | Frontend Version | Library Version |
|---------|------------------|-----------------|
| Retry Logic | None | Exponential backoff + jitter |
| Timeout | None | Configurable with AbortController |
| Interceptors | None | Request/Response/Error interceptors |
| Error Class | Basic | FetchApiError with metadata |
| Singleton | None | DefaultClientManager |

### Migration Path

The library version is significantly more robust. However, the frontend uses specific domain APIs (tasks, agents, projects).

**Recommended Approach**: Keep api.ts but refactor to use library client internally.

```typescript
// Before (in api.ts)
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  // ... inline implementation
}

// After (in api.ts)
import { createFetchClient } from '../lib/fetch_api_client';

const client = createFetchClient({
  baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8001',
  timeout: 30000,
  retry: { maxRetries: 2, baseDelay: 500 }
});

// Domain-specific APIs remain the same but use client internally
export async function getTasks(page = 1, pageSize = 20): Promise<PaginatedResponse<Task>> {
  return client.get(`/api/v1/tasks?page=${page}&page_size=${pageSize}`);
}
```

### Files to Update
- `D:\Projects\life-os-frontend\src\services\api.ts`
- Copy library client to frontend: `src\lib\fetch_api_client.ts`

---

## Internal Library Bundling (BY DESIGN - No Action Needed)

### Observation
The library has bundled copies in some components:
- `components/memory/memory-mcp-client/tagging_protocol.py` (bundled with client)
- `components/memory/memory-mcp-client/circuit_breaker.py` (bundled with client)

### Why This Is Correct
Each LEGO component is designed to be **self-contained** and **copy-ready**:
- No external dependencies within the library
- Each component can be extracted and used independently
- Bundled copies are clearly documented as local copies

**This is intentional for LEGO compatibility - NOT duplication to fix.**

The canonical standalone versions exist for projects that want:
- Just the tagging protocol: `observability/tagging-protocol/`
- Just the circuit breaker: `trading/circuit-breakers/`

The bundled versions exist for projects that want the complete client with all dependencies.

---

## Execution Order

### Phase 7.1: Dashboard Deduplication
1. [ ] Update dashboard to use library circuit_breaker
2. [ ] Update dashboard to use library tagging_protocol
3. [ ] Delete `memory_mcp_circuit_breaker.py`
4. [ ] Delete dashboard `tagging_protocol.py`
5. [ ] Run dashboard tests

### Phase 7.2: Frontend Deduplication
1. [ ] Copy fetch_api_client.ts to frontend lib
2. [ ] Refactor api.ts to use library client
3. [ ] Run frontend tests

---

## Estimated Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Total LOC (duplicated) | 832 | 0 | -100% |
| Maintenance points | 5 | 1 | -80% |
| Bug fix propagation | Manual | Automatic | N/A |

---

## Notes

- Dashboard and library both need Python path setup to import from library
- Frontend needs TypeScript path alias configured: `@lib/*` -> `src/lib/*`
- All migrations should preserve existing test coverage
