# Transaction Store Component

Double-entry bookkeeping transaction storage for financial applications.

## Features

- Double-entry bookkeeping pattern
- Decimal-only monetary values (no floats)
- Transaction atomicity
- Account balance tracking
- Transaction history queries

## Usage

```python
from decimal import Decimal
from store import TransactionStore, Transaction, Account

# Initialize store
store = TransactionStore()

# Create accounts
checking = store.create_account("checking", "Checking Account")
savings = store.create_account("savings", "Savings Account")

# Record a transfer (double-entry)
transaction = store.record_transfer(
    from_account="checking",
    to_account="savings",
    amount=Decimal("500.00"),
    description="Monthly savings"
)

# Query balances
checking_balance = store.get_balance("checking")
savings_balance = store.get_balance("savings")

# Query history
history = store.get_transactions(
    account="checking",
    start_date=datetime(2026, 1, 1),
    end_date=datetime(2026, 1, 31)
)
```

## Double-Entry Guarantee

Every transaction creates two entries:
- Debit entry (money leaving an account)
- Credit entry (money entering an account)

The sum of all debits always equals the sum of all credits.

## Important

NEVER use float for monetary values. Always use Decimal:

```python
# CORRECT
amount = Decimal("100.50")

# WRONG - will raise FloatNotAllowedError
amount = 100.50
```
