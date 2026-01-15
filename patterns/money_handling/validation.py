"""
Money Validation - Input validation utilities.
"""

from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple
from .money import Money, MoneyError


# ISO 4217 currency codes (common subset)
VALID_CURRENCIES = {
    'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'HKD', 'NZD',
    'SEK', 'NOK', 'DKK', 'SGD', 'MXN', 'BRL', 'KRW', 'INR', 'RUB', 'ZAR',
}


class ValidationError(MoneyError):
    """Raised when validation fails."""
    pass


def is_valid_currency(code: str) -> bool:
    """
    Check if currency code is valid ISO 4217.

    Args:
        code: Currency code to validate

    Returns:
        True if valid, False otherwise
    """
    return code.upper() in VALID_CURRENCIES


def validate_amount(
    value: str,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    allow_negative: bool = True,
    allow_zero: bool = True,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a string amount.

    Args:
        value: String value to validate
        min_amount: Minimum allowed amount (optional)
        max_amount: Maximum allowed amount (optional)
        allow_negative: Whether negative amounts are allowed
        allow_zero: Whether zero is allowed

    Returns:
        Tuple of (is_valid, error_message or None)

    Examples:
        validate_amount("100.00")  # (True, None)
        validate_amount("-50", allow_negative=False)  # (False, "Negative amounts not allowed")
        validate_amount("abc")  # (False, "Invalid numeric format")
    """
    # Try to parse as Decimal
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        return False, "Invalid numeric format"

    # Check for negative
    if not allow_negative and amount < 0:
        return False, "Negative amounts not allowed"

    # Check for zero
    if not allow_zero and amount == 0:
        return False, "Zero amount not allowed"

    # Check minimum
    if min_amount is not None and amount < min_amount:
        return False, f"Amount must be at least {min_amount}"

    # Check maximum
    if max_amount is not None and amount > max_amount:
        return False, f"Amount must be at most {max_amount}"

    return True, None


def validate_money(
    money: Money,
    min_amount: Optional[Money] = None,
    max_amount: Optional[Money] = None,
    allowed_currencies: Optional[set] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate a Money object.

    Args:
        money: Money object to validate
        min_amount: Minimum allowed (optional, must match currency)
        max_amount: Maximum allowed (optional, must match currency)
        allowed_currencies: Set of allowed currency codes (optional)

    Returns:
        Tuple of (is_valid, error_message or None)
    """
    # Check currency
    if allowed_currencies and money.currency not in allowed_currencies:
        return False, f"Currency {money.currency} not in allowed list: {allowed_currencies}"

    # Check minimum
    if min_amount is not None:
        if min_amount.currency != money.currency:
            return False, "Currency mismatch in min_amount comparison"
        if money < min_amount:
            return False, f"Amount must be at least {min_amount}"

    # Check maximum
    if max_amount is not None:
        if max_amount.currency != money.currency:
            return False, "Currency mismatch in max_amount comparison"
        if money > max_amount:
            return False, f"Amount must be at most {max_amount}"

    return True, None


def sanitize_amount_string(value: str) -> str:
    """
    Sanitize a user-input amount string.

    Removes currency symbols, extra whitespace, and normalizes format.

    Args:
        value: Raw user input

    Returns:
        Cleaned string suitable for Decimal()

    Examples:
        sanitize_amount_string("$1,234.56")  # "1234.56"
        sanitize_amount_string("  100  ")  # "100"
    """
    # Remove currency symbols and whitespace
    cleaned = value.strip()
    cleaned = cleaned.replace('$', '').replace(',', '').strip()

    # Handle accounting format (parentheses for negative)
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = '-' + cleaned[1:-1]

    return cleaned
