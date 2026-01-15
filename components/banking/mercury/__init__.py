"""
Mercury Bank Integration Component

Async Mercury banking API client for:
- Account management
- Transaction history
- ACH/Wire transfers
- Recipient management

Based on Mercury's official API.

References:
- https://docs.mercury.com/reference
- https://github.com/trix-solutions/mercury

Installation:
    pip install httpx

Example:
    from library.components.banking.mercury import MercuryClient, MercuryConfig
    from library.common.types import Money
    from decimal import Decimal

    async with MercuryClient(MercuryConfig()) as client:
        accounts = await client.get_accounts()
        print(f"Balance: {accounts[0].balance}")

        # Transfer funds
        await client.create_ach_transfer(
            account_id=accounts[0].id,
            recipient_id="rec_...",
            amount=Money(Decimal("100.00"), "USD"),
            idempotency_key="transfer-123"
        )
"""

from .client import (
    MercuryClient,
    MercuryConfig,
    MercuryAccount,
    MercuryTransaction,
    MercuryRecipient,
    AccountType,
    TransactionStatus,
    TransactionType,
)

__all__ = [
    "MercuryClient",
    "MercuryConfig",
    "MercuryAccount",
    "MercuryTransaction",
    "MercuryRecipient",
    "AccountType",
    "TransactionStatus",
    "TransactionType",
]
