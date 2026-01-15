"""
VERIX Epistemic Notation Parser

A standalone Python library for parsing, validating, and creating VERIX-formatted
epistemic claims. VERIX provides structured notation for expressing claims with
explicit confidence levels, evidence sources, and speech act types.

This module provides:
- Parsing of L0 (shorthand) and L1 (annotated) VERIX formats
- Creation of well-formed epistemic claims
- Validation against configurable strictness levels
- Formatting at different compression levels (L0, L1, L2)

Example Usage:
    from verix_parser import (
        VerixParser, VerixValidator, create_claim, format_claim,
        Illocution, Affect, State, Agent, CompressionLevel
    )

    # Parse existing VERIX text
    parser = VerixParser()
    claims = parser.parse("[assert|neutral] Claim content [conf:0.85] [state:confirmed]")

    # Create new claims
    claim = create_claim("My assertion", confidence=0.9, ground="direct observation")

    # Format at different levels
    l1 = format_claim(claim, CompressionLevel.L1_AI_HUMAN)
    l2 = format_claim(claim, CompressionLevel.L2_HUMAN)

    # Validate
    validator = VerixValidator()
    is_valid, violations = validator.validate(claims)
"""

from .verix_parser import (
    # Version
    __version__,
    VERSION,
    # Constants
    MAX_INPUT_LENGTH,
    MAX_CLAIMS_LIMIT,
    L0_CONTENT_TRUNCATION_LENGTH,
    # Enums
    Illocution,
    Affect,
    State,
    Agent,
    MetaLevel,
    VerixStrictness,
    CompressionLevel,
    # Data classes
    VerixClaim,
    PromptConfig,
    # Classes
    VerixParser,
    VerixValidator,
    # Functions
    create_claim,
    create_meta_claim,
    create_meta_verix_claim,
    format_claim,
)

__all__ = [
    # Version
    "__version__",
    "VERSION",
    # Constants
    "MAX_INPUT_LENGTH",
    "MAX_CLAIMS_LIMIT",
    "L0_CONTENT_TRUNCATION_LENGTH",
    # Enums
    "Illocution",
    "Affect",
    "State",
    "Agent",
    "MetaLevel",
    "VerixStrictness",
    "CompressionLevel",
    # Data classes
    "VerixClaim",
    "PromptConfig",
    # Classes
    "VerixParser",
    "VerixValidator",
    # Functions
    "create_claim",
    "create_meta_claim",
    "create_meta_verix_claim",
    "format_claim",
]
