# Model Router

A multi-model AI router with fallback, load balancing, and task-based routing.
Supports Claude, Gemini, Codex, and custom providers.

## Features

- Fallback chains for reliability
- Load balancing across providers
- Task-based routing (analysis, code, search, etc.)
- Async execution with timeouts
- Provider health tracking

## Exports

### Router

| Export | Description |
|--------|-------------|
| `ModelRouter` | Main router class |
| `RouterConfig` | Configuration for the router |
| `RoutingResult` | Result of a routing operation |
| `RoutingStrategy` | Enum (ROUND_ROBIN, TASK_BASED, etc.) |

### Providers

| Export | Description |
|--------|-------------|
| `Provider` | Provider enum (CLAUDE, GEMINI, CODEX) |
| `ProviderConfig` | Configuration for a provider |
| `ProviderStatus` | Status tracking for providers |
| `BaseProvider` | Abstract base class for providers |
| `ClaudeProvider` | Claude API provider |
| `GeminiProvider` | Gemini API provider |
| `CodexProvider` | Codex CLI provider |
| `ProviderRegistry` | Registry of available providers |

## Usage

```python
from library.components.ai.model_router import (
    ModelRouter,
    RouterConfig,
    Provider,
    RoutingStrategy,
)

config = RouterConfig(
    providers=["claude", "gemini", "codex"],
    strategy=RoutingStrategy.TASK_BASED,
    fallback_enabled=True,
)
router = ModelRouter(config)
result = await router.route("Analyze this code", task_type="analysis")
```

## Task-Based Routing

| Task Type | Preferred Provider |
|-----------|-------------------|
| `analysis` | Claude |
| `code` | Claude, Codex |
| `search` | Gemini |
| `media` | Gemini |
| `autonomous` | Codex |

## Related

- LEGO Principle: Import types from `library.common.types`
