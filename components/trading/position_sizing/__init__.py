"""
Position Sizing Library Components

A collection of position sizing algorithms for trading and betting,
with a focus on the Kelly Criterion and its variants.

All calculations use Decimal for financial precision.

Usage:
    from position_sizing import KellyCriterion, KellyResult
    from decimal import Decimal

    kelly = KellyCriterion(max_kelly_fraction=Decimal("0.25"))
    result = kelly.calculate(
        win_probability=Decimal("0.55"),
        win_loss_ratio=Decimal("1.5")
    )

Available Classes:
    - KellyCriterion: Main Kelly criterion calculator
    - KellyResult: Result of Kelly calculation
    - PositionSizeResult: Result of position size calculation
    - KellyRegime: Enum for Kelly regimes (aggressive, moderate, etc.)

Available Functions:
    - quick_kelly: Quick float-based Kelly for prototyping only

Constants:
    - FULL_KELLY: Decimal("1.0")
    - HALF_KELLY: Decimal("0.5")
    - QUARTER_KELLY: Decimal("0.25")
    - TENTH_KELLY: Decimal("0.1")
"""

from .kelly_criterion import (
    KellyCriterion,
    KellyResult,
    PositionSizeResult,
    KellyRegime,
    quick_kelly,
)

from decimal import Decimal

# Standard Kelly fraction constants
FULL_KELLY = Decimal("1.0")
HALF_KELLY = Decimal("0.5")
QUARTER_KELLY = Decimal("0.25")
TENTH_KELLY = Decimal("0.1")

__all__ = [
    # Classes
    "KellyCriterion",
    "KellyResult",
    "PositionSizeResult",
    "KellyRegime",
    # Functions
    "quick_kelly",
    # Constants
    "FULL_KELLY",
    "HALF_KELLY",
    "QUARTER_KELLY",
    "TENTH_KELLY",
]

__version__ = "1.0.0"
