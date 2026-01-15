"""
Money Handling Pattern - Library Component

CRITICAL RULE: NEVER use float for currency calculations.
This module provides Decimal-based utilities for all financial operations.

Usage:
    from library.patterns.money_handling import Money

    # Create money values (MUST use string or Decimal, NOT float)
    price = Money("123.45")
    quantity = Money.from_cents(10000)  # $100.00

    # Arithmetic (always returns Money)
    total = price * Decimal("10")

    # THESE WILL RAISE TypeError:
    # Money(19.99)  # Float not allowed!
    # price * 1.5   # Float multiplication not allowed!
"""

from .money import (
    Money,
    MoneyError,
    FloatNotAllowedError,
    CurrencyMismatchError,
)
from .operations import add_money, subtract_money, allocate_money
from .formatting import format_money, parse_money
from .validation import validate_amount, is_valid_currency

__all__ = [
    # Core Money class and exceptions
    'Money',
    'MoneyError',
    'FloatNotAllowedError',
    'CurrencyMismatchError',
    # Operations
    'add_money',
    'subtract_money',
    'allocate_money',
    # Formatting
    'format_money',
    'parse_money',
    # Validation
    'validate_amount',
    'is_valid_currency',
]
