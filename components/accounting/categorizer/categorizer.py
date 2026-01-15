"""
Transaction Categorizer Component

ML-based transaction categorization using scikit-learn.
Based on open-source banking classification patterns.

References:
- https://github.com/eli-goodfriend/banking-class
- https://github.com/j-convey/BankTextCategorizer
- https://medium.com/nerd-for-tech/how-to-build-a-machine-learning-service-for-classifying-financial-transactions

Installation:
    pip install scikit-learn
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import re
import pickle
from pathlib import Path


class TransactionCategory(Enum):
    """Standard transaction categories (Plaid-compatible)."""
    # Income
    INCOME_SALARY = "income_salary"
    INCOME_FREELANCE = "income_freelance"
    INCOME_INTEREST = "income_interest"
    INCOME_REFUND = "income_refund"
    INCOME_OTHER = "income_other"

    # Expenses
    FOOD_GROCERIES = "food_groceries"
    FOOD_RESTAURANTS = "food_restaurants"
    FOOD_COFFEE = "food_coffee"

    TRANSPORTATION_GAS = "transportation_gas"
    TRANSPORTATION_PARKING = "transportation_parking"
    TRANSPORTATION_RIDESHARE = "transportation_rideshare"
    TRANSPORTATION_PUBLIC = "transportation_public"

    UTILITIES_ELECTRIC = "utilities_electric"
    UTILITIES_WATER = "utilities_water"
    UTILITIES_GAS = "utilities_gas"
    UTILITIES_INTERNET = "utilities_internet"
    UTILITIES_PHONE = "utilities_phone"

    HOUSING_RENT = "housing_rent"
    HOUSING_MORTGAGE = "housing_mortgage"
    HOUSING_INSURANCE = "housing_insurance"

    SHOPPING_ONLINE = "shopping_online"
    SHOPPING_RETAIL = "shopping_retail"
    SHOPPING_ELECTRONICS = "shopping_electronics"

    ENTERTAINMENT_STREAMING = "entertainment_streaming"
    ENTERTAINMENT_GAMES = "entertainment_games"
    ENTERTAINMENT_EVENTS = "entertainment_events"

    HEALTH_MEDICAL = "health_medical"
    HEALTH_PHARMACY = "health_pharmacy"
    HEALTH_FITNESS = "health_fitness"

    PERSONAL_CARE = "personal_care"
    TRAVEL = "travel"
    EDUCATION = "education"
    CHARITY = "charity"
    FEES_BANK = "fees_bank"
    TRANSFER = "transfer"
    ATM = "atm"
    OTHER = "other"


@dataclass
class CategoryResult:
    """Categorization result."""
    category: TransactionCategory
    confidence: float
    secondary_category: Optional[TransactionCategory] = None
    secondary_confidence: Optional[float] = None


@dataclass
class CategorizerConfig:
    """Categorizer configuration."""
    min_confidence: float = 0.5
    use_rules_first: bool = True
    model_path: Optional[str] = None


# Keyword-based rules for common merchants
MERCHANT_RULES: Dict[str, TransactionCategory] = {
    # Groceries
    "walmart": TransactionCategory.FOOD_GROCERIES,
    "target": TransactionCategory.FOOD_GROCERIES,
    "costco": TransactionCategory.FOOD_GROCERIES,
    "safeway": TransactionCategory.FOOD_GROCERIES,
    "whole foods": TransactionCategory.FOOD_GROCERIES,
    "trader joe": TransactionCategory.FOOD_GROCERIES,
    "kroger": TransactionCategory.FOOD_GROCERIES,

    # Restaurants
    "mcdonald": TransactionCategory.FOOD_RESTAURANTS,
    "starbucks": TransactionCategory.FOOD_COFFEE,
    "dunkin": TransactionCategory.FOOD_COFFEE,
    "chipotle": TransactionCategory.FOOD_RESTAURANTS,
    "doordash": TransactionCategory.FOOD_RESTAURANTS,
    "uber eats": TransactionCategory.FOOD_RESTAURANTS,
    "grubhub": TransactionCategory.FOOD_RESTAURANTS,

    # Transportation
    "shell": TransactionCategory.TRANSPORTATION_GAS,
    "chevron": TransactionCategory.TRANSPORTATION_GAS,
    "exxon": TransactionCategory.TRANSPORTATION_GAS,
    "uber": TransactionCategory.TRANSPORTATION_RIDESHARE,
    "lyft": TransactionCategory.TRANSPORTATION_RIDESHARE,

    # Streaming
    "netflix": TransactionCategory.ENTERTAINMENT_STREAMING,
    "spotify": TransactionCategory.ENTERTAINMENT_STREAMING,
    "hulu": TransactionCategory.ENTERTAINMENT_STREAMING,
    "disney+": TransactionCategory.ENTERTAINMENT_STREAMING,
    "apple music": TransactionCategory.ENTERTAINMENT_STREAMING,
    "amazon prime": TransactionCategory.ENTERTAINMENT_STREAMING,

    # Utilities
    "comcast": TransactionCategory.UTILITIES_INTERNET,
    "verizon": TransactionCategory.UTILITIES_PHONE,
    "at&t": TransactionCategory.UTILITIES_PHONE,
    "t-mobile": TransactionCategory.UTILITIES_PHONE,

    # Shopping
    "amazon": TransactionCategory.SHOPPING_ONLINE,
    "ebay": TransactionCategory.SHOPPING_ONLINE,
    "best buy": TransactionCategory.SHOPPING_ELECTRONICS,
    "apple store": TransactionCategory.SHOPPING_ELECTRONICS,

    # Transfer/ATM
    "venmo": TransactionCategory.TRANSFER,
    "zelle": TransactionCategory.TRANSFER,
    "paypal": TransactionCategory.TRANSFER,
    "atm": TransactionCategory.ATM,
    "cash": TransactionCategory.ATM,

    # Fees
    "fee": TransactionCategory.FEES_BANK,
    "overdraft": TransactionCategory.FEES_BANK,
}


class TransactionCategorizer:
    """
    ML-based transaction categorizer.

    Uses a combination of:
    1. Rule-based matching for known merchants
    2. ML classification for unknown transactions

    Example:
        categorizer = TransactionCategorizer()

        result = categorizer.categorize("STARBUCKS #1234")
        print(f"{result.category}: {result.confidence:.2%}")

        # Batch categorization
        transactions = ["AMAZON.COM", "SHELL GAS", "UNKNOWN MERCHANT"]
        results = categorizer.categorize_batch(transactions)
    """

    def __init__(self, config: Optional[CategorizerConfig] = None):
        self.config = config or CategorizerConfig()
        self._model = None
        self._vectorizer = None

        if self.config.model_path:
            self._load_model(self.config.model_path)

    def _load_model(self, path: str):
        """Load a trained model from disk."""
        model_path = Path(path)
        if model_path.exists():
            with open(model_path, "rb") as f:
                data = pickle.load(f)
                self._model = data.get("model")
                self._vectorizer = data.get("vectorizer")

    def save_model(self, path: str):
        """Save the trained model to disk."""
        with open(path, "wb") as f:
            pickle.dump({
                "model": self._model,
                "vectorizer": self._vectorizer,
            }, f)

    def _preprocess(self, description: str) -> str:
        """Preprocess transaction description."""
        # Lowercase
        text = description.lower()

        # Remove special characters but keep spaces
        text = re.sub(r"[^a-z0-9\s]", " ", text)

        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove common noise words
        noise = ["pos", "debit", "credit", "card", "purchase", "payment", "#"]
        for word in noise:
            text = text.replace(word, "")

        return text.strip()

    def _rule_based_categorize(self, description: str) -> Optional[CategoryResult]:
        """Try to categorize using rule-based matching."""
        text = description.lower()

        for keyword, category in MERCHANT_RULES.items():
            if keyword in text:
                return CategoryResult(
                    category=category,
                    confidence=0.95,
                )

        return None

    def _ml_categorize(self, description: str) -> CategoryResult:
        """Categorize using ML model."""
        if self._model is None or self._vectorizer is None:
            # No model loaded, return OTHER with low confidence
            return CategoryResult(
                category=TransactionCategory.OTHER,
                confidence=0.3,
            )

        # Preprocess and vectorize
        text = self._preprocess(description)
        features = self._vectorizer.transform([text])

        # Get prediction probabilities
        proba = self._model.predict_proba(features)[0]
        classes = self._model.classes_

        # Get top 2 predictions
        top_indices = proba.argsort()[-2:][::-1]

        primary_idx = top_indices[0]
        primary_category = TransactionCategory(classes[primary_idx])
        primary_confidence = float(proba[primary_idx])

        result = CategoryResult(
            category=primary_category,
            confidence=primary_confidence,
        )

        if len(top_indices) > 1:
            secondary_idx = top_indices[1]
            result.secondary_category = TransactionCategory(classes[secondary_idx])
            result.secondary_confidence = float(proba[secondary_idx])

        return result

    def categorize(self, description: str) -> CategoryResult:
        """
        Categorize a single transaction.

        Args:
            description: Transaction description/memo

        Returns:
            CategoryResult with category and confidence
        """
        # Try rule-based first if enabled
        if self.config.use_rules_first:
            result = self._rule_based_categorize(description)
            if result:
                return result

        # Fall back to ML
        return self._ml_categorize(description)

    def categorize_batch(
        self,
        descriptions: List[str],
    ) -> List[CategoryResult]:
        """
        Categorize multiple transactions.

        Args:
            descriptions: List of transaction descriptions

        Returns:
            List of CategoryResult objects
        """
        return [self.categorize(desc) for desc in descriptions]

    def train(
        self,
        descriptions: List[str],
        categories: List[TransactionCategory],
    ):
        """
        Train the ML model on labeled data.

        Args:
            descriptions: Transaction descriptions
            categories: Corresponding categories
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.ensemble import RandomForestClassifier
        except ImportError:
            raise ImportError(
                "scikit-learn required. Install with: pip install scikit-learn"
            )

        # Preprocess descriptions
        processed = [self._preprocess(d) for d in descriptions]
        labels = [c.value for c in categories]

        # Create vectorizer and model
        self._vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=2,
        )

        self._model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
        )

        # Fit
        features = self._vectorizer.fit_transform(processed)
        self._model.fit(features, labels)

    def add_rule(self, keyword: str, category: TransactionCategory):
        """Add a custom categorization rule."""
        MERCHANT_RULES[keyword.lower()] = category

    def get_categories(self) -> List[TransactionCategory]:
        """Get all available categories."""
        return list(TransactionCategory)
