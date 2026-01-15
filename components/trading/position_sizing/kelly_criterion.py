"""
Kelly Criterion Position Sizing Calculator

A generalized, standalone implementation of the Kelly Criterion for optimal
position sizing in trading and betting scenarios.

Mathematical Foundation:
    Kelly % = (bp - q) / b

    where:
        b = odds (win amount / loss amount)
        p = probability of winning
        q = probability of losing (1 - p)

Features:
    - Full Kelly fraction calculation
    - Fractional Kelly (half-Kelly, quarter-Kelly, custom)
    - Maximum position cap (overleverage protection)
    - Risk-adjusted sizing
    - Uses Decimal for financial precision (NEVER float for money!)

Usage:
    from kelly_criterion import KellyCriterion

    kelly = KellyCriterion(max_kelly_fraction=Decimal("0.25"))
    result = kelly.calculate(
        win_probability=Decimal("0.55"),
        win_loss_ratio=Decimal("1.5")
    )

    position_size = kelly.position_size(
        capital=Decimal("10000"),
        win_probability=Decimal("0.55"),
        win_loss_ratio=Decimal("1.5"),
        fraction=Decimal("0.5")  # Half-Kelly
    )

Author: Extracted from trader-ai project
License: MIT
"""

from decimal import Decimal, ROUND_DOWN, InvalidOperation
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class KellyRegime(Enum):
    """Kelly calculation regimes for position sizing guidance."""

    AGGRESSIVE = "aggressive"      # Kelly > 25%
    MODERATE = "moderate"          # 10% < Kelly <= 25%
    CONSERVATIVE = "conservative"  # 5% < Kelly <= 10%
    MINIMAL = "minimal"            # 0% < Kelly <= 5%
    NO_BET = "no_bet"             # Kelly <= 0%


@dataclass(frozen=True)
class KellyResult:
    """
    Result of a Kelly criterion calculation.

    Attributes:
        raw_kelly: Unconstrained Kelly percentage (can be > 1.0)
        capped_kelly: Kelly capped at maximum allowed (default 1.0)
        final_kelly: Final Kelly after applying fraction multiplier
        win_probability: Input win probability
        loss_probability: Calculated loss probability (1 - win_prob)
        win_loss_ratio: Input win/loss ratio (odds)
        edge: Calculated edge ((b * p) - q)
        regime: Kelly regime classification
        is_favorable: Whether the bet has positive expected value
    """
    raw_kelly: Decimal
    capped_kelly: Decimal
    final_kelly: Decimal
    win_probability: Decimal
    loss_probability: Decimal
    win_loss_ratio: Decimal
    edge: Decimal
    regime: KellyRegime
    is_favorable: bool

    def __str__(self) -> str:
        return (
            f"KellyResult(kelly={self.final_kelly:.4f}, "
            f"regime={self.regime.value}, favorable={self.is_favorable})"
        )


@dataclass(frozen=True)
class PositionSizeResult:
    """
    Result of a position size calculation.

    Attributes:
        position_size: Recommended position size in currency units
        kelly_result: Underlying Kelly calculation result
        capital: Input capital amount
        fraction_used: Kelly fraction multiplier used
        max_position_cap: Maximum position cap applied (if any)
    """
    position_size: Decimal
    kelly_result: KellyResult
    capital: Decimal
    fraction_used: Decimal
    max_position_cap: Optional[Decimal]

    @property
    def position_percentage(self) -> Decimal:
        """Position size as percentage of capital."""
        if self.capital == 0:
            return Decimal("0")
        return (self.position_size / self.capital * 100).quantize(
            Decimal("0.01"), rounding=ROUND_DOWN
        )


class KellyCriterion:
    """
    Kelly Criterion calculator for optimal position sizing.

    The Kelly Criterion provides the mathematically optimal bet size
    to maximize long-term geometric growth rate of capital.

    IMPORTANT: This class uses Decimal throughout for financial precision.
    Never use float for monetary calculations!

    Attributes:
        max_kelly_fraction: Maximum allowed Kelly percentage (default 1.0)
        min_edge: Minimum edge required to recommend a position (default 0.01)
        default_fraction: Default Kelly fraction multiplier (default 1.0)

    Example:
        >>> kelly = KellyCriterion(max_kelly_fraction=Decimal("0.25"))
        >>> result = kelly.calculate(
        ...     win_probability=Decimal("0.60"),
        ...     win_loss_ratio=Decimal("1.5")
        ... )
        >>> print(result.final_kelly)
        Decimal('0.2500')
    """

    # Standard fractional Kelly values
    FULL_KELLY = Decimal("1.0")
    HALF_KELLY = Decimal("0.5")
    QUARTER_KELLY = Decimal("0.25")
    TENTH_KELLY = Decimal("0.1")

    def __init__(
        self,
        max_kelly_fraction: Decimal = Decimal("1.0"),
        min_edge: Decimal = Decimal("0.01"),
        default_fraction: Decimal = Decimal("1.0")
    ):
        """
        Initialize Kelly Criterion calculator.

        Args:
            max_kelly_fraction: Maximum allowed Kelly % (0-1). Default 1.0.
                               Use 0.25 for conservative, 0.5 for moderate.
            min_edge: Minimum edge required for a position (default 1%)
            default_fraction: Default Kelly fraction multiplier (default full Kelly)

        Raises:
            ValueError: If parameters are out of valid range
        """
        self._validate_decimal(max_kelly_fraction, "max_kelly_fraction")
        self._validate_decimal(min_edge, "min_edge")
        self._validate_decimal(default_fraction, "default_fraction")

        if not Decimal("0") < max_kelly_fraction <= Decimal("1"):
            raise ValueError("max_kelly_fraction must be between 0 and 1 (exclusive/inclusive)")

        if min_edge < Decimal("0"):
            raise ValueError("min_edge must be non-negative")

        if not Decimal("0") < default_fraction <= Decimal("1"):
            raise ValueError("default_fraction must be between 0 and 1 (exclusive/inclusive)")

        self.max_kelly_fraction = max_kelly_fraction
        self.min_edge = min_edge
        self.default_fraction = default_fraction

        logger.debug(
            f"KellyCriterion initialized: max={max_kelly_fraction}, "
            f"min_edge={min_edge}, default_fraction={default_fraction}"
        )

    def calculate(
        self,
        win_probability: Decimal,
        win_loss_ratio: Decimal,
        fraction: Optional[Decimal] = None
    ) -> KellyResult:
        """
        Calculate the Kelly criterion percentage.

        Formula: Kelly % = (bp - q) / b

        where:
            b = win_loss_ratio (odds)
            p = win_probability
            q = loss_probability = 1 - p

        Args:
            win_probability: Probability of winning (0 to 1)
            win_loss_ratio: Ratio of win amount to loss amount (odds)
            fraction: Kelly fraction multiplier (default: self.default_fraction)
                     Use 0.5 for half-Kelly, 0.25 for quarter-Kelly

        Returns:
            KellyResult with all calculation details

        Raises:
            ValueError: If input parameters are invalid

        Example:
            >>> kelly = KellyCriterion()
            >>> # 60% win rate, 1.5:1 payout
            >>> result = kelly.calculate(Decimal("0.60"), Decimal("1.5"))
            >>> print(f"Kelly: {result.final_kelly:.2%}")
            Kelly: 26.67%
        """
        # Validate inputs
        self._validate_decimal(win_probability, "win_probability")
        self._validate_decimal(win_loss_ratio, "win_loss_ratio")

        if not Decimal("0") < win_probability < Decimal("1"):
            raise ValueError("win_probability must be between 0 and 1 (exclusive)")

        if win_loss_ratio <= Decimal("0"):
            raise ValueError("win_loss_ratio must be positive")

        if fraction is not None:
            self._validate_decimal(fraction, "fraction")
            if not Decimal("0") < fraction <= Decimal("1"):
                raise ValueError("fraction must be between 0 and 1 (exclusive/inclusive)")

        fraction = fraction or self.default_fraction

        # Calculate loss probability
        loss_probability = Decimal("1") - win_probability

        # Calculate edge: (bp - q)
        edge = (win_loss_ratio * win_probability) - loss_probability

        # Calculate raw Kelly: (bp - q) / b
        raw_kelly = edge / win_loss_ratio

        # Determine if bet is favorable
        is_favorable = edge > Decimal("0") and edge >= self.min_edge

        # Cap Kelly at maximum allowed
        capped_kelly = min(max(raw_kelly, Decimal("0")), self.max_kelly_fraction)

        # Apply fraction multiplier
        final_kelly = capped_kelly * fraction

        # If edge is below minimum, return zero
        if not is_favorable:
            final_kelly = Decimal("0")

        # Determine regime
        regime = self._classify_regime(final_kelly)

        result = KellyResult(
            raw_kelly=raw_kelly.quantize(Decimal("0.0001")),
            capped_kelly=capped_kelly.quantize(Decimal("0.0001")),
            final_kelly=final_kelly.quantize(Decimal("0.0001")),
            win_probability=win_probability,
            loss_probability=loss_probability,
            win_loss_ratio=win_loss_ratio,
            edge=edge.quantize(Decimal("0.0001")),
            regime=regime,
            is_favorable=is_favorable
        )

        logger.debug(f"Kelly calculation: {result}")
        return result

    def position_size(
        self,
        capital: Decimal,
        win_probability: Decimal,
        win_loss_ratio: Decimal,
        fraction: Optional[Decimal] = None,
        max_position: Optional[Decimal] = None
    ) -> PositionSizeResult:
        """
        Calculate recommended position size in currency units.

        Args:
            capital: Total available capital
            win_probability: Probability of winning (0 to 1)
            win_loss_ratio: Ratio of win amount to loss amount
            fraction: Kelly fraction multiplier (default: self.default_fraction)
            max_position: Maximum position size cap (optional)

        Returns:
            PositionSizeResult with position size and calculation details

        Raises:
            ValueError: If input parameters are invalid

        Example:
            >>> kelly = KellyCriterion(max_kelly_fraction=Decimal("0.25"))
            >>> result = kelly.position_size(
            ...     capital=Decimal("10000"),
            ...     win_probability=Decimal("0.55"),
            ...     win_loss_ratio=Decimal("1.5"),
            ...     fraction=Decimal("0.5")  # Half-Kelly
            ... )
            >>> print(f"Position: ${result.position_size:.2f}")
        """
        self._validate_decimal(capital, "capital")

        if capital < Decimal("0"):
            raise ValueError("capital must be non-negative")

        if max_position is not None:
            self._validate_decimal(max_position, "max_position")
            if max_position < Decimal("0"):
                raise ValueError("max_position must be non-negative")

        # Calculate Kelly percentage
        kelly_result = self.calculate(win_probability, win_loss_ratio, fraction)

        # Calculate position size
        position_size = capital * kelly_result.final_kelly

        # Apply maximum position cap if specified
        if max_position is not None and position_size > max_position:
            position_size = max_position

        # Round down to avoid overallocation
        position_size = position_size.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

        return PositionSizeResult(
            position_size=position_size,
            kelly_result=kelly_result,
            capital=capital,
            fraction_used=fraction or self.default_fraction,
            max_position_cap=max_position
        )

    def calculate_from_history(
        self,
        wins: int,
        losses: int,
        average_win: Decimal,
        average_loss: Decimal,
        fraction: Optional[Decimal] = None
    ) -> KellyResult:
        """
        Calculate Kelly criterion from historical trading data.

        Args:
            wins: Number of winning trades
            losses: Number of losing trades
            average_win: Average profit on winning trades
            average_loss: Average loss on losing trades (as positive number)
            fraction: Kelly fraction multiplier

        Returns:
            KellyResult based on historical statistics

        Raises:
            ValueError: If input parameters are invalid

        Example:
            >>> kelly = KellyCriterion()
            >>> result = kelly.calculate_from_history(
            ...     wins=60, losses=40,
            ...     average_win=Decimal("150"),
            ...     average_loss=Decimal("100")
            ... )
        """
        if wins < 0 or losses < 0:
            raise ValueError("wins and losses must be non-negative")

        if wins + losses == 0:
            raise ValueError("Must have at least one trade")

        self._validate_decimal(average_win, "average_win")
        self._validate_decimal(average_loss, "average_loss")

        if average_win <= Decimal("0"):
            raise ValueError("average_win must be positive")

        if average_loss <= Decimal("0"):
            raise ValueError("average_loss must be positive")

        # Calculate win probability
        total_trades = wins + losses
        win_probability = Decimal(str(wins)) / Decimal(str(total_trades))

        # Calculate win/loss ratio (odds)
        win_loss_ratio = average_win / average_loss

        return self.calculate(win_probability, win_loss_ratio, fraction)

    def optimal_fraction_for_drawdown(
        self,
        win_probability: Decimal,
        win_loss_ratio: Decimal,
        max_drawdown_tolerance: Decimal
    ) -> Tuple[Decimal, KellyResult]:
        """
        Find the Kelly fraction that limits expected drawdown.

        Uses the approximation that expected maximum drawdown is roughly
        proportional to the Kelly fraction used.

        Args:
            win_probability: Probability of winning
            win_loss_ratio: Ratio of win amount to loss amount
            max_drawdown_tolerance: Maximum acceptable drawdown (e.g., 0.20 for 20%)

        Returns:
            Tuple of (optimal_fraction, KellyResult)

        Example:
            >>> kelly = KellyCriterion()
            >>> fraction, result = kelly.optimal_fraction_for_drawdown(
            ...     win_probability=Decimal("0.55"),
            ...     win_loss_ratio=Decimal("1.5"),
            ...     max_drawdown_tolerance=Decimal("0.15")  # 15% max DD
            ... )
        """
        self._validate_decimal(max_drawdown_tolerance, "max_drawdown_tolerance")

        if not Decimal("0") < max_drawdown_tolerance < Decimal("1"):
            raise ValueError("max_drawdown_tolerance must be between 0 and 1")

        # First calculate full Kelly
        full_kelly_result = self.calculate(
            win_probability, win_loss_ratio, Decimal("1.0")
        )

        if not full_kelly_result.is_favorable:
            return Decimal("0"), full_kelly_result

        # Approximate optimal fraction based on drawdown tolerance
        # Using simplified relationship: DD ~ 2 * kelly_fraction * volatility
        # We use a conservative approximation
        optimal_fraction = min(
            max_drawdown_tolerance / (full_kelly_result.capped_kelly * Decimal("2")),
            Decimal("1.0")
        )
        optimal_fraction = max(optimal_fraction, Decimal("0.1"))  # Minimum 10%

        result = self.calculate(win_probability, win_loss_ratio, optimal_fraction)

        return optimal_fraction.quantize(Decimal("0.01")), result

    def risk_of_ruin(
        self,
        win_probability: Decimal,
        win_loss_ratio: Decimal,
        kelly_fraction: Decimal,
        ruin_threshold: Decimal = Decimal("0.5")
    ) -> Decimal:
        """
        Estimate probability of ruin (losing a significant portion of capital).

        Uses the simplified formula:
            P(ruin) ~ exp(-2 * edge * fraction / variance)

        Args:
            win_probability: Probability of winning
            win_loss_ratio: Ratio of win amount to loss amount
            kelly_fraction: Kelly fraction being used
            ruin_threshold: What constitutes "ruin" (default 50% loss)

        Returns:
            Estimated probability of ruin

        Note:
            This is an approximation. Actual risk depends on many factors
            including bet sizing, number of bets, and correlation.
        """
        self._validate_decimal(kelly_fraction, "kelly_fraction")
        self._validate_decimal(ruin_threshold, "ruin_threshold")

        loss_prob = Decimal("1") - win_probability
        edge = (win_loss_ratio * win_probability) - loss_prob

        if edge <= Decimal("0"):
            return Decimal("1.0")  # Certain ruin with negative edge

        # Approximate variance
        variance = win_probability * (Decimal("1") - win_probability)

        if variance == Decimal("0"):
            return Decimal("0")

        # Risk of ruin approximation
        try:
            exponent = Decimal("-2") * edge * kelly_fraction / variance
            # Use float for exp calculation, then convert back
            import math
            risk = Decimal(str(math.exp(float(exponent))))
            return min(risk, Decimal("1.0")).quantize(Decimal("0.0001"))
        except (OverflowError, InvalidOperation):
            return Decimal("0.0001")  # Very low risk

    def _classify_regime(self, kelly_percentage: Decimal) -> KellyRegime:       
        """Classify Kelly percentage into a risk regime."""
        if kelly_percentage <= Decimal("0"):
            return KellyRegime.NO_BET
        if kelly_percentage <= Decimal("0.05"):
            return KellyRegime.MINIMAL
        if kelly_percentage <= Decimal("0.10"):
            return KellyRegime.CONSERVATIVE
        if kelly_percentage <= Decimal("0.25"):
            return KellyRegime.MODERATE
        return KellyRegime.AGGRESSIVE

    @staticmethod
    def _validate_decimal(value, name: str) -> None:
        """Validate that a value is a Decimal."""
        if not isinstance(value, Decimal):
            raise TypeError(
                f"{name} must be a Decimal, got {type(value).__name__}. "
                f"Use Decimal('{value}') instead of {value}"
            )


def quick_kelly(
    win_prob: float,
    win_loss_ratio: float,
    fraction: float = 1.0
) -> float:
    """
    Quick Kelly calculation for exploration/prototyping.

    .. deprecated::
        This function uses float and is deprecated for production use.
        Use KellyCriterion class with Decimal for actual trading.

    WARNING: Uses float for convenience. Do NOT use for actual trading!
    Use KellyCriterion class with Decimal for production code.

    Args:
        win_prob: Probability of winning (0 to 1)
        win_loss_ratio: Win amount / Loss amount
        fraction: Kelly fraction multiplier (default 1.0 = full Kelly)

    Returns:
        Kelly percentage as float

    Example:
        >>> quick_kelly(0.55, 1.5, 0.5)  # Half Kelly
        0.0833...
    """
    import warnings
    warnings.warn(
        "quick_kelly() uses float and is deprecated for production use. "
        "Use KellyCriterion class with Decimal for actual trading calculations.",
        DeprecationWarning,
        stacklevel=2
    )
    if not 0 < win_prob < 1 or win_loss_ratio <= 0:
        return 0.0

    loss_prob = 1 - win_prob
    edge = (win_loss_ratio * win_prob) - loss_prob

    if edge <= 0:
        return 0.0

    kelly = (edge / win_loss_ratio) * fraction
    return max(0.0, min(kelly, 1.0))


if __name__ == "__main__":
    # Demo usage
    print("Kelly Criterion Position Sizing Demo")
    print("=" * 50)

    kelly = KellyCriterion(
        max_kelly_fraction=Decimal("0.25"),
        min_edge=Decimal("0.01")
    )

    # Example 1: Basic calculation
    print("\n1. Basic Kelly Calculation")
    print("-" * 30)
    result = kelly.calculate(
        win_probability=Decimal("0.55"),
        win_loss_ratio=Decimal("1.5")
    )
    print(f"Win Probability: 55%")
    print(f"Win/Loss Ratio: 1.5:1")
    print(f"Raw Kelly: {result.raw_kelly:.2%}")
    print(f"Final Kelly (capped at 25%): {result.final_kelly:.2%}")
    print(f"Regime: {result.regime.value}")
    print(f"Edge: {result.edge:.2%}")

    # Example 2: Position sizing
    print("\n2. Position Sizing")
    print("-" * 30)
    pos_result = kelly.position_size(
        capital=Decimal("10000"),
        win_probability=Decimal("0.55"),
        win_loss_ratio=Decimal("1.5"),
        fraction=Decimal("0.5")  # Half-Kelly
    )
    print(f"Capital: $10,000")
    print(f"Fraction: Half-Kelly (50%)")
    print(f"Position Size: ${pos_result.position_size:.2f}")
    print(f"Position %: {pos_result.position_percentage:.2f}%")

    # Example 3: From history
    print("\n3. Calculate from Trading History")
    print("-" * 30)
    hist_result = kelly.calculate_from_history(
        wins=65,
        losses=35,
        average_win=Decimal("200"),
        average_loss=Decimal("150")
    )
    print(f"Wins: 65, Losses: 35")
    print(f"Avg Win: $200, Avg Loss: $150")
    print(f"Calculated Kelly: {hist_result.final_kelly:.2%}")
    print(f"Is Favorable: {hist_result.is_favorable}")

    # Example 4: Different fractions
    print("\n4. Kelly Fractions Comparison")
    print("-" * 30)
    fractions = [
        ("Full Kelly", Decimal("1.0")),
        ("Half Kelly", Decimal("0.5")),
        ("Quarter Kelly", Decimal("0.25")),
        ("Tenth Kelly", Decimal("0.1"))
    ]

    for name, frac in fractions:
        r = kelly.calculate(
            win_probability=Decimal("0.60"),
            win_loss_ratio=Decimal("2.0"),
            fraction=frac
        )
        print(f"{name:15} -> Kelly: {r.final_kelly:.2%}")

    print("\n" + "=" * 50)
    print("Use Decimal types for all monetary calculations!")
