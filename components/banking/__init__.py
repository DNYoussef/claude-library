"""
Banking Integration Components

Provides abstractions for integrating with banking APIs and databases.

Components:
- plaid: Plaid API client for bank account linking and transactions
- models: Common data models for banking data
- database: Database layer for storing banking data
"""

from .models import BankAccount, Transaction, BankConnection

__all__ = [
    'BankAccount',
    'Transaction',
    'BankConnection',
]
