"""
Core Money Class - Immutable Decimal-based currency handling.

CRITICAL: This class REJECTS float values to prevent precision errors.
All monetary amounts MUST be provided as Decimal, str, or int.

Adapted from: D:/Projects/trader-ai/src/utils/money.py
Enhanced to: REJECT floats entirely (not just warn)
"""

from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN, InvalidOperation, getcontext
from typing import Union, Optional
from dataclasses import dataclass

# Set precision high enough for financial calculations
getcontext().prec = 28


class MoneyError(Exception):
    """Base exception for money-related errors."""
    pass


class CurrencyMismatchError(MoneyError):
    """Raised when operating on money with different currencies."""
    pass


class FloatNotAllowedError(MoneyError, TypeError):
    """Raised when float is used instead of Decimal/str/int."""
    pass


# Accepted input types (EXCLUDES float!)
MoneyInput = Union['Money', Decimal, str, int]


@dataclass(frozen=True, slots=True)
class Money:
    """
    Immutable Decimal-based money value with STRICT float rejection.

    Uses banker's rounding (ROUND_HALF_EVEN) which is the standard
    for financial calculations to minimize cumulative rounding errors.

    Attributes:
        amount: The underlying Decimal value
        currency: Currency code (default: USD)

    Raises:
        FloatNotAllowedError: If float is passed as amount
        ValueError: If amount cannot be converted to Decimal

    Examples:
        # CORRECT usage
        price = Money(Decimal("19.99"))
        price = Money("19.99")
        price = Money.from_string("19.99")
        price = Money.from_cents(1999)

        # INCORRECT - will raise FloatNotAllowedError
        price = Money(19.99)  # REJECTED!
    """
    amount: Decimal
    currency: str = "USD"

    # Default decimal places for different operations
    PRICE_PLACES = 2      # Prices: 2 decimal places
    QUANTITY_PLACES = 6   # Quantities: 6 decimal places (fractional shares)
    PERCENT_PLACES = 4    # Percentages: 4 decimal places (0.01%)

    def __post_init__(self):
        """Validate and normalize the amount."""
        # CRITICAL: Reject float immediately
        if isinstance(object.__getattribute__(self, 'amount'), float):
            raise FloatNotAllowedError(
                "Money amount must be Decimal, str, or int - NOT float. "
                "Use Money.from_string('19.99') or Money(Decimal('19.99'))"
            )

        # Convert to Decimal if needed
        raw_amount = object.__getattribute__(self, 'amount')
        if not isinstance(raw_amount, Decimal):
            try:
                decimal_amount = Decimal(str(raw_amount))
            except (InvalidOperation, ValueError) as e:
                raise ValueError(f"Cannot convert {raw_amount!r} to Money: {e}") from e
            # Use object.__setattr__ because frozen=True
            object.__setattr__(self, 'amount', decimal_amount)

        # Normalize currency to uppercase
        currency = object.__getattribute__(self, 'currency')
        object.__setattr__(self, 'currency', currency.upper())

    @classmethod
    def from_string(cls, value: str, currency: str = "USD") -> "Money":
        """
        Create Money from a string value.

        Args:
            value: String representation (e.g., "19.99", "1000")
            currency: Currency code

        Returns:
            Money instance
        """
        return cls(Decimal(value), currency)

    @classmethod
    def from_cents(cls, cents: int, currency: str = "USD") -> "Money":
        """
        Create Money from integer cents (avoids float entirely).

        Args:
            cents: Integer cents (e.g., 1999 for $19.99)
            currency: Currency code

        Returns:
            Money instance
        """
        if not isinstance(cents, int):
            raise TypeError("cents must be an integer")
        return cls(Decimal(cents) / Decimal(100), currency)

    @classmethod
    def zero(cls, currency: str = "USD") -> "Money":
        """Create a zero Money value."""
        return cls(Decimal("0"), currency)

    # Arithmetic operations

    def __add__(self, other: "Money") -> "Money":
        """Add two Money values (must be same currency)."""
        self._check_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __radd__(self, other) -> "Money":
        """Support sum() - handles sum([money1, money2]) starting with 0."""
        if other == 0:
            return self
        return self.__add__(other)

    def __sub__(self, other: "Money") -> "Money":
        """Subtract two Money values (must be same currency)."""
        self._check_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Union[int, Decimal]) -> "Money":
        """
        Multiply Money by a scalar (REJECTS float).

        Args:
            factor: int or Decimal multiplier (NOT float!)

        Returns:
            New Money instance

        Raises:
            FloatNotAllowedError: If factor is float
        """
        if isinstance(factor, float):
            raise FloatNotAllowedError(
                "Cannot multiply Money by float. Use Decimal instead: "
                f"money * Decimal('{factor}')"
            )
        if isinstance(factor, Money):
            return Money(self.amount * factor.amount, self.currency)
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def __rmul__(self, factor: Union[int, Decimal]) -> "Money":
        """Support scalar * Money."""
        return self.__mul__(factor)

    def __truediv__(self, divisor: Union[int, Decimal, "Money"]) -> "Money":
        """
        Divide Money by a scalar or Money (REJECTS float).

        Args:
            divisor: int, Decimal, or Money (NOT float!)

        Returns:
            New Money instance

        Raises:
            FloatNotAllowedError: If divisor is float
            ZeroDivisionError: If dividing by zero
        """
        if isinstance(divisor, float):
            raise FloatNotAllowedError(
                "Cannot divide Money by float. Use Decimal instead."
            )

        if isinstance(divisor, Money):
            divisor_val = divisor.amount
        else:
            divisor_val = Decimal(str(divisor))

        if divisor_val == 0:
            raise ZeroDivisionError("Cannot divide Money by zero")

        return Money(self.amount / divisor_val, self.currency)

    def __neg__(self) -> "Money":
        """Negate the value."""
        return Money(-self.amount, self.currency)

    def __abs__(self) -> "Money":
        """Absolute value."""
        return Money(abs(self.amount), self.currency)

    # Comparison operations

    def __eq__(self, other: object) -> bool:
        """Check equality (same amount AND currency)."""
        if isinstance(other, Money):
            return self.amount == other.amount and self.currency == other.currency
        return False

    def __lt__(self, other: "Money") -> bool:
        """Less than comparison."""
        self._check_currency(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        """Less than or equal comparison."""
        self._check_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        """Greater than comparison."""
        self._check_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        """Greater than or equal comparison."""
        self._check_currency(other)
        return self.amount >= other.amount

    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash((self.amount, self.currency))

    # Rounding operations

    def round(self, places: int = 2, rounding: str = ROUND_HALF_EVEN) -> "Money":
        """
        Round to specified decimal places.

        Args:
            places: Number of decimal places (default: 2)
            rounding: Rounding mode (default: ROUND_HALF_EVEN for banker's rounding)

        Returns:
            New Money with rounded value
        """
        quantize_str = '0.' + '0' * places if places > 0 else '1'
        rounded = self.amount.quantize(Decimal(quantize_str), rounding=rounding)
        return Money(rounded, self.currency)

    def round_to_cents(self) -> "Money":
        """Round to cents (2 decimal places) using banker's rounding."""
        return self.round(self.PRICE_PLACES)

    # Conversion methods

    def to_decimal(self) -> Decimal:
        """Get the Decimal value (preferred over to_float)."""
        return self.amount

    def to_cents(self) -> int:
        """Convert to integer cents."""
        return int(self.round_to_cents().amount * 100)

    def to_float(self) -> float:
        """
        Convert to float (USE SPARINGLY - only for external APIs).

        Warning: This loses precision. Only use when external API requires float.
        """
        return float(self.amount)

    # String representations

    def __str__(self) -> str:
        """Human-readable string with currency symbol."""
        if self.currency == 'USD':
            return f"${self.amount:,.2f}"
        return f"{self.amount:,.2f} {self.currency}"

    def __repr__(self) -> str:
        """Debug representation."""
        return f"Money({self.amount!r}, {self.currency!r})"

    # Internal helpers

    def _check_currency(self, other: "Money") -> None:
        """Verify currency compatibility."""
        if not isinstance(other, Money):
            raise TypeError(f"Expected Money, got {type(other).__name__}")
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )


# Convenience constants
ZERO_USD = Money.zero("USD")
ZERO_EUR = Money.zero("EUR")
