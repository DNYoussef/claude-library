# Mercury Bank Integration Component

Async Mercury banking API client for startup banking operations.

## Features

- Account balance and info
- Transaction history with filtering
- ACH and internal transfers
- Recipient management
- **Decimal-only money handling (NO floats)**

## Installation

```bash
pip install httpx
```

## Usage

### Basic Operations

```python
from library.components.banking.mercury import MercuryClient, MercuryConfig
from library.common.types import Money
from decimal import Decimal
from datetime import date

# Using context manager (auto-closes connection)
async with MercuryClient(MercuryConfig()) as client:
    # Get all accounts
    accounts = await client.get_accounts()

    for acc in accounts:
        print(f"{acc.name}: {acc.balance.amount} {acc.balance.currency}")

    # Get transactions from this year
    transactions = await client.get_transactions(
        account_id=accounts[0].id,
        start_date=date(2024, 1, 1),
        limit=50
    )
```

### ACH Transfers

```python
# IMPORTANT: Always use Decimal, never float
amount = Money(Decimal("500.00"), "USD")

# Create transfer with idempotency key
transfer = await client.create_ach_transfer(
    account_id="acc_abc123",
    recipient_id="rec_xyz789",
    amount=amount,
    idempotency_key="payroll-jan-2024-001",  # Prevents duplicates
    note="January payroll"
)

print(f"Transfer status: {transfer.status}")
```

### Internal Transfers

```python
# Transfer between your Mercury accounts
await client.create_internal_transfer(
    from_account_id="acc_checking",
    to_account_id="acc_savings",
    amount=Money(Decimal("1000.00"), "USD"),
    idempotency_key="savings-transfer-001"
)
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_key` | `MERCURY_API_KEY` env | Mercury API key |
| `base_url` | `https://api.mercury.com/api/v1` | API base URL |
| `timeout` | `30` | Request timeout (seconds) |

## CRITICAL: Money Handling

**NEVER use floats for money:**

```python
# CORRECT
amount = Money(Decimal("100.50"), "USD")

# WRONG - Raises TypeError
amount = Money(100.50, "USD")
```

## Sources

- [Mercury API Docs](https://docs.mercury.com/reference)
- [trix-solutions/mercury](https://github.com/trix-solutions/mercury)
- [Oxiin/mercury-api](https://github.com/Oxiin/mercury-api)
