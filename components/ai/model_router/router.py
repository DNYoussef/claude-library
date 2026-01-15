"""
Model Router - provider selection and routing logic.

Lightweight async router that selects a provider based on strategy and
executes the provider call with optional fallback chaining.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .providers import ProviderRegistry, Provider, ProviderConfig


class RoutingStrategy(Enum):
    """Strategies for choosing a provider."""

    ROUND_ROBIN = "round_robin"
    FALLBACK = "fallback"
    TASK_BASED = "task_based"


@dataclass
class RouterConfig:
    """Configuration for routing behavior."""

    providers: List[str] = field(default_factory=lambda: ["claude", "gemini", "codex"])
    strategy: RoutingStrategy = RoutingStrategy.TASK_BASED
    fallback_enabled: bool = True
    provider_configs: Dict[str, ProviderConfig] = field(default_factory=dict)


@dataclass
class RoutingResult:
    """Result from a routing attempt."""

    provider_name: str
    response: Optional[str]
    success: bool
    error: Optional[str] = None


class ModelRouter:
    """Routes prompts to model providers based on configuration."""

    def __init__(self, config: Optional[RouterConfig] = None):
        self.config = config or RouterConfig()
        self._rr_index = 0

    def _get_provider(self, name: str) -> Provider:
        provider_config = self.config.provider_configs.get(name)
        return ProviderRegistry.create(name, provider_config)

    def _select_provider(self, task_type: Optional[str] = None) -> str:
        if self.config.strategy == RoutingStrategy.ROUND_ROBIN:
            if not self.config.providers:
                raise ValueError("No providers configured for round-robin routing")
            provider = self.config.providers[self._rr_index % len(self.config.providers)]
            self._rr_index += 1
            return provider

        if self.config.strategy == RoutingStrategy.TASK_BASED and task_type:
            best = ProviderRegistry.get_best_for_task(task_type, exclude=[])
            if best:
                return best

        # Default to first provider for fallback or unknown strategy.
        if not self.config.providers:
            raise ValueError("No providers configured for routing")
        return self.config.providers[0]

    async def route(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> RoutingResult:
        """
        Route a prompt to a provider.

        Falls back across configured providers when enabled.
        """
        providers = list(self.config.providers)
        if not providers:
            return RoutingResult(provider_name="", response=None, success=False, error="No providers configured")

        primary = self._select_provider(task_type=task_type)
        if primary in providers:
            providers.remove(primary)
            providers.insert(0, primary)

        last_error = None
        for name in providers:
            provider = self._get_provider(name)
            try:
                if hasattr(provider, "is_available"):
                    available = await provider.is_available()
                    if not available:
                        last_error = f"Provider {name} is unavailable"
                        if self.config.fallback_enabled:
                            continue
                        return RoutingResult(
                            provider_name=primary,
                            response=None,
                            success=False,
                            error=last_error,
                        )

                response = await provider.generate(prompt, system=system, task_type=task_type, **kwargs)
                return RoutingResult(provider_name=name, response=response, success=True)
            except Exception as exc:  # pragma: no cover - provider errors vary
                last_error = str(exc)
                if not self.config.fallback_enabled:
                    break

        return RoutingResult(provider_name=primary, response=None, success=False, error=last_error)
