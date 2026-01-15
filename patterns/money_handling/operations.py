"""
Money Operations - Safe arithmetic operations for Money values.
"""

from decimal import Decimal
from typing import List, Sequence
from .money import Money, MoneyError


def add_money(*amounts: Money) -> Money:
    """
    Add multiple Money values together.

    Args:
        *amounts: Money values to add (must all be same currency)

    Returns:
        Sum of all amounts

    Raises:
        CurrencyMismatchError: If currencies don't match
        ValueError: If no amounts provided
    """
    if not amounts:
        raise ValueError("At least one Money value required")

    result = amounts[0]
    for amount in amounts[1:]:
        result = result + amount
    return result


def subtract_money(minuend: Money, *subtrahends: Money) -> Money:
    """
    Subtract multiple Money values from a starting value.

    Args:
        minuend: The starting value
        *subtrahends: Values to subtract

    Returns:
        Result of subtraction

    Raises:
        CurrencyMismatchError: If currencies don't match
    """
    result = minuend
    for subtrahend in subtrahends:
        result = result - subtrahend
    return result


def allocate_money(amount: Money, ratios: Sequence[Decimal]) -> List[Money]:
    """
    Allocate money according to ratios (handles remainders correctly).

    This is useful for splitting bills, calculating tax distributions, etc.
    The allocation ensures no money is lost due to rounding by distributing
    any remainder to the first items.

    Args:
        amount: Total amount to allocate
        ratios: Ratios for allocation (will be normalized)

    Returns:
        List of Money values matching the length of ratios

    Example:
        # Split $100 three ways: 50%, 30%, 20%
        allocate_money(Money("100"), [Decimal("50"), Decimal("30"), Decimal("20")])
        # Returns: [Money("50.00"), Money("30.00"), Money("20.00")]

        # Split $10 three ways equally (handles remainder)
        allocate_money(Money("10"), [Decimal("1"), Decimal("1"), Decimal("1")])
        # Returns: [Money("3.34"), Money("3.33"), Money("3.33")]
    """
    if not ratios:
        raise ValueError("At least one ratio required")

    # Normalize ratios to sum to 1
    total_ratio = sum(ratios)
    if total_ratio == 0:
        raise ValueError("Ratios sum to zero")

    normalized = [r / total_ratio for r in ratios]

    # Calculate allocations
    allocations = []
    remaining = amount.amount

    for i, ratio in enumerate(normalized[:-1]):
        # Calculate this allocation and round to cents
        allocation = (amount.amount * ratio).quantize(Decimal("0.01"))
        allocations.append(Money(allocation, amount.currency))
        remaining -= allocation

    # Last allocation gets the remainder (no money lost)
    allocations.append(Money(remaining, amount.currency))

    return allocations


def sum_money(amounts: Sequence[Money]) -> Money:
    """
    Sum a sequence of Money values.

    Args:
        amounts: Sequence of Money values (must all be same currency)

    Returns:
        Sum of all amounts, or zero if empty

    Raises:
        CurrencyMismatchError: If currencies don't match
    """
    if not amounts:
        return Money.zero()
    return sum(amounts[1:], amounts[0])


def max_money(*amounts: Money) -> Money:
    """Return the maximum of multiple Money values."""
    if not amounts:
        raise ValueError("At least one Money value required")
    return max(amounts, key=lambda m: m.amount)


def min_money(*amounts: Money) -> Money:
    """Return the minimum of multiple Money values."""
    if not amounts:
        raise ValueError("At least one Money value required")
    return min(amounts, key=lambda m: m.amount)
