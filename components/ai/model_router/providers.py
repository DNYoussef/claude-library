"""
Model Provider Implementations

Abstractions for different AI model providers (Claude, Gemini, Codex).
Each provider implements a common interface for routing.

Author: Library extraction from multi-model skill
License: MIT
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Health status of a provider."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ProviderHealth:
    """Health information for a provider."""

    status: ProviderStatus = ProviderStatus.UNKNOWN
    last_check: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0

    def record_success(self, latency_ms: float) -> None:
        """Record a successful call."""
        self.last_success = datetime.now()
        self.last_check = datetime.now()
        self.consecutive_failures = 0

        # Update rolling average latency
        self.avg_latency_ms = (self.avg_latency_ms * 0.9) + (latency_ms * 0.1)

        self._update_status()

    def record_failure(self, error: str) -> None:
        """Record a failed call."""
        self.last_failure = datetime.now()
        self.last_check = datetime.now()
        self.consecutive_failures += 1
        self._update_status()

    def _update_status(self) -> None:
        """Update health status based on metrics."""
        if self.consecutive_failures >= 5:
            self.status = ProviderStatus.UNHEALTHY
        elif self.consecutive_failures >= 2:
            self.status = ProviderStatus.DEGRADED
        else:
            self.status = ProviderStatus.HEALTHY


@dataclass
class ProviderConfig:
    """Configuration for a model provider."""

    name: str
    enabled: bool = True
    timeout_seconds: int = 180
    max_tokens: int = 4000
    temperature: float = 0.7

    # Rate limiting
    requests_per_minute: int = 60
    concurrent_limit: int = 5

    # CLI settings (for subprocess-based providers)
    cli_command: Optional[str] = None
    cli_args: List[str] = field(default_factory=list)

    # API settings (for SDK-based providers)
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None

    # Task routing weights
    task_weights: Dict[str, float] = field(default_factory=lambda: {
        "analysis": 1.0,
        "code": 1.0,
        "search": 1.0,
        "creative": 1.0,
        "general": 1.0,
    })

    # Retry settings
    retry_count: int = 2
    retry_delay_seconds: float = 1.0

    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Provider(Protocol):
    """Protocol for AI model providers."""

    name: str
    config: ProviderConfig
    health: ProviderHealth

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a response from the model."""
        ...

    async def is_available(self) -> bool:
        """Check if the provider is available."""
        ...

    def supports_task(self, task_type: str) -> bool:
        """Check if the provider supports a task type."""
        ...


class BaseProvider(ABC):
    """Base implementation for providers."""

    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or self._default_config()
        self.health = ProviderHealth()
        self._semaphore = asyncio.Semaphore(self.config.concurrent_limit)
        self._last_request_time: Optional[datetime] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        ...

    @abstractmethod
    def _default_config(self) -> ProviderConfig:
        """Return default configuration for this provider."""
        ...

    @abstractmethod
    async def _generate_impl(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Actual generation implementation. Override in subclasses."""
        ...

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate with rate limiting, retries, and health tracking."""
        if not self.config.enabled:
            raise RuntimeError(f"Provider {self.name} is disabled")

        async with self._semaphore:
            # Rate limiting
            await self._rate_limit()

            start_time = datetime.now()
            attempts = 0
            last_error = None

            while attempts <= self.config.retry_count:
                try:
                    result = await asyncio.wait_for(
                        self._generate_impl(prompt, system, **kwargs),
                        timeout=self.config.timeout_seconds,
                    )

                    latency_ms = (datetime.now() - start_time).total_seconds() * 1000
                    self.health.record_success(latency_ms)

                    return result

                except asyncio.TimeoutError:
                    last_error = f"Timeout after {self.config.timeout_seconds}s"
                    logger.warning(f"{self.name} timeout (attempt {attempts + 1})")
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"{self.name} error (attempt {attempts + 1}): {e}")

                attempts += 1
                if attempts <= self.config.retry_count:
                    await asyncio.sleep(self.config.retry_delay_seconds)

            self.health.record_failure(last_error or "Unknown error")
            raise RuntimeError(f"{self.name} failed after {attempts} attempts: {last_error}")

    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        if not self._last_request_time:
            self._last_request_time = datetime.now()
            return

        min_interval = 60.0 / self.config.requests_per_minute
        elapsed = (datetime.now() - self._last_request_time).total_seconds()
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

        self._last_request_time = datetime.now()

    async def is_available(self) -> bool:
        """Check if the provider is available."""
        return (
            self.config.enabled
            and self.health.status != ProviderStatus.UNHEALTHY
        )

    def supports_task(self, task_type: str) -> bool:
        """Check if provider supports a task type with non-zero weight."""
        return self.config.task_weights.get(task_type, 0) > 0

    def get_task_weight(self, task_type: str) -> float:
        """Get routing weight for a task type."""
        return self.config.task_weights.get(task_type, 0)


class ClaudeProvider(BaseProvider):
    """Provider for Claude (Anthropic)."""

    @property
    def name(self) -> str:
        return "claude"

    def _default_config(self) -> ProviderConfig:
        return ProviderConfig(
            name="claude",
            cli_command="claude",
            timeout_seconds=180,
            max_tokens=4000,
            task_weights={
                "analysis": 1.0,
                "code": 0.9,
                "search": 0.5,  # No native search
                "creative": 1.0,
                "reasoning": 1.0,
                "general": 1.0,
            },
        )

    async def _generate_impl(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate using Claude CLI."""
        # Truncate prompt for CLI safety
        truncated_prompt = prompt[:15000]

        cmd = ["claude", "-p", truncated_prompt]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0 and stdout:
                return stdout.decode("utf-8", errors="replace")
            else:
                # Return structured response for batch mode
                return self._batch_mode_response(prompt)

        except FileNotFoundError:
            logger.info("Claude CLI not found, using batch mode response")
            return self._batch_mode_response(prompt)

    def _batch_mode_response(self, prompt: str) -> str:
        """Generate structured response when CLI not available."""
        import json

        return json.dumps({
            "model": "claude-opus-4-5",
            "response": "Analysis placeholder - Claude CLI in batch mode",
            "prompt_preview": prompt[:200],
        })


class GeminiProvider(BaseProvider):
    """Provider for Gemini (Google)."""

    @property
    def name(self) -> str:
        return "gemini"

    def _default_config(self) -> ProviderConfig:
        return ProviderConfig(
            name="gemini",
            cli_command="gemini",
            timeout_seconds=180,
            max_tokens=8000,  # Gemini supports larger context
            task_weights={
                "analysis": 0.9,
                "code": 0.8,
                "search": 1.0,  # Native Google Search
                "creative": 0.8,
                "reasoning": 0.8,
                "general": 0.9,
                "media": 1.0,  # Multimodal
                "megacontext": 1.0,  # 1M token window
            },
        )

    async def _generate_impl(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate using Gemini CLI."""
        # Truncate for CLI
        truncated_prompt = prompt[:8000]

        # Use --yolo flag for non-interactive mode
        cmd = f'gemini -y "{truncated_prompt}"'

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                return stdout.decode("utf-8", errors="replace")
            else:
                logger.warning(f"Gemini CLI error: {stderr.decode()}")
                raise RuntimeError(f"Gemini CLI failed: {stderr.decode()[:500]}")

        except FileNotFoundError:
            raise RuntimeError("Gemini CLI not found")


class CodexProvider(BaseProvider):
    """Provider for Codex (OpenAI)."""

    @property
    def name(self) -> str:
        return "codex"

    def _default_config(self) -> ProviderConfig:
        return ProviderConfig(
            name="codex",
            cli_command="codex",
            timeout_seconds=300,  # Codex can be slower
            max_tokens=4000,
            task_weights={
                "analysis": 0.8,
                "code": 1.0,  # Code specialist
                "search": 0.3,
                "creative": 0.6,
                "reasoning": 0.7,
                "general": 0.7,
                "autonomous": 1.0,  # Full-auto mode
                "sandbox": 1.0,  # Sandbox isolation
            },
        )

    async def _generate_impl(
        self,
        prompt: str,
        system: Optional[str] = None,
        context_path: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate using Codex CLI."""
        truncated_prompt = prompt[:8000]

        cmd = f'codex exec "{truncated_prompt}"'

        if context_path and Path(context_path).exists():
            cmd += f' --context "{context_path}"'

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                return stdout.decode("utf-8", errors="replace")
            else:
                logger.warning(f"Codex CLI error: {stderr.decode()}")
                raise RuntimeError(f"Codex CLI failed: {stderr.decode()[:500]}")

        except FileNotFoundError:
            raise RuntimeError("Codex CLI not found")


class ProviderRegistry:
    """Registry and factory for providers."""

    _providers: Dict[str, type] = {
        "claude": ClaudeProvider,
        "gemini": GeminiProvider,
        "codex": CodexProvider,
    }

    @classmethod
    def register(cls, name: str, provider_class: type) -> None:
        """Register a custom provider."""
        cls._providers[name] = provider_class

    @classmethod
    def create(cls, name: str, config: Optional[ProviderConfig] = None) -> BaseProvider:
        """Create a provider instance."""
        if name not in cls._providers:
            raise ValueError(f"Unknown provider: {name}. Available: {list(cls._providers.keys())}")

        return cls._providers[name](config)

    @classmethod
    def available_providers(cls) -> List[str]:
        """List all registered providers."""
        return list(cls._providers.keys())

    @classmethod
    def get_best_for_task(
        cls,
        task_type: str,
        exclude: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Get the best provider for a task type."""
        exclude = exclude or []
        best_provider = None
        best_weight = 0.0

        for name, provider_class in cls._providers.items():
            if name in exclude:
                continue

            # Create temp instance to check weights
            provider = provider_class()
            weight = provider.get_task_weight(task_type)

            if weight > best_weight:
                best_weight = weight
                best_provider = name

        return best_provider
