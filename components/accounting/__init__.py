"""
Accounting Components

Provides transaction tracking, categorization, and reporting.

Components:
- transactions: Transaction storage and querying
- categorizer: Transaction categorization (rule-based and AI)
- reports: P&L, balance sheets, spending summaries

All monetary values use Decimal (NEVER float!).
"""

from .transactions import TransactionStore, TransactionQuery

__all__ = [
    'TransactionStore',
    'TransactionQuery',
]
