# Money Handling Pattern

**CRITICAL RULE: NEVER use float for currency calculations.**

This pattern provides Decimal-based utilities for all financial operations, preventing the floating-point precision errors that plague financial software.

## Why This Matters

```python
# The problem with float:
>>> 0.1 + 0.2
0.30000000000000004  # NOT 0.3!

>>> 19.99 * 100
1998.9999999999998  # Lost a fraction of a cent!
```

In financial applications, these tiny errors accumulate into real money losses.

## Installation

Copy the `money-handling` directory to your project's `lib/` or add to your Python path.

## Quick Start

```python
from library.patterns.money_handling import Money
from decimal import Decimal

# Create money values (NEVER use float!)
price = Money("19.99")
price = Money(Decimal("19.99"))
price = Money.from_cents(1999)  # Safest - no decimals involved

# Arithmetic
total = price * Decimal("10")  # $199.90
discount = total * Decimal("0.10")  # 10% off
final = total - discount

# THESE WILL RAISE ERRORS (by design!):
# Money(19.99)  # FloatNotAllowedError!
# price * 1.5   # FloatNotAllowedError!
```

## Features

### Strict Float Rejection

Unlike other money libraries that merely warn about floats, this pattern **rejects them entirely**:

```python
Money(19.99)  # Raises FloatNotAllowedError
price * 1.5   # Raises FloatNotAllowedError
```

This is intentional. The moment you allow floats "just this once," precision errors creep in.

### Currency Safety

```python
usd = Money("100", "USD")
eur = Money("100", "EUR")
total = usd + eur  # Raises CurrencyMismatchError
```

### Safe Allocation

Split money without losing cents:

```python
from library.patterns.money_handling import allocate_money

# Split $10 three ways (handles remainder correctly)
shares = allocate_money(Money("10"), [Decimal("1"), Decimal("1"), Decimal("1")])
# Returns: [Money("3.34"), Money("3.33"), Money("3.33")]
# Total: exactly $10.00 - no money lost!
```

### Formatting & Parsing

```python
from library.patterns.money_handling import format_money, parse_money

# Format for display
format_money(Money("1234.56"))  # "$1,234.56"

# Parse user input
parse_money("$1,234.56")  # Money("1234.56", "USD")
```

### Validation

```python
from library.patterns.money_handling import validate_amount

# Validate user input before creating Money
is_valid, error = validate_amount("-50", allow_negative=False)
# (False, "Negative amounts not allowed")
```

## API Reference

### Money Class

| Method | Description |
|--------|-------------|
| `Money(amount, currency="USD")` | Create from Decimal, str, or int (NOT float!) |
| `Money.from_string(value, currency)` | Create from string |
| `Money.from_cents(cents, currency)` | Create from integer cents |
| `Money.zero(currency)` | Create zero value |
| `money.round(places)` | Round to decimal places |
| `money.round_to_cents()` | Round to 2 decimal places |
| `money.to_decimal()` | Get Decimal value |
| `money.to_cents()` | Get integer cents |
| `money.to_float()` | Get float (use sparingly!) |

### Arithmetic Operators

| Operator | Types | Description |
|----------|-------|-------------|
| `+` | Money + Money | Add (same currency) |
| `-` | Money - Money | Subtract (same currency) |
| `*` | Money * int/Decimal | Multiply (NO float!) |
| `/` | Money / int/Decimal | Divide (NO float!) |
| `-money` | unary | Negate |
| `abs(money)` | unary | Absolute value |

### Comparison Operators

All comparison operators work: `==`, `!=`, `<`, `<=`, `>`, `>=`

Note: Comparing different currencies raises `CurrencyMismatchError`.

## Integration Examples

### With SQLAlchemy

```python
from sqlalchemy import Column, Numeric
from decimal import Decimal

class Invoice(Base):
    # Store as Numeric in database
    amount = Column(Numeric(precision=10, scale=2))

    @property
    def total(self) -> Money:
        return Money(self.amount)

    @total.setter
    def total(self, value: Money):
        self.amount = value.to_decimal()
```

### With FastAPI/Pydantic

```python
from pydantic import BaseModel, validator
from decimal import Decimal

class PaymentRequest(BaseModel):
    amount: str  # Accept string, not float!
    currency: str = "USD"

    @validator('amount')
    def validate_amount(cls, v):
        # Ensures valid Decimal format
        try:
            Decimal(v)
        except:
            raise ValueError("Invalid amount format")
        return v

    def to_money(self) -> Money:
        return Money(self.amount, self.currency)
```

### With External APIs (Stripe, etc.)

```python
# When you MUST use float for an external API:
def create_stripe_charge(money: Money):
    stripe.Charge.create(
        amount=money.to_cents(),  # Preferred: cents as integer
        # OR if API requires float:
        amount=money.to_float(),  # Use explicitly
        currency=money.currency.lower()
    )
```

## Running Tests

```bash
cd library/patterns/money-handling
pytest tests/ -v
```

## Migrating from Float

If you have existing code using float:

```python
# Before (WRONG):
price = 19.99
total = price * quantity

# After (CORRECT):
price = Money.from_string("19.99")
total = price * quantity  # quantity must be int or Decimal!
```

## Source

Adapted from `D:\Projects\trader-ai\src\utils\money.py` with enhanced float rejection.

## Related Patterns

- `webhook-idempotency` - Often used together for payment webhooks
- `stripe-integration` - Uses this pattern for all money operations
