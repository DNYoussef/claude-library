"""
Image Generator Base Pattern

Abstract base class for pluggable image generation supporting
multiple providers: local models (SDXL, SD1.5), APIs (OpenAI, Replicate).

Features:
- Provider registry for dynamic provider selection
- Availability checking (models downloaded, API keys set)
- Batch generation support
- Priority-based provider selection (prefers local over API)

Usage:
    # Implement a provider
    class MyGenerator(ImageGeneratorBase):
        provider = ImageProvider.CUSTOM

        def is_available(self) -> bool:
            return os.path.exists(self.model_path)

        def setup(self) -> bool:
            # Download model if needed
            return True

        def generate(self, prompt, output_path, config=None):
            # Generate image
            return GeneratedImage(
                path=output_path,
                prompt=prompt,
                provider=self.provider,
                config=config or ImageConfig(),
                generation_time_seconds=1.5,
            )

        def generate_batch(self, prompts, output_dir, config=None):
            return [self.generate(p, output_dir / f"{i}.png") for i, p in enumerate(prompts)]

    # Register provider
    ProviderRegistry.register(ImageProvider.CUSTOM, MyGenerator)

    # Use best available
    generator = ProviderRegistry.get_best_available()
    if generator:
        result = generator.generate("A cat", Path("output.png"))

Source: Extracted from context-cascade/scripts/multi-model/image-gen/base.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Type
from enum import Enum


class ImageProvider(Enum):
    """Supported image generation providers."""
    LOCAL_SDXL = "local_sdxl"      # SDXL Lightning local
    LOCAL_SD15 = "local_sd15"      # Stable Diffusion 1.5 local
    OPENAI = "openai"              # DALL-E 3
    REPLICATE = "replicate"        # Replicate API
    STABILITY = "stability"        # Stability AI API
    CUSTOM = "custom"              # User-defined


@dataclass
class ImageConfig:
    """
    Configuration for image generation.

    Attributes:
        width: Image width in pixels (default 1024)
        height: Image height in pixels (default 1024)
        num_inference_steps: Denoising steps (low for Lightning models)
        guidance_scale: CFG scale (0 for Lightning)
        num_images: Number of images to generate
        seed: Random seed for reproducibility
        negative_prompt: What to avoid in the image
    """
    width: int = 1024
    height: int = 1024
    num_inference_steps: int = 4   # Low for SDXL Lightning
    guidance_scale: float = 0.0    # 0 for Lightning
    num_images: int = 1
    seed: Optional[int] = None
    negative_prompt: Optional[str] = None


@dataclass
class GeneratedImage:
    """
    Result of image generation.

    Attributes:
        path: Path to the generated image file
        prompt: The prompt used to generate
        provider: Which provider generated it
        config: Configuration used
        generation_time_seconds: How long it took
    """
    path: Path
    prompt: str
    provider: ImageProvider
    config: ImageConfig
    generation_time_seconds: float


class ImageGeneratorBase(ABC):
    """
    Abstract base class for image generators.

    Implementers must provide:
        - provider: Class attribute identifying the provider
        - is_available(): Check if provider can be used
        - setup(): Initialize the provider (download models, etc.)
        - generate(): Generate a single image
        - generate_batch(): Generate multiple images

    The provider pattern allows:
        - Runtime provider selection
        - Fallback to alternatives
        - Local-first with API backup
    """

    provider: ImageProvider

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this provider is available.

        Returns:
            True if models downloaded, API keys set, etc.
        """
        pass

    @abstractmethod
    def setup(self) -> bool:
        """
        Download models or configure API.

        Returns:
            True if setup successful
        """
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        output_path: Path,
        config: Optional[ImageConfig] = None
    ) -> GeneratedImage:
        """
        Generate an image from prompt.

        Args:
            prompt: Text description of desired image
            output_path: Where to save the image
            config: Optional generation configuration

        Returns:
            GeneratedImage with path and metadata
        """
        pass

    @abstractmethod
    def generate_batch(
        self,
        prompts: List[str],
        output_dir: Path,
        config: Optional[ImageConfig] = None
    ) -> List[GeneratedImage]:
        """
        Generate multiple images.

        Args:
            prompts: List of text prompts
            output_dir: Directory to save images
            config: Optional generation configuration

        Returns:
            List of GeneratedImage results
        """
        pass


class ProviderRegistry:
    """
    Registry of available image generation providers.

    Use this to:
        - Register custom providers
        - List what's available
        - Get the best available provider
    """

    _providers: Dict[ImageProvider, Type[ImageGeneratorBase]] = {}

    @classmethod
    def register(cls, provider_type: ImageProvider, provider_class: Type[ImageGeneratorBase]) -> None:
        """
        Register a provider implementation.

        Args:
            provider_type: The provider enum value
            provider_class: The class implementing ImageGeneratorBase
        """
        cls._providers[provider_type] = provider_class

    @classmethod
    def get(cls, provider_type: ImageProvider) -> Optional[ImageGeneratorBase]:
        """
        Get a provider instance by type.

        Args:
            provider_type: Which provider to get

        Returns:
            Instance of the provider, or None if not registered
        """
        if provider_type not in cls._providers:
            return None
        return cls._providers[provider_type]()

    @classmethod
    def list_available(cls) -> List[ImageProvider]:
        """
        List providers that are currently available.

        Checks is_available() on each registered provider.

        Returns:
            List of available provider types
        """
        available = []
        for provider_type, provider_class in cls._providers.items():
            try:
                instance = provider_class()
                if instance.is_available():
                    available.append(provider_type)
            except Exception:
                pass
        return available

    @classmethod
    def get_best_available(cls) -> Optional[ImageGeneratorBase]:
        """
        Get the best available provider.

        Priority order (prefers local over API):
        1. LOCAL_SDXL
        2. LOCAL_SD15
        3. OPENAI
        4. REPLICATE
        5. STABILITY

        Returns:
            Best available provider instance, or None if none available
        """
        priority = [
            ImageProvider.LOCAL_SDXL,
            ImageProvider.LOCAL_SD15,
            ImageProvider.OPENAI,
            ImageProvider.REPLICATE,
            ImageProvider.STABILITY,
        ]

        for provider_type in priority:
            if provider_type in cls._providers:
                try:
                    instance = cls._providers[provider_type]()
                    if instance.is_available():
                        return instance
                except Exception:
                    pass
        return None

    @classmethod
    def clear(cls) -> None:
        """Clear all registered providers (for testing)."""
        cls._providers.clear()
