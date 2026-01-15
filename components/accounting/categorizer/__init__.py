"""
Transaction Categorizer Component

ML-based transaction categorization for financial applications.

Features:
- Rule-based matching for known merchants
- ML classification with scikit-learn
- Plaid-compatible categories
- Trainable on custom data

References:
- https://github.com/eli-goodfriend/banking-class
- https://github.com/j-convey/BankTextCategorizer

Installation:
    pip install scikit-learn

Example:
    from library.components.accounting.categorizer import (
        TransactionCategorizer,
        TransactionCategory,
    )

    categorizer = TransactionCategorizer()

    result = categorizer.categorize("STARBUCKS STORE #1234")
    print(f"{result.category}: {result.confidence:.0%}")
    # TransactionCategory.FOOD_COFFEE: 95%
"""

from .categorizer import (
    TransactionCategorizer,
    TransactionCategory,
    CategoryResult,
    CategorizerConfig,
)

__all__ = [
    "TransactionCategorizer",
    "TransactionCategory",
    "CategoryResult",
    "CategorizerConfig",
]
