"""
Banking Data Models - Common structures for banking integrations.

These models are provider-agnostic and can be used with Plaid, Mercury, or other APIs.

Source: Adapted from trader-ai/src/finances/plaid_client.py
Enhanced: Added validation for required fields and currency codes (2026-01-10)
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Set
from decimal import Decimal
from enum import Enum


# ISO 4217 currency codes (common subset)
VALID_CURRENCY_CODES: Set[str] = {
    'USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF', 'CNY', 'INR', 'MXN',
    'BRL', 'KRW', 'SGD', 'HKD', 'NOK', 'SEK', 'DKK', 'NZD', 'ZAR', 'RUB',
    'TRY', 'PLN', 'THB', 'MYR', 'IDR', 'PHP', 'CZK', 'ILS', 'CLP', 'AED',
}


class AccountType(str, Enum):
    """Bank account types."""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    LOAN = "loan"
    INVESTMENT = "investment"
    OTHER = "other"


class TransactionType(str, Enum):
    """Transaction types."""
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    FEE = "fee"
    INTEREST = "interest"
    OTHER = "other"


@dataclass
class BankAccount:
    """
    Bank account data structure.

    Represents a linked bank account with current balance information.
    Uses Decimal for all monetary values (NEVER float!).
    """
    account_id: str
    name: str
    type: AccountType
    subtype: Optional[str] = None
    mask: Optional[str] = None  # Last 4 digits
    official_name: Optional[str] = None
    current_balance: Decimal = Decimal("0")
    available_balance: Optional[Decimal] = None
    currency_code: str = "USD"
    institution_name: Optional[str] = None
    last_synced: Optional[datetime] = None

    def __post_init__(self):
        """Validate and normalize values."""
        # Validate required fields
        if not self.account_id or not str(self.account_id).strip():
            raise ValueError("account_id cannot be empty")
        if not self.name or not str(self.name).strip():
            raise ValueError("name cannot be empty")

        # Ensure balances are Decimal (reject float)
        if isinstance(self.current_balance, float):
            raise TypeError("current_balance must be Decimal, not float")
        if isinstance(self.available_balance, float):
            raise TypeError("available_balance must be Decimal, not float")

        # Normalize type if string
        if isinstance(self.type, str):
            self.type = AccountType(self.type.lower())

        # Validate currency code (ISO 4217)
        currency_upper = self.currency_code.upper()
        if currency_upper not in VALID_CURRENCY_CODES:
            raise ValueError(
                f"Invalid currency code: {self.currency_code}. "
                f"Must be ISO 4217 (e.g., USD, EUR, GBP)"
            )
        object.__setattr__(self, 'currency_code', currency_upper)

    @classmethod
    def from_plaid(cls, data: dict) -> "BankAccount":
        """
        Create from Plaid API response.

        Args:
            data: Plaid account object from API response

        Returns:
            BankAccount instance

        Raises:
            ValueError: If required fields are missing
        """
        # Defensive extraction with safe defaults
        balances = data.get('balances', {})

        # Get account_id with fallback to item_id
        account_id = data.get('account_id') or data.get('item_id')
        if not account_id:
            raise ValueError("Plaid response missing account_id")

        # Get name with fallback to official_name
        name = data.get('name') or data.get('official_name') or 'Unknown Account'

        # Get account type with safe fallback
        raw_type = data.get('type', 'other')
        try:
            account_type = AccountType(str(raw_type).lower())
        except ValueError:
            account_type = AccountType.OTHER

        # Get currency with safe default
        currency = balances.get('iso_currency_code') or balances.get('unofficial_currency_code') or 'USD'

        return cls(
            account_id=account_id,
            name=name,
            type=account_type,
            subtype=data.get('subtype'),
            mask=data.get('mask'),
            official_name=data.get('official_name'),
            current_balance=Decimal(str(balances.get('current', 0) or 0)),
            available_balance=Decimal(str(balances['available'])) if balances.get('available') else None,
            currency_code=currency,
        )


@dataclass
class Transaction:
    """
    Bank transaction data structure.

    Represents a single transaction with categorization.
    Uses Decimal for amounts (NEVER float!).
    """
    transaction_id: str
    account_id: str
    amount: Decimal  # Positive = money out, Negative = money in (Plaid convention)
    date: date
    name: str
    merchant_name: Optional[str] = None
    category: List[str] = field(default_factory=list)
    pending: bool = False
    transaction_type: TransactionType = TransactionType.OTHER
    currency_code: str = "USD"
    location: Optional[dict] = None
    payment_channel: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize values."""
        # Validate required fields
        if not self.transaction_id or not str(self.transaction_id).strip():
            raise ValueError("transaction_id cannot be empty")
        if not self.account_id or not str(self.account_id).strip():
            raise ValueError("account_id cannot be empty")
        if not self.name or not str(self.name).strip():
            raise ValueError("name cannot be empty")

        # Reject float for amount
        if isinstance(self.amount, float):
            raise TypeError("amount must be Decimal, not float")

        # Parse date string if needed
        if isinstance(self.date, str):
            self.date = datetime.strptime(self.date, '%Y-%m-%d').date()

        # Validate currency code
        currency_upper = self.currency_code.upper()
        if currency_upper not in VALID_CURRENCY_CODES:
            raise ValueError(f"Invalid currency code: {self.currency_code}")
        object.__setattr__(self, 'currency_code', currency_upper)

    @classmethod
    def from_plaid(cls, data: dict) -> "Transaction":
        """
        Create from Plaid API response.

        Args:
            data: Plaid transaction object from API response

        Returns:
            Transaction instance

        Raises:
            ValueError: If required fields are missing
        """
        # Defensive extraction with validation
        transaction_id = data.get('transaction_id')
        if not transaction_id:
            raise ValueError("Plaid response missing transaction_id")

        account_id = data.get('account_id')
        if not account_id:
            raise ValueError("Plaid response missing account_id")

        # Get amount with safe conversion
        raw_amount = data.get('amount', 0)
        amount = Decimal(str(raw_amount)) if raw_amount is not None else Decimal('0')

        # Parse date safely
        raw_date = data.get('date')
        if not raw_date:
            txn_date = date.today()
        elif isinstance(raw_date, date):
            txn_date = raw_date
        else:
            txn_date = datetime.strptime(str(raw_date), '%Y-%m-%d').date()

        # Get name with fallback
        name = data.get('name') or data.get('merchant_name') or 'Unknown Transaction'

        return cls(
            transaction_id=transaction_id,
            account_id=account_id,
            amount=amount,
            date=txn_date,
            name=name,
            merchant_name=data.get('merchant_name'),
            category=data.get('category') or [],
            pending=bool(data.get('pending', False)),
            payment_channel=data.get('payment_channel'),
        )

    @property
    def is_expense(self) -> bool:
        """True if this is an expense (money out)."""
        return self.amount > 0  # Plaid convention: positive = outflow

    @property
    def is_income(self) -> bool:
        """True if this is income (money in)."""
        return self.amount < 0  # Plaid convention: negative = inflow


@dataclass
class BankConnection:
    """
    Represents a connection to a bank/institution.

    Contains metadata about the link and access credentials.
    """
    connection_id: str
    access_token: str  # Store securely!
    institution_name: str
    institution_id: Optional[str] = None
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def needs_reauth(self) -> bool:
        """True if user needs to re-authenticate."""
        return self.error_code in ['ITEM_LOGIN_REQUIRED', 'PENDING_EXPIRATION']
