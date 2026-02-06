"""
Plaid Banking Integration

Provides Plaid API client for:
- Link token creation (initiating bank connections)
- Public token exchange (completing connections)
- Account data retrieval (balances, metadata)
- Transaction history (with pagination)

Source: Adapted from trader-ai/src/finances/plaid_client.py

Usage:
    from library.components.banking.plaid import PlaidClient

    client = PlaidClient(environment="sandbox")
    link_token = client.create_link_token("user-123")
    # User completes Plaid Link flow...
    access_token = client.exchange_public_token(public_token)
    accounts = client.get_accounts(access_token)
"""

from .client import PlaidClient, PlaidError

__all__ = ['PlaidClient', 'PlaidError']
