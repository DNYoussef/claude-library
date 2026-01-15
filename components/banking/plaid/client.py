"""
Plaid API Client

Handles all Plaid API interactions with proper error handling.
Supports sandbox, development, and production environments.

Source: Adapted from D:/Projects/trader-ai/src/finances/plaid_client.py
Improvements:
- Uses Decimal for all money values (not float)
- Better error handling with PlaidError
- Async-ready structure
"""

import os
import json
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class PlaidError(Exception):
    """Plaid API error with structured information."""

    def __init__(self, message: str, error_code: str = None, error_type: str = None):
        super().__init__(message)
        self.error_code = error_code
        self.error_type = error_type


class PlaidClient:
    """
    Plaid API client for bank account integration.

    Supports sandbox, development, and production environments.
    Handles Link token creation, public token exchange, and data fetching.

    Environment Variables:
        PLAID_CLIENT_ID: Plaid client ID
        PLAID_SECRET: Plaid secret key
        PLAID_ENV: Environment (sandbox, development, production)
    """

    def __init__(
        self,
        client_id: str = None,
        secret: str = None,
        environment: str = "sandbox"
    ):
        """
        Initialize Plaid client.

        Args:
            client_id: Plaid client ID (falls back to PLAID_CLIENT_ID env var)
            secret: Plaid secret (falls back to PLAID_SECRET env var)
            environment: Plaid environment (sandbox, development, production)
        """
        self.client_id = client_id or os.getenv("PLAID_CLIENT_ID")
        self.secret = secret or os.getenv("PLAID_SECRET")
        self.environment = environment or os.getenv("PLAID_ENV", "sandbox")

        if not self.client_id or not self.secret:
            raise PlaidError(
                "Plaid credentials not provided. "
                "Set PLAID_CLIENT_ID and PLAID_SECRET environment variables.",
                error_code="MISSING_CREDENTIALS"
            )

        # Lazy-load plaid library
        self._client = None

    @property
    def client(self):
        """Lazy-initialize Plaid API client."""
        if self._client is None:
            try:
                import plaid
                from plaid.api import plaid_api
            except ImportError:
                raise PlaidError(
                    "plaid-python package required: pip install plaid-python",
                    error_code="MISSING_DEPENDENCY"
                )

            env_map = {
                "sandbox": plaid.Environment.Sandbox,
                "development": plaid.Environment.Development,
                "production": plaid.Environment.Production
            }

            if self.environment not in env_map:
                raise PlaidError(
                    f"Invalid environment: {self.environment}",
                    error_code="INVALID_ENVIRONMENT"
                )

            configuration = plaid.Configuration(
                host=env_map[self.environment],
                api_key={
                    'clientId': self.client_id,
                    'secret': self.secret,
                }
            )

            api_client = plaid.ApiClient(configuration)
            self._client = plaid_api.PlaidApi(api_client)

            logger.info(f"Plaid client initialized for {self.environment}")

        return self._client

    def create_link_token(
        self,
        user_id: str,
        client_name: str = "Banking App",
        products: List[str] = None,
        country_codes: List[str] = None,
        language: str = "en"
    ) -> Dict[str, str]:
        """
        Create a Link token for Plaid Link initialization.

        Args:
            user_id: Unique user identifier
            client_name: Your application name shown in Plaid Link
            products: Products to request (default: auth, transactions)
            country_codes: Supported countries (default: US)
            language: UI language

        Returns:
            Dict containing link_token, expiration, and request_id

        Raises:
            PlaidError: If API call fails
        """
        from plaid.model.link_token_create_request import LinkTokenCreateRequest
        from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
        from plaid.model.products import Products
        from plaid.model.country_code import CountryCode

        if products is None:
            products = ["auth", "transactions"]
        if country_codes is None:
            country_codes = ["US"]

        try:
            request = LinkTokenCreateRequest(
                user=LinkTokenCreateRequestUser(client_user_id=user_id),
                client_name=client_name,
                products=[Products(p) for p in products],
                country_codes=[CountryCode(c) for c in country_codes],
                language=language
            )

            response = self.client.link_token_create(request)

            logger.info(f"Link token created for user {user_id}")

            return {
                "link_token": response['link_token'],
                "expiration": response['expiration'],
                "request_id": response['request_id']
            }

        except Exception as e:
            self._handle_error(e)

    def exchange_public_token(self, public_token: str) -> str:
        """
        Exchange public token for access token.

        Call after user completes Plaid Link. Store the access_token securely!

        Args:
            public_token: Public token from Plaid Link

        Returns:
            Access token for future API calls

        Raises:
            PlaidError: If exchange fails
        """
        from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)

            logger.info(f"Public token exchanged. Item ID: {response['item_id']}")
            return response['access_token']

        except Exception as e:
            self._handle_error(e)

    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Fetch all linked bank accounts.

        Args:
            access_token: Access token from exchange_public_token()

        Returns:
            List of account dictionaries with Decimal balances

        Raises:
            PlaidError: If API call fails
        """
        from plaid.model.accounts_get_request import AccountsGetRequest

        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)

            accounts = []
            for account in response['accounts']:
                balances = account['balances']
                accounts.append({
                    'account_id': account['account_id'],
                    'name': account['name'],
                    'official_name': account.get('official_name'),
                    'type': account['type'],
                    'subtype': account.get('subtype'),
                    'mask': account.get('mask'),
                    # Use Decimal for money values!
                    'current_balance': Decimal(str(balances['current'])) if balances['current'] else Decimal("0"),
                    'available_balance': Decimal(str(balances['available'])) if balances.get('available') else None,
                    'currency_code': balances.get('iso_currency_code', 'USD')
                })

            logger.info(f"Retrieved {len(accounts)} bank accounts")
            return accounts

        except Exception as e:
            self._handle_error(e)

    def get_balances(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Fetch real-time account balances.

        Args:
            access_token: Access token from exchange_public_token()

        Returns:
            List of balance dictionaries with Decimal values

        Raises:
            PlaidError: If API call fails
        """
        from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest

        try:
            request = AccountsBalanceGetRequest(access_token=access_token)
            response = self.client.accounts_balance_get(request)

            balances = []
            for account in response['accounts']:
                bal = account['balances']
                balances.append({
                    'account_id': account['account_id'],
                    'name': account['name'],
                    'current': Decimal(str(bal['current'])) if bal['current'] else Decimal("0"),
                    'available': Decimal(str(bal['available'])) if bal.get('available') else None,
                    'currency': bal.get('iso_currency_code', 'USD'),
                    'type': account['type'],
                    'subtype': account.get('subtype')
                })

            logger.info(f"Retrieved balances for {len(balances)} accounts")
            return balances

        except Exception as e:
            self._handle_error(e)

    def get_transactions(
        self,
        access_token: str,
        start_date: str = None,
        end_date: str = None,
        count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch transactions for specified date range.

        Args:
            access_token: Access token from exchange_public_token()
            start_date: Start date (YYYY-MM-DD) - defaults to 30 days ago
            end_date: End date (YYYY-MM-DD) - defaults to today
            count: Maximum transactions to fetch (default 100)

        Returns:
            List of transaction dictionaries with Decimal amounts

        Raises:
            PlaidError: If API call fails
        """
        from plaid.model.transactions_get_request import TransactionsGetRequest
        from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions

        try:
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
                options=TransactionsGetRequestOptions(count=count)
            )

            response = self.client.transactions_get(request)

            transactions = []
            for txn in response['transactions']:
                transactions.append({
                    'transaction_id': txn['transaction_id'],
                    'account_id': txn['account_id'],
                    # Use Decimal for amount!
                    'amount': Decimal(str(txn['amount'])),
                    'date': str(txn['date']),
                    'name': txn['name'],
                    'merchant_name': txn.get('merchant_name'),
                    'category': txn.get('category', []),
                    'pending': txn['pending'],
                    'payment_channel': txn.get('payment_channel')
                })

            logger.info(f"Retrieved {len(transactions)} transactions from {start_date} to {end_date}")
            return transactions

        except Exception as e:
            self._handle_error(e)

    def _handle_error(self, exception: Exception):
        """Convert Plaid exceptions to PlaidError."""
        import plaid

        if not isinstance(exception, plaid.ApiException):
            raise PlaidError(f"Unexpected error: {str(exception)}")

        try:
            error_response = json.loads(exception.body)
            error_code = error_response.get('error_code', 'UNKNOWN')
            error_message = error_response.get('error_message', str(exception))
            error_type = error_response.get('error_type', 'API_ERROR')

            # Provide user-friendly messages for common errors
            if error_code == 'ITEM_LOGIN_REQUIRED':
                raise PlaidError(
                    "Bank login required. Please re-authenticate through Plaid Link.",
                    error_code=error_code,
                    error_type=error_type
                )
            if error_code == 'RATE_LIMIT_EXCEEDED':
                raise PlaidError(
                    "Rate limit exceeded. Please retry in a few minutes.",
                    error_code=error_code,
                    error_type=error_type
                )
            raise PlaidError(
                f"Plaid API error: {error_message}",
                error_code=error_code,
                error_type=error_type
            )

        except json.JSONDecodeError:
            raise PlaidError(f"Plaid API error: {str(exception)}")
