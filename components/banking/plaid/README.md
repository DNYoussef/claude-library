# Plaid Banking Integration

Component for integrating with the Plaid API for bank account linking and transaction data.

## Features

- Link token creation for Plaid Link
- Public token exchange for access tokens
- Account data retrieval with Decimal balances
- Transaction history with pagination
- Proper error handling with PlaidError

## Installation

Requires the plaid-python package:

```bash
pip install plaid-python
```

## Quick Start

```python
from library.components.banking.plaid import PlaidClient

# Initialize client (uses env vars or explicit credentials)
client = PlaidClient(environment="sandbox")

# Create link token for user
link_token = client.create_link_token("user-123")
# Returns: {"link_token": "link-xxx", "expiration": "...", "request_id": "..."}

# After user completes Plaid Link, exchange public token
access_token = client.exchange_public_token(public_token)
# Store access_token securely!

# Get accounts
accounts = client.get_accounts(access_token)
for account in accounts:
    print(f"{account['name']}: ${account['current_balance']}")

# Get transactions
transactions = client.get_transactions(
    access_token,
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PLAID_CLIENT_ID` | Your Plaid client ID |
| `PLAID_SECRET` | Your Plaid secret key |
| `PLAID_ENV` | Environment: sandbox, development, or production |

## Using with Money Pattern

The Plaid client returns Decimal values for all monetary amounts, compatible
with the money-handling pattern:

```python
from library.patterns.money_handling import Money
from library.components.banking.plaid import PlaidClient

client = PlaidClient()
accounts = client.get_accounts(access_token)

for account in accounts:
    balance = Money(account['current_balance'], account['currency_code'])
    print(f"{account['name']}: {balance}")
```

## Error Handling

```python
from library.components.banking.plaid import PlaidClient, PlaidError

try:
    accounts = client.get_accounts(access_token)
except PlaidError as e:
    if e.error_code == 'ITEM_LOGIN_REQUIRED':
        # User needs to re-authenticate
        redirect_to_plaid_link()
    elif e.error_code == 'RATE_LIMIT_EXCEEDED':
        # Retry later
        retry_after_delay()
    else:
        # Log and handle other errors
        logger.error(f"Plaid error: {e.error_code} - {e}")
```

## Source

Adapted from D:\Projects\trader-ai\src\finances\plaid_client.py
