# Transaction Categorizer Component

ML-based transaction categorization for financial applications.

## Features

- Rule-based matching for 50+ known merchants
- ML classification for unknown transactions
- 40+ Plaid-compatible categories
- Trainable on custom data
- Confidence scoring

## Installation

```bash
pip install scikit-learn
```

## Usage

### Basic Categorization

```python
from library.components.accounting.categorizer import (
    TransactionCategorizer,
    TransactionCategory,
)

categorizer = TransactionCategorizer()

# Single transaction
result = categorizer.categorize("STARBUCKS STORE #1234")
print(f"{result.category.value}: {result.confidence:.0%}")
# food_coffee: 95%

# Batch categorization
transactions = [
    "AMAZON.COM*1A2B3C4D",
    "SHELL OIL 12345",
    "NETFLIX.COM",
    "ACH DEPOSIT PAYROLL",
]

results = categorizer.categorize_batch(transactions)
for desc, result in zip(transactions, results):
    print(f"{desc}: {result.category.value}")
```

### Training Custom Model

```python
# Prepare labeled training data
descriptions = [
    "WHOLE FOODS MARKET",
    "CHEVRON GAS STATION",
    "MONTHLY RENT PAYMENT",
    # ... more examples
]

categories = [
    TransactionCategory.FOOD_GROCERIES,
    TransactionCategory.TRANSPORTATION_GAS,
    TransactionCategory.HOUSING_RENT,
    # ... matching categories
]

# Train
categorizer.train(descriptions, categories)

# Save model
categorizer.save_model("categorizer_model.pkl")

# Load later
config = CategorizerConfig(model_path="categorizer_model.pkl")
categorizer = TransactionCategorizer(config)
```

### Custom Rules

```python
# Add custom merchant rules
categorizer.add_rule("local coffee shop", TransactionCategory.FOOD_COFFEE)
categorizer.add_rule("gym membership", TransactionCategory.HEALTH_FITNESS)
```

## Categories

| Category | Description |
|----------|-------------|
| **Income** | |
| `income_salary` | Regular payroll deposits |
| `income_freelance` | Freelance/contractor income |
| `income_interest` | Bank interest |
| `income_refund` | Refunds |
| **Food** | |
| `food_groceries` | Grocery stores |
| `food_restaurants` | Restaurants, delivery |
| `food_coffee` | Coffee shops |
| **Transportation** | |
| `transportation_gas` | Gas stations |
| `transportation_rideshare` | Uber, Lyft |
| `transportation_public` | Transit |
| **Utilities** | |
| `utilities_electric` | Electric bills |
| `utilities_internet` | Internet service |
| `utilities_phone` | Phone service |
| **Entertainment** | |
| `entertainment_streaming` | Netflix, Spotify |
| `entertainment_games` | Gaming |
| **And more...** | |

## Configuration

```python
config = CategorizerConfig(
    min_confidence=0.5,      # Minimum confidence threshold
    use_rules_first=True,    # Try rules before ML
    model_path=None,         # Path to saved model
)
```

## Sources

- [banking-class](https://github.com/eli-goodfriend/banking-class) - Parse and categorize banking transactions
- [BankTextCategorizer](https://github.com/j-convey/BankTextCategorizer) - BERT-based categorization
- [Plaid Categories](https://plaid.com/docs/api/products/transactions/#categorization)
