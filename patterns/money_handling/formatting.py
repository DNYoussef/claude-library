"""
Money Formatting - Display and parsing utilities for Money values.
"""

from decimal import Decimal, InvalidOperation
from typing import Optional
import re
from .money import Money


# Currency symbols mapping
CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': 'E',
    'GBP': 'L',
    'JPY': 'Y',
    'CAD': 'C$',
    'AUD': 'A$',
    'CHF': 'CHF',
}

# Regex for parsing formatted money strings
MONEY_PATTERN = re.compile(
    r'^[\$ELYCAD]*\s*'           # Optional currency symbol
    r'(-?)'                        # Optional negative sign
    r'[\s]*'
    r'([0-9]{1,3}(?:,?[0-9]{3})*)'  # Integer part with optional commas
    r'(?:\.([0-9]{1,2}))?'         # Optional decimal part
    r'[\s]*'
    r'([A-Z]{3})?$'                # Optional currency code
)


def format_money(
    amount: Money,
    show_symbol: bool = True,
    show_code: bool = False,
    places: int = 2,
    thousands_sep: str = ",",
    decimal_sep: str = "."
) -> str:
    """
    Format Money value for display.

    Args:
        amount: Money value to format
        show_symbol: Include currency symbol (e.g., $)
        show_code: Include currency code (e.g., USD)
        places: Decimal places to show
        thousands_sep: Thousands separator
        decimal_sep: Decimal separator

    Returns:
        Formatted string

    Examples:
        format_money(Money("1234.56"))  # "$1,234.56"
        format_money(Money("1234.56"), show_code=True)  # "$1,234.56 USD"
        format_money(Money("1234.56", "EUR"))  # "E1,234.56"
    """
    # Round to specified places
    rounded = amount.round(places)

    # Format the number
    abs_value = abs(rounded.amount)
    int_part = int(abs_value)
    dec_part = abs_value - int_part

    # Add thousands separators
    int_str = ""
    int_remaining = int_part
    while int_remaining:
        if int_str:
            int_str = thousands_sep + int_str
        int_str = str(int_remaining % 1000).zfill(3 if int_remaining >= 1000 else 0) + int_str
        int_remaining //= 1000
    int_str = int_str.lstrip('0') or '0'

    # Format decimal part
    if places > 0:
        dec_str = str(dec_part)[2:2+places].ljust(places, '0')
        number_str = f"{int_str}{decimal_sep}{dec_str}"
    else:
        number_str = int_str

    # Add negative sign if needed
    if rounded.amount < 0:
        number_str = f"-{number_str}"

    # Add currency symbol
    result = ""
    if show_symbol:
        symbol = CURRENCY_SYMBOLS.get(amount.currency, '')
        result = f"{symbol}{number_str}"
    else:
        result = number_str

    # Add currency code
    if show_code:
        result = f"{result} {amount.currency}"

    return result


def parse_money(
    value: str,
    default_currency: str = "USD"
) -> Money:
    """
    Parse a formatted money string into Money.

    Args:
        value: String to parse (e.g., "$1,234.56", "1234.56 USD", "1234")
        default_currency: Currency to use if not specified in string

    Returns:
        Money instance

    Raises:
        ValueError: If string cannot be parsed

    Examples:
        parse_money("$1,234.56")  # Money("1234.56", "USD")
        parse_money("1234.56 EUR")  # Money("1234.56", "EUR")
        parse_money("-$50.00")  # Money("-50.00", "USD")
    """
    # Clean the input
    cleaned = value.strip()

    # Try to match the pattern
    match = MONEY_PATTERN.match(cleaned)
    if not match:
        # Try simpler numeric parse
        try:
            # Remove common currency symbols and commas
            numeric = re.sub(r'[\$,ELYCAD]', '', cleaned).strip()
            return Money(Decimal(numeric), default_currency)
        except (InvalidOperation, ValueError):
            raise ValueError(f"Cannot parse '{value}' as money")

    negative = match.group(1) == '-'
    int_part = match.group(2).replace(',', '')
    dec_part = match.group(3) or '00'
    currency = match.group(4) or default_currency

    # Build decimal string
    decimal_str = f"{int_part}.{dec_part}"
    if negative:
        decimal_str = f"-{decimal_str}"

    return Money(Decimal(decimal_str), currency)


def format_accounting(amount: Money, places: int = 2) -> str:
    """
    Format Money in accounting style (negatives in parentheses).

    Args:
        amount: Money value
        places: Decimal places

    Returns:
        Formatted string with negatives in parentheses

    Examples:
        format_accounting(Money("100.00"))  # "$100.00"
        format_accounting(Money("-50.00"))  # "($50.00)"
    """
    formatted = format_money(abs(amount), places=places)
    if amount.amount < 0:
        return f"({formatted})"
    return formatted
