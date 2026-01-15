"""
Mode library for cognitive architecture.

Defines named configuration modes with their settings,
use cases, and expected performance characteristics.
"""

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import (
    FullConfig,
    FrameworkConfig,
    PromptConfig,
    VerixStrictness,
    CompressionLevel,
    VectorCodec,
)


class ModeType(Enum):
    """Types of configuration modes."""
    STRICT = "strict"
    BALANCED = "balanced"
    EFFICIENT = "efficient"
    ROBUST = "robust"
    MINIMAL = "minimal"
    CUSTOM = "custom"


@dataclass
class Mode:
    """A named configuration mode."""

    name: str
    mode_type: ModeType
    description: str
    config: FullConfig
    use_cases: List[str] = field(default_factory=list)
    expected_metrics: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    @property
    def vector(self) -> List[float]:
        """Get config vector."""
        return VectorCodec.encode(self.config)

    @property
    def cluster_key(self) -> str:
        """Get cluster key for caching."""
        return VectorCodec.cluster_key(self.config)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.mode_type.value,
            "description": self.description,
            "use_cases": self.use_cases,
            "expected_metrics": self.expected_metrics,
            "tags": self.tags,
            "config": {
                "framework": {
                    "evidential": self.config.framework.evidential,
                    "aspectual": self.config.framework.aspectual,
                    "morphological": self.config.framework.morphological,
                    "compositional": self.config.framework.compositional,
                    "honorific": self.config.framework.honorific,
                    "classifier": self.config.framework.classifier,
                    "spatial": self.config.framework.spatial,
                },
                "prompt": {
                    "verix_strictness": self.config.prompt.verix_strictness.value,
                    "compression_level": self.config.prompt.compression_level.value,
                    "require_ground": self.config.prompt.require_ground,
                    "require_confidence": self.config.prompt.require_confidence,
                },
            },
        }


# Built-in modes

def _create_strict_mode() -> Mode:
    """Create strict mode with maximum epistemic rigor."""
    config = FullConfig(
        framework=FrameworkConfig(
            evidential=True,
            aspectual=True,
            morphological=True,
            compositional=True,
            honorific=True,
            classifier=True,
            spatial=True,
        ),
        prompt=PromptConfig(
            verix_strictness=VerixStrictness.STRICT,
            compression_level=CompressionLevel.L1_AI_HUMAN,
            require_ground=True,
            require_confidence=True,
        ),
    )
    return Mode(
        name="strict",
        mode_type=ModeType.STRICT,
        description="Maximum epistemic consistency with all frames and strict VERIX",
        config=config,
        use_cases=[
            "Academic research requiring rigorous sourcing",
            "Legal document analysis",
            "Medical diagnosis support",
            "Financial compliance reporting",
            "Scientific paper review",
        ],
        expected_metrics={
            "task_accuracy": 0.85,
            "token_efficiency": 0.6,
            "edge_robustness": 0.8,
            "epistemic_consistency": 0.95,
        },
        tags=["rigorous", "academic", "compliance", "high-stakes"],
    )


def _create_balanced_mode() -> Mode:
    """Create balanced mode with good tradeoffs."""
    config = FullConfig(
        framework=FrameworkConfig(
            evidential=True,
            aspectual=True,
            morphological=False,
            compositional=False,
            honorific=False,
            classifier=False,
            spatial=False,
        ),
        prompt=PromptConfig(
            verix_strictness=VerixStrictness.MODERATE,
            compression_level=CompressionLevel.L1_AI_HUMAN,
            require_ground=True,
            require_confidence=True,
        ),
    )
    return Mode(
        name="balanced",
        mode_type=ModeType.BALANCED,
        description="Good tradeoff across all objectives for general use",
        config=config,
        use_cases=[
            "General-purpose assistant tasks",
            "Code review and analysis",
            "Technical documentation",
            "Customer support automation",
            "Content generation",
        ],
        expected_metrics={
            "task_accuracy": 0.82,
            "token_efficiency": 0.75,
            "edge_robustness": 0.72,
            "epistemic_consistency": 0.8,
        },
        tags=["general", "default", "versatile"],
    )


def _create_efficient_mode() -> Mode:
    """Create efficient mode optimized for token usage."""
    config = FullConfig(
        framework=FrameworkConfig(
            evidential=True,
            aspectual=False,
            morphological=False,
            compositional=False,
            honorific=False,
            classifier=False,
            spatial=False,
        ),
        prompt=PromptConfig(
            verix_strictness=VerixStrictness.RELAXED,
            compression_level=CompressionLevel.L0_AI_AI,
            require_ground=False,
            require_confidence=True,
        ),
    )
    return Mode(
        name="efficient",
        mode_type=ModeType.EFFICIENT,
        description="Optimized for minimal token usage with L0 compression",
        config=config,
        use_cases=[
            "High-volume API endpoints",
            "Real-time chat applications",
            "Cost-sensitive deployments",
            "Quick summaries and translations",
            "Batch processing",
        ],
        expected_metrics={
            "task_accuracy": 0.75,
            "token_efficiency": 0.92,
            "edge_robustness": 0.65,
            "epistemic_consistency": 0.7,
        },
        tags=["fast", "cheap", "high-volume", "api"],
    )


def _create_robust_mode() -> Mode:
    """Create robust mode for edge case handling."""
    config = FullConfig(
        framework=FrameworkConfig(
            evidential=True,
            aspectual=True,
            morphological=False,
            compositional=True,
            honorific=False,
            classifier=True,
            spatial=False,
        ),
        prompt=PromptConfig(
            verix_strictness=VerixStrictness.MODERATE,
            compression_level=CompressionLevel.L1_AI_HUMAN,
            require_ground=True,
            require_confidence=True,
        ),
    )
    return Mode(
        name="robust",
        mode_type=ModeType.ROBUST,
        description="Optimized for handling edge cases and adversarial inputs",
        config=config,
        use_cases=[
            "User-facing applications with unpredictable input",
            "Security-sensitive contexts",
            "Multi-language support",
            "Error-prone data sources",
            "Adversarial testing",
        ],
        expected_metrics={
            "task_accuracy": 0.8,
            "token_efficiency": 0.7,
            "edge_robustness": 0.9,
            "epistemic_consistency": 0.85,
        },
        tags=["secure", "defensive", "adversarial", "safe"],
    )


def _create_minimal_mode() -> Mode:
    """Create minimal mode with fewest frames."""
    config = FullConfig(
        framework=FrameworkConfig(
            evidential=False,
            aspectual=False,
            morphological=False,
            compositional=False,
            honorific=False,
            classifier=False,
            spatial=False,
        ),
        prompt=PromptConfig(
            verix_strictness=VerixStrictness.RELAXED,
            compression_level=CompressionLevel.L2_HUMAN,
            require_ground=False,
            require_confidence=False,
        ),
    )
    return Mode(
        name="minimal",
        mode_type=ModeType.MINIMAL,
        description="Lightweight mode with no cognitive frames for simple tasks",
        config=config,
        use_cases=[
            "Simple Q&A tasks",
            "Rapid prototyping",
            "Baseline comparison",
            "Legacy system integration",
            "Simple formatting tasks",
        ],
        expected_metrics={
            "task_accuracy": 0.7,
            "token_efficiency": 0.95,
            "edge_robustness": 0.6,
            "epistemic_consistency": 0.5,
        },
        tags=["simple", "lightweight", "baseline", "prototype"],
    )


# Built-in modes registry
BUILTIN_MODES: Dict[str, Mode] = {
    "strict": _create_strict_mode(),
    "balanced": _create_balanced_mode(),
    "efficient": _create_efficient_mode(),
    "robust": _create_robust_mode(),
    "minimal": _create_minimal_mode(),
}


class ModeLibrary:
    """Library of configuration modes."""

    def __init__(self, include_builtins: bool = True):
        """
        Initialize mode library.

        Args:
            include_builtins: Include built-in modes
        """
        self._modes: Dict[str, Mode] = {}
        if include_builtins:
            self._modes.update(BUILTIN_MODES)

    def get(self, name: str) -> Optional[Mode]:
        """Get mode by name."""
        return self._modes.get(name)

    def add(self, mode: Mode) -> None:
        """Add or update a mode."""
        self._modes[mode.name] = mode

    def remove(self, name: str) -> bool:
        """Remove a mode. Returns True if found."""
        if name in self._modes:
            del self._modes[name]
            return True
        return False

    def list_names(self) -> List[str]:
        """List all mode names."""
        return list(self._modes.keys())

    def list_by_type(self, mode_type: ModeType) -> List[Mode]:
        """List modes by type."""
        return [m for m in self._modes.values() if m.mode_type == mode_type]

    def list_by_tag(self, tag: str) -> List[Mode]:
        """List modes by tag."""
        return [m for m in self._modes.values() if tag in m.tags]

    def search(self, query: str) -> List[Mode]:
        """Search modes by name, description, or tags."""
        query_lower = query.lower()
        results = []
        for mode in self._modes.values():
            if (
                query_lower in mode.name.lower() or
                query_lower in mode.description.lower() or
                any(query_lower in tag.lower() for tag in mode.tags)
            ):
                results.append(mode)
        return results


# Convenience functions

_default_library = ModeLibrary()


def get_mode(name: str) -> Optional[Mode]:
    """Get mode by name from default library."""
    return _default_library.get(name)


def list_modes() -> List[str]:
    """List all mode names in default library."""
    return _default_library.list_names()


def get_mode_config(name: str) -> Optional[FullConfig]:
    """Get config for a mode by name."""
    mode = _default_library.get(name)
    return mode.config if mode else None
