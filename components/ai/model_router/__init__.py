"""
Model Router Component

A multi-model AI router with fallback, load balancing, and task-based routing.
Supports Claude, Gemini, Codex, and custom providers.

Features:
- Fallback chains for reliability
- Load balancing across providers
- Task-based routing (analysis, code, search, etc.)
- Async execution with timeouts
- Provider health tracking

Usage:
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

LEGO Principle: Import types from library.common.types
"""

from .router import (
    ModelRouter,
    RouterConfig,
    RoutingResult,
    RoutingStrategy,
)
from .providers import (
    Provider,
    ProviderConfig,
    ProviderStatus,
    BaseProvider,
    ClaudeProvider,
    GeminiProvider,
    CodexProvider,
    ProviderRegistry,
)

__all__ = [
    # Router
    "ModelRouter",
    "RouterConfig",
    "RoutingResult",
    "RoutingStrategy",
    # Providers
    "Provider",
    "ProviderConfig",
    "ProviderStatus",
    "BaseProvider",
    "ClaudeProvider",
    "GeminiProvider",
    "CodexProvider",
    "ProviderRegistry",
]
