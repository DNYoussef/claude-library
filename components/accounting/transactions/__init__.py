"""
Transaction Storage and Querying

Provides a database layer for storing and querying transactions.
Works with any banking provider (Plaid, Mercury, etc.).

Source: Adapted from D:\Projects\trader-ai\src\finances\bank_database.py

Usage:
    from library.components.accounting.transactions import TransactionStore

    store = TransactionStore("data/transactions.db")
    store.add_transaction(transaction)
    recent = store.get_recent_transactions(days=30)
    by_category = store.get_spending_by_category(days=30)
"""

from .store import TransactionStore, TransactionQuery

__all__ = ['TransactionStore', 'TransactionQuery']
