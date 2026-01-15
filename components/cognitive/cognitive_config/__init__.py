"""
Cognitive Configuration Manager - Standalone Component

Provides configuration dataclasses for cognitive architecture including
VERILINGUA frames, VERIX epistemic notation, and multi-objective optimization
via 14-dimensional vector encoding.

Example usage:
    from cognitive_config import (
        FullConfig,
        FrameworkConfig,
        PromptConfig,
        VerixStrictness,
        CompressionLevel,
        VectorCodec,
        get_named_mode,
        DEFAULT_CONFIG,
        STRICT_CONFIG,
        MINIMAL_CONFIG,
    )

    # Create default config
    config = FullConfig()
    print(config.summary())

    # Use named mode
    audit_config = get_named_mode("audit")

    # Encode for optimization
    vector = VectorCodec.encode(config)

    # Decode from vector
    restored = VectorCodec.decode(vector)

    # Get cache key for DSPy
    key = VectorCodec.cluster_key(config)
"""

from .cognitive_config import (
    # Enums
    VerixStrictness,
    CompressionLevel,

    # Constants
    DEFAULT_FRAME_WEIGHTS,
    DEFAULT_EVIDENTIAL_MINIMUM,

    # Dataclasses
    FrameworkConfig,
    PromptConfig,
    FullConfig,

    # Codec class
    VectorCodec,

    # Preset configurations
    DEFAULT_CONFIG,
    MINIMAL_CONFIG,
    STRICT_CONFIG,

    # Named mode functions
    create_audit_config,
    create_speed_config,
    create_research_config,
    create_robust_config,
    create_balanced_config,
    NAMED_MODES,
    get_named_mode,
)

__all__ = [
    # Enums
    "VerixStrictness",
    "CompressionLevel",

    # Constants
    "DEFAULT_FRAME_WEIGHTS",
    "DEFAULT_EVIDENTIAL_MINIMUM",

    # Dataclasses
    "FrameworkConfig",
    "PromptConfig",
    "FullConfig",

    # Codec class
    "VectorCodec",

    # Preset configurations
    "DEFAULT_CONFIG",
    "MINIMAL_CONFIG",
    "STRICT_CONFIG",

    # Named mode functions
    "create_audit_config",
    "create_speed_config",
    "create_research_config",
    "create_robust_config",
    "create_balanced_config",
    "NAMED_MODES",
    "get_named_mode",
]

__version__ = "1.0.0"
__author__ = "Extracted from Context Cascade"
