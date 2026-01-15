"""
Transaction Store - SQLite-based storage for banking transactions.

Provides atomic operations for storing and querying transactions.
Uses Decimal for all monetary values.

Source: Adapted from D:/Projects/trader-ai/src/finances/bank_database.py
Improvements:
- Uses Decimal instead of float for amounts
- Cleaner API without Plaid-specific dependencies
- Better query building with TransactionQuery
- Python-side aggregations to preserve Decimal precision (2026-01-10)
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from decimal import Decimal
from dataclasses import dataclass
import json


@dataclass
class TransactionQuery:
    """Query builder for transaction searches."""
    account_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    category: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    pending_only: bool = False
    limit: int = 100
    offset: int = 0

    def to_sql(self) -> tuple[str, list]:
        """Build SQL WHERE clause and parameters."""
        conditions = []
        params = []

        if self.account_id:
            conditions.append("account_id = ?")
            params.append(self.account_id)

        if self.start_date:
            conditions.append("date >= ?")
            params.append(self.start_date)

        if self.end_date:
            conditions.append("date <= ?")
            params.append(self.end_date)

        if self.category:
            conditions.append("category LIKE ?")
            params.append(f"%{self.category}%")

        if self.min_amount is not None:
            conditions.append("amount >= ?")
            params.append(str(self.min_amount))

        if self.max_amount is not None:
            conditions.append("amount <= ?")
            params.append(str(self.max_amount))

        if self.pending_only:
            conditions.append("pending = 1")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params


class TransactionStore:
    """
    SQLite-based transaction storage.

    Thread-safe for read operations. Write operations should be serialized.
    All monetary amounts are stored and returned as Decimal.
    """

    def __init__(self, db_path: str):
        """
        Initialize transaction store.

        Args:
            db_path: Path to SQLite database file (created if doesn't exist)
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT,
                subtype TEXT,
                mask TEXT,
                current_balance TEXT DEFAULT '0',
                available_balance TEXT,
                currency TEXT DEFAULT 'USD',
                institution_name TEXT,
                last_synced TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                amount TEXT NOT NULL,
                date DATE NOT NULL,
                name TEXT,
                merchant_name TEXT,
                category TEXT,
                pending INTEGER DEFAULT 0,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
            )
        """)

        # Indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_account
            ON transactions(account_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date
            ON transactions(date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_category
            ON transactions(category)
        """)

        conn.commit()
        conn.close()

    def upsert_account(self, account: Dict[str, Any]) -> None:
        """
        Insert or update an account.

        Args:
            account: Account dictionary with account_id, name, balances, etc.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO accounts (
                account_id, name, type, subtype, mask,
                current_balance, available_balance, currency,
                institution_name, last_synced
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(account_id) DO UPDATE SET
                name = excluded.name,
                type = excluded.type,
                subtype = excluded.subtype,
                mask = excluded.mask,
                current_balance = excluded.current_balance,
                available_balance = excluded.available_balance,
                currency = excluded.currency,
                institution_name = excluded.institution_name,
                last_synced = excluded.last_synced
        """, (
            account['account_id'],
            account.get('name'),
            account.get('type'),
            account.get('subtype'),
            account.get('mask'),
            str(account.get('current_balance', 0)),
            str(account['available_balance']) if account.get('available_balance') else None,
            account.get('currency', 'USD'),
            account.get('institution_name'),
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()

    def upsert_transaction(self, transaction: Dict[str, Any]) -> None:
        """
        Insert or update a transaction.

        Args:
            transaction: Transaction dictionary with transaction_id, amount, etc.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Convert category list to string if needed
        category = transaction.get('category', [])
        if isinstance(category, list):
            category = ', '.join(category)

        # Convert metadata dict to JSON if present
        metadata = transaction.get('metadata')
        if metadata and isinstance(metadata, dict):
            metadata = json.dumps(metadata)

        cursor.execute("""
            INSERT INTO transactions (
                transaction_id, account_id, amount, date, name,
                merchant_name, category, pending, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(transaction_id) DO UPDATE SET
                amount = excluded.amount,
                date = excluded.date,
                name = excluded.name,
                merchant_name = excluded.merchant_name,
                category = excluded.category,
                pending = excluded.pending,
                metadata = excluded.metadata
        """, (
            transaction['transaction_id'],
            transaction['account_id'],
            str(transaction['amount']),  # Store as string for Decimal precision
            transaction['date'],
            transaction.get('name'),
            transaction.get('merchant_name'),
            category,
            1 if transaction.get('pending') else 0,
            metadata
        ))

        conn.commit()
        conn.close()

    def upsert_transactions(self, transactions: List[Dict[str, Any]]) -> int:
        """
        Bulk insert/update transactions with batch commit (efficient).

        Args:
            transactions: List of transaction dictionaries

        Returns:
            Number of transactions processed
        """
        if not transactions:
            return 0

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Prepare batch data
            batch_data = []
            for txn in transactions:
                category = txn.get('category', [])
                if isinstance(category, list):
                    category = ', '.join(category)

                metadata = txn.get('metadata')
                if metadata and isinstance(metadata, dict):
                    metadata = json.dumps(metadata)

                batch_data.append((
                    txn['transaction_id'],
                    txn['account_id'],
                    str(txn['amount']),
                    txn['date'],
                    txn.get('name'),
                    txn.get('merchant_name'),
                    category,
                    1 if txn.get('pending') else 0,
                    metadata
                ))

            # Batch insert with single commit
            cursor.executemany("""
                INSERT INTO transactions (
                    transaction_id, account_id, amount, date, name,
                    merchant_name, category, pending, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(transaction_id) DO UPDATE SET
                    amount = excluded.amount,
                    date = excluded.date,
                    name = excluded.name,
                    merchant_name = excluded.merchant_name,
                    category = excluded.category,
                    pending = excluded.pending,
                    metadata = excluded.metadata
            """, batch_data)

            conn.commit()
            return len(transactions)
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Batch upsert failed: {e}") from e
        finally:
            conn.close()

    def get_transactions(self, query: TransactionQuery = None) -> List[Dict[str, Any]]:
        """
        Query transactions with filters.

        Args:
            query: TransactionQuery with filter criteria

        Returns:
            List of transaction dictionaries with Decimal amounts
        """
        if query is None:
            query = TransactionQuery()

        conn = self._get_connection()
        cursor = conn.cursor()

        where_clause, params = query.to_sql()

        cursor.execute(f"""
            SELECT
                t.transaction_id,
                t.account_id,
                t.amount,
                t.date,
                t.name,
                t.merchant_name,
                t.category,
                t.pending,
                t.metadata,
                a.name as account_name,
                a.mask as account_mask
            FROM transactions t
            LEFT JOIN accounts a ON t.account_id = a.account_id
            WHERE {where_clause}
            ORDER BY t.date DESC, t.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [query.limit, query.offset])

        results = []
        for row in cursor.fetchall():
            txn = dict(row)
            # Convert amount string back to Decimal
            txn['amount'] = Decimal(txn['amount'])
            # Parse metadata JSON if present
            if txn.get('metadata'):
                try:
                    txn['metadata'] = json.loads(txn['metadata'])
                except json.JSONDecodeError:
                    pass
            results.append(txn)

        conn.close()
        return results

    def get_recent_transactions(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get transactions from the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of transaction dictionaries sorted by date (newest first)
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        query = TransactionQuery(start_date=cutoff_date, limit=500)
        return self.get_transactions(query)

    def get_spending_by_category(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Aggregate spending by category using Decimal arithmetic (preserves precision).

        Args:
            days: Number of days to look back

        Returns:
            List of category summaries sorted by total (highest first)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cutoff_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()

        # Fetch raw data and aggregate in Python to preserve Decimal precision
        # (SQLite CAST AS REAL loses precision for financial calculations)
        cursor.execute("""
            SELECT category, amount
            FROM transactions
            WHERE date >= ?
            AND category IS NOT NULL
            AND category != ''
        """, (cutoff_date,))

        # Aggregate with Decimal precision
        categories: Dict[str, Dict[str, Any]] = {}
        for row in cursor.fetchall():
            category = row['category']
            amount = Decimal(row['amount'])

            # Only count positive amounts (expenses)
            if amount <= 0:
                continue

            if category not in categories:
                categories[category] = {
                    'category': category,
                    'transaction_count': 0,
                    'total_amount': Decimal('0'),
                    'amounts': []  # For calculating average
                }

            categories[category]['transaction_count'] += 1
            categories[category]['total_amount'] += amount
            categories[category]['amounts'].append(amount)

        conn.close()

        # Calculate averages and build results
        results = []
        for cat_data in categories.values():
            amounts = cat_data.pop('amounts')
            if amounts:
                cat_data['avg_amount'] = cat_data['total_amount'] / len(amounts)
            else:
                cat_data['avg_amount'] = Decimal('0')
            results.append(cat_data)

        # Sort by total_amount descending
        results.sort(key=lambda x: x['total_amount'], reverse=True)
        return results

    def get_account_summary(self) -> Dict[str, Any]:
        """
        Get summary of all accounts with proper Decimal precision.

        Returns:
            Dictionary with total_balance, account_count, and accounts list
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Fetch without CAST AS REAL to preserve Decimal precision
        # Sorting done in Python to maintain precision
        cursor.execute("""
            SELECT
                account_id, name, type, subtype, mask,
                current_balance, available_balance, currency,
                institution_name, last_synced
            FROM accounts
        """)

        accounts = []
        total_balance = Decimal("0")

        for row in cursor.fetchall():
            account = dict(row)
            account['current_balance'] = Decimal(account['current_balance'] or '0')
            if account['available_balance']:
                account['available_balance'] = Decimal(account['available_balance'])
            total_balance += account['current_balance']
            accounts.append(account)

        conn.close()

        # Sort by current_balance descending (done in Python to preserve Decimal precision)
        accounts.sort(key=lambda x: x['current_balance'], reverse=True)

        return {
            'total_balance': total_balance,
            'account_count': len(accounts),
            'accounts': accounts
        }

    def delete_transaction(self, transaction_id: str) -> bool:
        """
        Delete a transaction.

        Args:
            transaction_id: Transaction ID to delete

        Returns:
            True if deleted, False if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM transactions WHERE transaction_id = ?", (transaction_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted
