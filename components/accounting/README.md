# Accounting Domain

Components for financial bookkeeping and transaction management.

## Components

| Component | Description |
|-----------|-------------|
| `transactions/` | Transaction storage and retrieval |
| `categorizer/` | Automatic transaction categorization |

## Usage

```python
# Transaction management
from library.components.accounting.transactions import (
    TransactionStore,
    Transaction,
    TransactionType,
)

# Categorization
from library.components.accounting.categorizer import (
    TransactionCategorizer,
    Category,
    CategoryRule,
)
```

## Related Domains

- `banking/` - Banking integrations (Plaid, Mercury)
- `payments/` - Payment processing (Stripe)
