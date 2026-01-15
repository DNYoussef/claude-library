"""
Mercury Bank API Client

Production-ready async Mercury banking integration.
Based on Mercury's official API documentation.

References:
- https://docs.mercury.com/reference
- https://github.com/trix-solutions/mercury
- https://github.com/Oxiin/mercury-api

IMPORTANT: Uses Decimal for all monetary values - NO floats allowed.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, date
import os

try:
    import httpx
except ImportError:
    httpx = None

# Import shared types with multi-path fallback (LEGO pattern)
_money_imported = False

try:
    from library.common.types import Money, FloatNotAllowedError
    _money_imported = True
except ImportError:
    pass

if not _money_imported:
    try:
        from common.types import Money, FloatNotAllowedError
        _money_imported = True
    except ImportError:
        pass

if not _money_imported:
    # Fallback for standalone usage (copy-paste scenarios)
    class FloatNotAllowedError(TypeError):
        """Raised when float is used instead of Decimal for money."""
        pass

    @dataclass(frozen=True)
    class Money:
        """Minimal Money implementation for standalone use."""
        amount: Decimal
        currency: str = "USD"

        def __post_init__(self):
            if isinstance(self.amount, float):
                raise FloatNotAllowedError("Use Decimal, not float for money")


class AccountType(Enum):
    """Mercury account types."""
    CHECKING = "checking"
    SAVINGS = "savings"


class TransactionStatus(Enum):
    """Mercury transaction statuses."""
    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TransactionType(Enum):
    """Mercury transaction types."""
    CREDIT = "credit"
    DEBIT = "debit"
    ACH = "ach"
    WIRE = "wire"
    CHECK = "check"
    INTERNAL = "internal"


@dataclass
class MercuryConfig:
    """Mercury API configuration."""
    api_key: str = field(default_factory=lambda: os.environ.get("MERCURY_API_KEY", ""))
    base_url: str = "https://api.mercury.com/api/v1"
    timeout: int = 30

    def __post_init__(self):
        if not self.api_key:
            raise ValueError("MERCURY_API_KEY required")


@dataclass
class MercuryAccount:
    """Mercury bank account."""
    id: str
    name: str
    account_number: str
    routing_number: str
    account_type: AccountType
    balance: Money
    available_balance: Money
    created_at: Optional[datetime] = None


@dataclass
class MercuryTransaction:
    """Mercury transaction."""
    id: str
    amount: Money
    status: TransactionStatus
    transaction_type: TransactionType
    counterparty_name: Optional[str] = None
    counterparty_id: Optional[str] = None
    description: Optional[str] = None
    posted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    external_memo: Optional[str] = None


@dataclass
class MercuryRecipient:
    """Mercury payment recipient."""
    id: str
    name: str
    email: Optional[str] = None
    account_number: Optional[str] = None
    routing_number: Optional[str] = None


class MercuryClient:
    """
    Async Mercury Bank API client.

    Provides access to:
    - Account information and balances
    - Transaction history
    - ACH transfers
    - Recipients management

    Example:
        client = MercuryClient(MercuryConfig(api_key="..."))

        # Get accounts
        accounts = await client.get_accounts()

        # Get transactions
        transactions = await client.get_transactions(
            account_id=accounts[0].id,
            start_date=date(2024, 1, 1)
        )

        # Initiate ACH transfer
        transfer = await client.create_ach_transfer(
            account_id="acc_...",
            recipient_id="rec_...",
            amount=Money(Decimal("100.00"), "USD"),
            idempotency_key="unique-key-123"
        )
    """

    def __init__(self, config: Optional[MercuryConfig] = None):
        self.config = config or MercuryConfig()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> "httpx.AsyncClient":
        """Get or create HTTP client."""
        if httpx is None:
            raise ImportError("httpx required. Install with: pip install httpx")

        if self._client is not None:
            return self._client
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
        )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    def _parse_money(self, amount: Any, currency: str = "USD") -> Money:
        """Parse API amount to Money (converts to Decimal)."""
        if isinstance(amount, float):
            # API returns floats, convert safely
            amount = Decimal(str(amount))
        elif isinstance(amount, (int, str)):
            amount = Decimal(amount)
        return Money(amount, currency)

    def _money_to_cents(self, money: Money) -> int:
        """Convert Money to cents for API."""
        return int(money.amount * 100)

    # Account Operations

    async def get_accounts(self) -> List[MercuryAccount]:
        """Get all accounts."""
        client = await self._get_client()
        response = await client.get("/accounts")
        response.raise_for_status()

        accounts = []
        for acc in response.json().get("accounts", []):
            accounts.append(MercuryAccount(
                id=acc["id"],
                name=acc["name"],
                account_number=acc["accountNumber"],
                routing_number=acc["routingNumber"],
                account_type=AccountType(acc["type"]),
                balance=self._parse_money(acc["currentBalance"]),
                available_balance=self._parse_money(acc["availableBalance"]),
                created_at=datetime.fromisoformat(acc["createdAt"].replace("Z", "+00:00")) if acc.get("createdAt") else None,
            ))
        return accounts

    async def get_account(self, account_id: str) -> MercuryAccount:
        """Get a specific account by ID."""
        client = await self._get_client()
        response = await client.get(f"/account/{account_id}")
        response.raise_for_status()

        acc = response.json()
        return MercuryAccount(
            id=acc["id"],
            name=acc["name"],
            account_number=acc["accountNumber"],
            routing_number=acc["routingNumber"],
            account_type=AccountType(acc["type"]),
            balance=self._parse_money(acc["currentBalance"]),
            available_balance=self._parse_money(acc["availableBalance"]),
            created_at=datetime.fromisoformat(acc["createdAt"].replace("Z", "+00:00")) if acc.get("createdAt") else None,
        )

    # Transaction Operations

    async def get_transactions(
        self,
        account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MercuryTransaction]:
        """
        Get transactions for an account.

        Args:
            account_id: Account ID
            start_date: Filter start date
            end_date: Filter end date
            limit: Max results (default 100)
            offset: Pagination offset
        """
        client = await self._get_client()

        params = {"limit": limit, "offset": offset}
        if start_date:
            params["start"] = start_date.isoformat()
        if end_date:
            params["end"] = end_date.isoformat()

        response = await client.get(
            f"/account/{account_id}/transactions",
            params=params,
        )
        response.raise_for_status()

        transactions = []
        for txn in response.json().get("transactions", []):
            transactions.append(self._parse_transaction(txn))
        return transactions

    async def get_transaction(
        self,
        account_id: str,
        transaction_id: str,
    ) -> MercuryTransaction:
        """Get a specific transaction."""
        client = await self._get_client()
        response = await client.get(
            f"/account/{account_id}/transaction/{transaction_id}"
        )
        response.raise_for_status()
        return self._parse_transaction(response.json())

    def _parse_transaction(self, txn: Dict[str, Any]) -> MercuryTransaction:
        """Parse transaction from API response."""
        return MercuryTransaction(
            id=txn["id"],
            amount=self._parse_money(txn["amount"]),
            status=TransactionStatus(txn["status"]),
            transaction_type=TransactionType(txn.get("kind", "credit")),
            counterparty_name=txn.get("counterpartyName"),
            counterparty_id=txn.get("counterpartyId"),
            description=txn.get("bankDescription"),
            posted_at=datetime.fromisoformat(txn["postedAt"].replace("Z", "+00:00")) if txn.get("postedAt") else None,
            created_at=datetime.fromisoformat(txn["createdAt"].replace("Z", "+00:00")) if txn.get("createdAt") else None,
            external_memo=txn.get("externalMemo"),
        )

    # Recipient Operations

    async def get_recipients(self) -> List[MercuryRecipient]:
        """Get all payment recipients."""
        client = await self._get_client()
        response = await client.get("/recipients")
        response.raise_for_status()

        recipients = []
        for rec in response.json().get("recipients", []):
            recipients.append(MercuryRecipient(
                id=rec["id"],
                name=rec["name"],
                email=rec.get("emails", [None])[0] if rec.get("emails") else None,
                account_number=rec.get("electronicRoutingInfo", {}).get("accountNumber"),
                routing_number=rec.get("electronicRoutingInfo", {}).get("routingNumber"),
            ))
        return recipients

    # Transfer Operations

    async def create_ach_transfer(
        self,
        account_id: str,
        recipient_id: str,
        amount: Money,
        idempotency_key: str,
        note: Optional[str] = None,
    ) -> MercuryTransaction:
        """
        Create an ACH transfer.

        Args:
            account_id: Source account ID
            recipient_id: Recipient ID
            amount: Transfer amount (Decimal only!)
            idempotency_key: Unique key to prevent duplicates
            note: Optional memo

        Returns:
            Created transaction
        """
        if isinstance(amount.amount, float):
            raise TypeError("Amount must use Decimal, not float")

        client = await self._get_client()

        payload = {
            "recipientId": recipient_id,
            "amount": float(amount.amount),  # API expects float
            "paymentMethod": "ach",
            "idempotencyKey": idempotency_key,
        }
        if note:
            payload["note"] = note

        response = await client.post(
            f"/account/{account_id}/transactions",
            json=payload,
        )
        response.raise_for_status()
        return self._parse_transaction(response.json())

    async def create_internal_transfer(
        self,
        from_account_id: str,
        to_account_id: str,
        amount: Money,
        idempotency_key: str,
    ) -> MercuryTransaction:
        """
        Transfer between Mercury accounts.

        Args:
            from_account_id: Source account ID
            to_account_id: Destination account ID
            amount: Transfer amount (Decimal only!)
            idempotency_key: Unique key to prevent duplicates
        """
        if isinstance(amount.amount, float):
            raise TypeError("Amount must use Decimal, not float")

        client = await self._get_client()

        payload = {
            "toAccountId": to_account_id,
            "amount": float(amount.amount),
            "idempotencyKey": idempotency_key,
        }

        response = await client.post(
            f"/account/{from_account_id}/transactions",
            json=payload,
        )
        response.raise_for_status()
        return self._parse_transaction(response.json())
