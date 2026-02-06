# Banking Domain

Components for banking integrations and financial data access.

## Components

| Component | Description |
|-----------|-------------|
| `plaid/` | Plaid API integration for account aggregation |
| `mercury/` | Mercury bank API integration |

## Usage

```python
# Plaid integration
from library.components.banking.plaid import (
    PlaidClient,
    PlaidConfig,
    AccountBalance,
    Transaction,
)

# Mercury integration
from library.components.banking.mercury import (
    MercuryClient,
    MercuryConfig,
    Account,
    Transfer,
)
```

## Related Domains

- `accounting/` - Transaction categorization and bookkeeping
- `payments/` - Payment processing (Stripe)
