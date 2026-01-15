"""
Cognitive Configuration Manager - Standalone Component

Extracted from Context Cascade cognitive-architecture/core/config.py
Provides configuration dataclasses for cognitive architecture.

Classes:
- FrameworkConfig: Frame toggles (evidential, aspectual, etc.)
- PromptConfig: VERIX settings (strictness, compression_level)
- FullConfig: Combined config
- VectorCodec: Stable config <-> vector mapping (14 dimensions)

Enums:
- VerixStrictness: VERIX compliance strictness levels
- CompressionLevel: VERIX output compression levels

Constants:
- DEFAULT_FRAME_WEIGHTS: Default weights for all 7 cognitive frames
- DEFAULT_EVIDENTIAL_MINIMUM: Minimum weight for evidential frame
- DEFAULT_CONFIG: Default full configuration
- MINIMAL_CONFIG: Minimal configuration (evidential only)
- STRICT_CONFIG: Strict configuration (all frames enabled)

This module is STANDALONE - zero external dependencies (stdlib only).
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict
from types import MappingProxyType
from enum import Enum


class VerixStrictness(Enum):
    """
    VERIX compliance strictness levels.

    VERIX is an epistemic notation system that makes claim properties explicit.

    Levels:
        RELAXED (0): Only illocution required
        MODERATE (1): Illocution + confidence required
        STRICT (2): All fields required (illocution, affect, ground, confidence, state)
    """
    RELAXED = 0    # Only illocution required
    MODERATE = 1   # Illocution + confidence required
    STRICT = 2     # All fields required


class CompressionLevel(Enum):
    """
    VERIX output compression levels.

    Controls how VERIX notation is rendered in output.

    Levels:
        L0_AI_AI (0): Emoji shorthand for machine-to-machine communication
        L1_AI_HUMAN (1): Annotated format for human inspection
        L2_HUMAN (2): Natural language for end users (lossy, no markers)
    """
    L0_AI_AI = 0      # Emoji shorthand (machine-to-machine)
    L1_AI_HUMAN = 1   # Annotated format (human inspector)
    L2_HUMAN = 2      # Natural language (end user, lossy)


# Default frame weights (matches FRAME_WEIGHTS in VERILINGUA spec)
# Higher weight = frame instruction appears earlier and is emphasized more
# All values MUST be in range [0.0, 1.0]
_DEFAULT_FRAME_WEIGHTS_MUTABLE: Dict[str, float] = {
    "evidential": 0.95,      # Turkish -mis/-di: "How do you know?"
    "aspectual": 0.80,       # Russian aspect: "Complete or ongoing?"
    "morphological": 0.65,   # Arabic trilateral roots: semantic decomposition
    "compositional": 0.60,   # German compounding: primitives to compounds
    "honorific": 0.35,       # Japanese keigo: audience calibration
    "classifier": 0.45,      # Chinese measure words: object comparison
    "spatial": 0.40,         # Guugu Yimithirr: absolute positioning
}

# L2: Validate all default weights are in valid range [0.0, 1.0]
for _frame_name, _weight in _DEFAULT_FRAME_WEIGHTS_MUTABLE.items():
    assert 0.0 <= _weight <= 1.0, (
        f"Invalid default weight for '{_frame_name}': {_weight}. "
        f"All weights must be in range [0.0, 1.0]."
    )

# Expose as immutable mapping to prevent accidental modification
DEFAULT_FRAME_WEIGHTS: MappingProxyType = MappingProxyType(_DEFAULT_FRAME_WEIGHTS_MUTABLE)

# Minimum weight for evidential frame (evidence is foundational)
DEFAULT_EVIDENTIAL_MINIMUM: float = 0.30


# M2 FIX: Extract frame complexity order to module-level constant
# Used for Hofstadter recursion validation - frames should simplify as nesting increases
# Ordered from most complex to least complex
FRAME_COMPLEXITY_ORDER: Tuple[str, ...] = (
    "compositional",   # Most complex: compound building
    "morphological",   # Complex: semantic decomposition
    "aspectual",       # Moderate: temporal aspect
    "honorific",       # Moderate: audience calibration
    "classifier",      # Simple: type/count classification
    "spatial",         # Simple: absolute positioning
    "evidential",      # Simplest: evidence source (foundational)
)


@dataclass
class FrameworkConfig:
    """
    Configuration for which cognitive frames are active.

    Each frame adds specific cognitive constraints from natural language:
    - evidential: Turkish -mis/-di (how do you know?)
    - aspectual: Russian pfv/ipfv (complete or ongoing?)
    - morphological: Arabic trilateral roots (semantic decomposition)
    - compositional: German compounding (primitives to compounds)
    - honorific: Japanese keigo (audience calibration)
    - classifier: Chinese measure words (object comparison)
    - spatial: Guugu Yimithirr absolute positioning (navigation)

    Frame Weight Policy:
    - Each frame has a numeric weight (0.0 - 1.0) for prioritization
    - Higher weight = frame instruction appears earlier and is emphasized more
    - Evidential frame has a minimum weight floor (cannot be de-prioritized)

    Hofstadter Recursion Control:
    - max_frame_depth: Prevents infinite nesting (base case at depth 3)
    - frame_step_policy: Each nested level must be "lighter"
    - FRAME_COMPLEXITY_ORDER: Defines complexity ordering for simplification validation
    """
    # Frame activation toggles
    evidential: bool = True
    aspectual: bool = True
    morphological: bool = True   # Enable semantic decomposition (Arabic roots)
    compositional: bool = True   # Enable primitives->compounds (German compounding)
    honorific: bool = False
    classifier: bool = False
    spatial: bool = False

    # Frame weight overrides (optional)
    # If not set, uses DEFAULT_FRAME_WEIGHTS
    # H1 FIX: Use dict() to create mutable copy from immutable MappingProxyType
    frame_weights: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_FRAME_WEIGHTS))

    # Evidential minimum weight (evidence is foundational)
    evidential_minimum: float = DEFAULT_EVIDENTIAL_MINIMUM

    # Hofstadter recursion control
    max_frame_depth: int = 3  # Base case: stop at depth 3
    frame_step_policy: str = "simpler"  # Each nested level must be "lighter"

    def active_frames(self) -> List[str]:
        """Return list of active frame names."""
        frames = []
        if self.evidential:
            frames.append("evidential")
        if self.aspectual:
            frames.append("aspectual")
        if self.morphological:
            frames.append("morphological")
        if self.compositional:
            frames.append("compositional")
        if self.honorific:
            frames.append("honorific")
        if self.classifier:
            frames.append("classifier")
        if self.spatial:
            frames.append("spatial")
        return frames

    def frame_count(self) -> int:
        """Return number of active frames."""
        return len(self.active_frames())

    def get_weighted_frames(self) -> List[Tuple[str, float]]:
        """
        Get active frames with their weights, sorted by weight descending.

        Returns:
            List of (frame_name, weight) tuples, highest weight first
        """
        active = self.active_frames()
        weighted = [(f, self.frame_weights.get(f, 0.5)) for f in active]
        return sorted(weighted, key=lambda x: x[1], reverse=True)

    def validate_weights(self) -> List[str]:
        """
        Validate the frame weight configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check evidential minimum
        evidential_weight = self.frame_weights.get("evidential", 0.95)
        if self.evidential and evidential_weight < self.evidential_minimum:
            errors.append(
                f"Evidential weight ({evidential_weight}) is below minimum ({self.evidential_minimum})"
            )

        # Check all weights are in valid range
        for frame_name, weight in self.frame_weights.items():
            if weight < 0.0 or weight > 1.0:
                errors.append(f"Weight for '{frame_name}' ({weight}) outside valid range [0.0, 1.0]")

        return errors

    def set_frame_weight(self, frame_name: str, weight: float) -> None:
        """
        Set the weight for a specific frame.

        Args:
            frame_name: Name of the frame
            weight: Weight value (0.0 - 1.0)

        Raises:
            ValueError: If weight is out of range or violates evidential minimum
        """
        if weight < 0.0 or weight > 1.0:
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {weight}")

        if frame_name == "evidential" and weight < self.evidential_minimum:
            raise ValueError(
                f"Cannot set evidential weight ({weight}) below minimum ({self.evidential_minimum}). "
                "Evidence is foundational and cannot be de-prioritized."
            )

        self.frame_weights[frame_name] = weight

    def validate_nesting(self, frame_stack: List[str]) -> bool:
        """
        Ensure frame nesting follows Hofstadter recursion rules.

        Returns True if nesting is valid (within depth limit and follows
        simplification policy).

        Args:
            frame_stack: List of frame names representing the nesting order

        Note:
            Uses module-level FRAME_COMPLEXITY_ORDER constant for complexity ordering.
        """
        if len(frame_stack) > self.max_frame_depth:
            return False  # Hit base case limit

        if self.frame_step_policy == "simpler":
            # M2 FIX: Use module-level constant instead of hardcoded list
            # Each nested frame should be "lighter" (lower complexity)
            for i in range(1, len(frame_stack)):
                if frame_stack[i] not in FRAME_COMPLEXITY_ORDER or frame_stack[i-1] not in FRAME_COMPLEXITY_ORDER:
                    continue
                prev_complexity = FRAME_COMPLEXITY_ORDER.index(frame_stack[i-1])
                curr_complexity = FRAME_COMPLEXITY_ORDER.index(frame_stack[i])
                if curr_complexity <= prev_complexity:
                    return False  # Not simplifying

        return True


@dataclass
class PromptConfig:
    """
    Configuration for VERIX epistemic notation requirements.

    Controls how strict the VERIX compliance checking is and
    what format the output should use.

    VERIX Grammar:
        CLAIM := [illocution|affect] content [ground:source] [conf:X.XX] [state:status]

    Illocution Types:
        assert - Factual claim
        query - Question
        direct - Instruction
        commit - Promise
        express - Attitude

    Confidence Ceilings by Evidence Type:
        definition: 0.95, policy: 0.90, observation: 0.95
        research: 0.85, report: 0.70, inference: 0.70
    """
    verix_strictness: VerixStrictness = VerixStrictness.MODERATE
    compression_level: CompressionLevel = CompressionLevel.L1_AI_HUMAN
    require_ground: bool = True      # Require source/evidence citations
    require_confidence: bool = True  # Require confidence values

    # Hofstadter recursive claim limits
    max_claim_depth: int = 3  # Maximum nested ground depth
    require_confidence_decrease: bool = True  # Confidence must decrease toward base

    def is_strict(self) -> bool:
        """Check if running in strict mode."""
        return self.verix_strictness == VerixStrictness.STRICT

    def is_relaxed(self) -> bool:
        """Check if running in relaxed mode."""
        return self.verix_strictness == VerixStrictness.RELAXED


@dataclass
class FullConfig:
    """
    Complete configuration combining framework and prompt settings.

    This is the primary config object passed to all components.
    """
    framework: FrameworkConfig = field(default_factory=FrameworkConfig)
    prompt: PromptConfig = field(default_factory=PromptConfig)

    def summary(self) -> str:
        """Return human-readable config summary."""
        frames = ", ".join(self.framework.active_frames()) or "none"
        return (
            f"Frames: [{frames}] | "
            f"VERIX: {self.prompt.verix_strictness.name} | "
            f"Compression: {self.prompt.compression_level.name}"
        )


class VectorCodec:
    """
    Stable mapping between FullConfig and float vectors.

    Vector Format (14 dimensions):
    [0-6]: Frame toggles (evidential, aspectual, morphological,
           compositional, honorific, classifier, spatial)
    [7]: verix_strictness (0, 1, 2)
    [8]: compression_level (0, 1, 2)
    [9]: require_ground (0, 1)
    [10]: require_confidence (0, 1)
    [11-13]: Reserved for expansion

    This codec is STABLE - the mapping NEVER changes once deployed.
    GlobalMOO optimization operates on these vectors.

    Use Cases:
    - Multi-objective optimization (GlobalMOO, PyMOO NSGA-II)
    - Configuration clustering for DSPy caching
    - Similarity search between configurations
    - Configuration interpolation for exploration
    """

    VECTOR_SIZE = 14

    # Frame indices (0-6)
    IDX_EVIDENTIAL = 0
    IDX_ASPECTUAL = 1
    IDX_MORPHOLOGICAL = 2
    IDX_COMPOSITIONAL = 3
    IDX_HONORIFIC = 4
    IDX_CLASSIFIER = 5
    IDX_SPATIAL = 6

    # Prompt config indices (7-10)
    IDX_VERIX_STRICTNESS = 7
    IDX_COMPRESSION_LEVEL = 8
    IDX_REQUIRE_GROUND = 9
    IDX_REQUIRE_CONFIDENCE = 10

    # Reserved indices (11-13)
    IDX_RESERVED_1 = 11
    IDX_RESERVED_2 = 12
    IDX_RESERVED_3 = 13

    @staticmethod
    def encode(config: FullConfig) -> List[float]:
        """
        Convert FullConfig to 14-dimensional float vector.

        Args:
            config: The configuration to encode

        Returns:
            List of 14 floats representing the configuration
        """
        vector = [0.0] * VectorCodec.VECTOR_SIZE

        # Encode framework config (boolean -> 0.0 or 1.0)
        vector[VectorCodec.IDX_EVIDENTIAL] = 1.0 if config.framework.evidential else 0.0
        vector[VectorCodec.IDX_ASPECTUAL] = 1.0 if config.framework.aspectual else 0.0
        vector[VectorCodec.IDX_MORPHOLOGICAL] = 1.0 if config.framework.morphological else 0.0
        vector[VectorCodec.IDX_COMPOSITIONAL] = 1.0 if config.framework.compositional else 0.0
        vector[VectorCodec.IDX_HONORIFIC] = 1.0 if config.framework.honorific else 0.0
        vector[VectorCodec.IDX_CLASSIFIER] = 1.0 if config.framework.classifier else 0.0
        vector[VectorCodec.IDX_SPATIAL] = 1.0 if config.framework.spatial else 0.0

        # Encode prompt config (enum -> float value)
        vector[VectorCodec.IDX_VERIX_STRICTNESS] = float(config.prompt.verix_strictness.value)
        vector[VectorCodec.IDX_COMPRESSION_LEVEL] = float(config.prompt.compression_level.value)
        vector[VectorCodec.IDX_REQUIRE_GROUND] = 1.0 if config.prompt.require_ground else 0.0
        vector[VectorCodec.IDX_REQUIRE_CONFIDENCE] = 1.0 if config.prompt.require_confidence else 0.0

        # Reserved slots remain 0.0

        return vector

    @staticmethod
    def decode(vector: List[float]) -> FullConfig:
        """
        Convert 14-dimensional float vector to FullConfig.

        Args:
            vector: List of 14 floats

        Returns:
            FullConfig reconstructed from vector

        Raises:
            ValueError: If vector is wrong size or contains invalid values

        Limitations (M1 documented):
            - frame_weights: NOT restored from vector. The decoded FrameworkConfig
              will use DEFAULT_FRAME_WEIGHTS. Custom frame weights are not encoded
              in the 14-dimension vector format because they would require 7
              additional dimensions (one per frame). If you need to preserve
              custom frame weights, serialize the full config object instead.
            - evidential_minimum: NOT restored, uses DEFAULT_EVIDENTIAL_MINIMUM.
            - max_frame_depth: NOT restored, uses default value (3).
            - frame_step_policy: NOT restored, uses default value ("simpler").
            - max_claim_depth: NOT restored, uses default value (3).
            - require_confidence_decrease: NOT restored, uses default value (True).
        """
        if len(vector) != VectorCodec.VECTOR_SIZE:
            raise ValueError(
                f"Vector must have {VectorCodec.VECTOR_SIZE} dimensions, "
                f"got {len(vector)}"
            )

        # Decode framework config (threshold at 0.5 for booleans)
        framework = FrameworkConfig(
            evidential=vector[VectorCodec.IDX_EVIDENTIAL] >= 0.5,
            aspectual=vector[VectorCodec.IDX_ASPECTUAL] >= 0.5,
            morphological=vector[VectorCodec.IDX_MORPHOLOGICAL] >= 0.5,
            compositional=vector[VectorCodec.IDX_COMPOSITIONAL] >= 0.5,
            honorific=vector[VectorCodec.IDX_HONORIFIC] >= 0.5,
            classifier=vector[VectorCodec.IDX_CLASSIFIER] >= 0.5,
            spatial=vector[VectorCodec.IDX_SPATIAL] >= 0.5,
        )

        # Decode prompt config (round to nearest enum value)
        strictness_val = int(round(vector[VectorCodec.IDX_VERIX_STRICTNESS]))
        strictness_val = max(0, min(2, strictness_val))  # Clamp to valid range

        compression_val = int(round(vector[VectorCodec.IDX_COMPRESSION_LEVEL]))
        compression_val = max(0, min(2, compression_val))  # Clamp to valid range

        prompt = PromptConfig(
            verix_strictness=VerixStrictness(strictness_val),
            compression_level=CompressionLevel(compression_val),
            require_ground=vector[VectorCodec.IDX_REQUIRE_GROUND] >= 0.5,
            require_confidence=vector[VectorCodec.IDX_REQUIRE_CONFIDENCE] >= 0.5,
        )

        return FullConfig(framework=framework, prompt=prompt)

    @staticmethod
    def cluster_key(config: FullConfig) -> str:
        """
        Generate cluster key for DSPy Level 2 caching.

        The cluster key identifies a unique configuration "type" that
        should share compiled prompts. Two configs with the same
        cluster key will use the same cached DSPy artifacts.

        Format: "frames:{sorted_frames}|strict:{0-2}|compress:{0-2}"

        Args:
            config: Configuration to generate key for

        Returns:
            String key for cache lookup
        """
        frames = sorted(config.framework.active_frames())
        frames_str = "+".join(frames) if frames else "none"

        return (
            f"frames:{frames_str}|"
            f"strict:{config.prompt.verix_strictness.value}|"
            f"compress:{config.prompt.compression_level.value}"
        )

    @staticmethod
    def distance(v1: List[float], v2: List[float]) -> float:
        """
        Calculate Euclidean distance between two config vectors.

        Useful for finding similar configurations in the Pareto frontier.

        Args:
            v1: First vector
            v2: Second vector

        Returns:
            Euclidean distance
        """
        if len(v1) != len(v2):
            raise ValueError("Vectors must have same length")

        squared_diff_sum = sum((a - b) ** 2 for a, b in zip(v1, v2))
        return squared_diff_sum ** 0.5

    @staticmethod
    def interpolate(v1: List[float], v2: List[float], t: float) -> List[float]:
        """
        Linear interpolation between two config vectors.

        Useful for exploring the configuration space between
        two known good configurations.

        Args:
            v1: Start vector
            v2: End vector
            t: Interpolation factor (0.0 = v1, 1.0 = v2)

        Returns:
            Interpolated vector
        """
        if len(v1) != len(v2):
            raise ValueError("Vectors must have same length")

        t = max(0.0, min(1.0, t))  # Clamp to [0, 1]
        return [a + t * (b - a) for a, b in zip(v1, v2)]


# =============================================================================
# Preset Configurations
# =============================================================================

# Default configuration (moderate strictness, common frames)
DEFAULT_CONFIG = FullConfig()

# Minimal configuration (evidential only, relaxed)
MINIMAL_CONFIG = FullConfig(
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
        compression_level=CompressionLevel.L2_HUMAN,
        require_ground=False,
        require_confidence=False,
    ),
)

# Strict configuration (all frames, maximum strictness)
STRICT_CONFIG = FullConfig(
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
        compression_level=CompressionLevel.L0_AI_AI,
        require_ground=True,
        require_confidence=True,
    ),
)


# =============================================================================
# Named Mode Presets (Pareto-Optimal from MOO)
# =============================================================================

def create_audit_config() -> FullConfig:
    """
    Create audit mode configuration.

    Optimized for code review, compliance checking.
    Accuracy: 0.960, Efficiency: 0.763
    """
    return FullConfig(
        framework=FrameworkConfig(
            evidential=True,
            aspectual=True,
            morphological=True,
            compositional=False,
            honorific=False,
            classifier=False,
            spatial=False,
        ),
        prompt=PromptConfig(
            verix_strictness=VerixStrictness.STRICT,
            compression_level=CompressionLevel.L1_AI_HUMAN,
            require_ground=True,
            require_confidence=True,
        ),
    )


def create_speed_config() -> FullConfig:
    """
    Create speed mode configuration.

    Optimized for quick tasks, prototyping.
    Accuracy: 0.734, Efficiency: 0.950
    """
    return FullConfig(
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
            compression_level=CompressionLevel.L2_HUMAN,
            require_ground=False,
            require_confidence=False,
        ),
    )


def create_research_config() -> FullConfig:
    """
    Create research mode configuration.

    Optimized for content analysis, deep work.
    Accuracy: 0.980, Efficiency: 0.824
    """
    return FullConfig(
        framework=FrameworkConfig(
            evidential=True,
            aspectual=False,
            morphological=False,
            compositional=False,
            honorific=True,
            classifier=True,
            spatial=False,
        ),
        prompt=PromptConfig(
            verix_strictness=VerixStrictness.STRICT,
            compression_level=CompressionLevel.L1_AI_HUMAN,
            require_ground=True,
            require_confidence=True,
        ),
    )


def create_robust_config() -> FullConfig:
    """
    Create robust mode configuration.

    Optimized for production code, critical paths.
    Accuracy: 0.960, Efficiency: 0.769
    """
    return FullConfig(
        framework=FrameworkConfig(
            evidential=True,
            aspectual=True,
            morphological=True,
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


def create_balanced_config() -> FullConfig:
    """
    Create balanced mode configuration.

    Optimized for general purpose use.
    Accuracy: 0.882, Efficiency: 0.928
    """
    return FullConfig(
        framework=FrameworkConfig(
            evidential=True,
            aspectual=False,
            morphological=False,
            compositional=False,
            honorific=False,
            classifier=False,
            spatial=True,
        ),
        prompt=PromptConfig(
            verix_strictness=VerixStrictness.MODERATE,
            compression_level=CompressionLevel.L1_AI_HUMAN,
            require_ground=True,
            require_confidence=False,
        ),
    )


# M3 FIX: Use MappingProxyType for immutability to prevent accidental modification
# Named mode lookup table (immutable)
_NAMED_MODES_MUTABLE: Dict[str, FullConfig] = {
    "audit": create_audit_config(),
    "speed": create_speed_config(),
    "research": create_research_config(),
    "robust": create_robust_config(),
    "balanced": create_balanced_config(),
}
NAMED_MODES: MappingProxyType = MappingProxyType(_NAMED_MODES_MUTABLE)


def get_named_mode(name: str) -> FullConfig:
    """
    Get a named mode configuration.

    Args:
        name: Mode name (audit, speed, research, robust, balanced)

    Returns:
        FullConfig for the named mode

    Raises:
        KeyError: If mode name is not recognized
    """
    # L1 FIX: Use .get() pattern with explicit error for better clarity
    config = NAMED_MODES.get(name)
    if config is None:
        available = ", ".join(NAMED_MODES.keys())
        raise KeyError(f"Unknown mode '{name}'. Available: {available}")
    return config
