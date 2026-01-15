"""
Image Generator Base Pattern - Pluggable Image Generation

Provides abstract base class and registry for modular image generation
supporting multiple providers (local models, APIs, etc.).

Source: Extracted from context-cascade/scripts/multi-model/image-gen/base.py
"""

from .generator_base import (
    ImageProvider,
    ImageConfig,
    GeneratedImage,
    ImageGeneratorBase,
    ProviderRegistry,
)

__all__ = [
    "ImageProvider",
    "ImageConfig",
    "GeneratedImage",
    "ImageGeneratorBase",
    "ProviderRegistry",
]
