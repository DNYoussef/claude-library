"""
Stripe Payment Client

Production-ready async Stripe integration based on official stripe-python SDK patterns.
Uses stripe[async] for native async support (v13.0.1+).

References:
- https://github.com/stripe/stripe-python
- https://stripe.com/docs/api

IMPORTANT: Uses Decimal for all monetary values - NO floats allowed.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional
from datetime import datetime
import os

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


class PaymentStatus(Enum):
    """Stripe payment intent statuses."""
    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    REQUIRES_ACTION = "requires_action"
    PROCESSING = "processing"
    REQUIRES_CAPTURE = "requires_capture"
    CANCELED = "canceled"
    SUCCEEDED = "succeeded"


class SubscriptionStatus(Enum):
    """Stripe subscription statuses."""
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    PAUSED = "paused"


@dataclass
class StripeConfig:
    """Stripe client configuration."""
    api_key: str = field(default_factory=lambda: os.environ.get("STRIPE_SECRET_KEY", ""))
    api_version: str = "2024-12-18.acacia"
    max_retries: int = 3
    timeout: int = 30

    def __post_init__(self):
        if not self.api_key:
            raise ValueError("STRIPE_SECRET_KEY required")


@dataclass
class Customer:
    """Stripe customer data."""
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    created: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class PaymentIntent:
    """Stripe payment intent data."""
    id: str
    amount: Money
    status: PaymentStatus
    customer_id: Optional[str] = None
    created: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Subscription:
    """Stripe subscription data."""
    id: str
    customer_id: str
    status: SubscriptionStatus
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)


class StripeClient:
    """
    Async Stripe API client.

    Uses official stripe-python with async support (stripe[async]).
    All monetary values use Decimal - floats are rejected.

    Example:
        client = StripeClient(config)

        # Create customer
        customer = await client.create_customer_async(
            email="user@example.com",
            name="John Doe"
        )

        # Create payment intent (amount in dollars as Decimal - converted to cents internally)
        intent = await client.create_payment_intent_async(
            amount=Money(Decimal("19.99"), "USD"),  # $19.99 -> 1999 cents
            customer_id=customer.id
        )
    """

    def __init__(self, config: Optional[StripeConfig] = None):
        self.config = config or StripeConfig()
        self._client = None

    async def _get_client(self):
        """Lazy initialize Stripe client."""
        if self._client is None:
            try:
                import stripe
                from stripe import StripeClient as _StripeClient

                self._client = _StripeClient(
                    api_key=self.config.api_key,
                    stripe_version=self.config.api_version,
                )
            except ImportError:
                raise ImportError(
                    "stripe package required. Install with: pip install stripe[async]"
                )
        return self._client

    def _money_to_cents(self, money: Money) -> int:
        """Convert Money to Stripe cents (integer)."""
        if isinstance(money.amount, float):
            raise TypeError("Money amount must be Decimal, not float")
        # Stripe uses cents for USD
        return int(money.amount * 100)

    def _cents_to_money(self, cents: int, currency: str = "USD") -> Money:
        """Convert Stripe cents to Money."""
        return Money(Decimal(cents) / Decimal(100), currency.upper())

    # Customer Operations

    async def create_customer_async(
        self,
        email: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Customer:
        """Create a new Stripe customer."""
        client = await self._get_client()

        params = {}
        if email:
            params["email"] = email
        if name:
            params["name"] = name
        if metadata:
            params["metadata"] = metadata

        result = await client.customers.create_async(**params)

        return Customer(
            id=result.id,
            email=result.email,
            name=result.name,
            created=datetime.fromtimestamp(result.created) if result.created else None,
            metadata=dict(result.metadata) if result.metadata else {},
        )

    async def get_customer_async(self, customer_id: str) -> Customer:
        """Retrieve a customer by ID."""
        client = await self._get_client()
        result = await client.customers.retrieve_async(customer_id)

        return Customer(
            id=result.id,
            email=result.email,
            name=result.name,
            created=datetime.fromtimestamp(result.created) if result.created else None,
            metadata=dict(result.metadata) if result.metadata else {},
        )

    async def update_customer_async(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Customer:
        """Update a customer."""
        client = await self._get_client()

        params = {}
        if email is not None:
            params["email"] = email
        if name is not None:
            params["name"] = name
        if metadata is not None:
            params["metadata"] = metadata

        result = await client.customers.update_async(customer_id, **params)

        return Customer(
            id=result.id,
            email=result.email,
            name=result.name,
            created=datetime.fromtimestamp(result.created) if result.created else None,
            metadata=dict(result.metadata) if result.metadata else {},
        )

    # Payment Intent Operations

    async def create_payment_intent_async(
        self,
        amount: Money,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        automatic_payment_methods: bool = True,
    ) -> PaymentIntent:
        """
        Create a payment intent.

        Args:
            amount: Money object with Decimal amount (e.g., Decimal("19.99") for $19.99)
            customer_id: Optional customer to associate
            metadata: Optional key-value metadata
            automatic_payment_methods: Enable automatic payment methods (default True)
        """
        client = await self._get_client()

        params = {
            "amount": self._money_to_cents(amount),
            "currency": amount.currency.lower(),
        }

        if customer_id:
            params["customer"] = customer_id
        if metadata:
            params["metadata"] = metadata
        if automatic_payment_methods:
            params["automatic_payment_methods"] = {"enabled": True}

        result = await client.payment_intents.create_async(**params)

        return PaymentIntent(
            id=result.id,
            amount=self._cents_to_money(result.amount, result.currency),
            status=PaymentStatus(result.status),
            customer_id=result.customer,
            created=datetime.fromtimestamp(result.created) if result.created else None,
            metadata=dict(result.metadata) if result.metadata else {},
        )

    async def get_payment_intent_async(self, intent_id: str) -> PaymentIntent:
        """Retrieve a payment intent by ID."""
        client = await self._get_client()
        result = await client.payment_intents.retrieve_async(intent_id)

        return PaymentIntent(
            id=result.id,
            amount=self._cents_to_money(result.amount, result.currency),
            status=PaymentStatus(result.status),
            customer_id=result.customer,
            created=datetime.fromtimestamp(result.created) if result.created else None,
            metadata=dict(result.metadata) if result.metadata else {},
        )

    async def confirm_payment_intent_async(self, intent_id: str) -> PaymentIntent:
        """Confirm a payment intent."""
        client = await self._get_client()
        result = await client.payment_intents.confirm_async(intent_id)

        return PaymentIntent(
            id=result.id,
            amount=self._cents_to_money(result.amount, result.currency),
            status=PaymentStatus(result.status),
            customer_id=result.customer,
            created=datetime.fromtimestamp(result.created) if result.created else None,
            metadata=dict(result.metadata) if result.metadata else {},
        )

    async def cancel_payment_intent_async(self, intent_id: str) -> PaymentIntent:
        """Cancel a payment intent."""
        client = await self._get_client()
        result = await client.payment_intents.cancel_async(intent_id)

        return PaymentIntent(
            id=result.id,
            amount=self._cents_to_money(result.amount, result.currency),
            status=PaymentStatus(result.status),
            customer_id=result.customer,
            created=datetime.fromtimestamp(result.created) if result.created else None,
            metadata=dict(result.metadata) if result.metadata else {},
        )

    # Subscription Operations

    async def create_subscription_async(
        self,
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Subscription:
        """Create a subscription for a customer."""
        client = await self._get_client()

        params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
        }
        if metadata:
            params["metadata"] = metadata

        result = await client.subscriptions.create_async(**params)

        return Subscription(
            id=result.id,
            customer_id=result.customer,
            status=SubscriptionStatus(result.status),
            current_period_start=datetime.fromtimestamp(result.current_period_start) if result.current_period_start else None,
            current_period_end=datetime.fromtimestamp(result.current_period_end) if result.current_period_end else None,
            cancel_at_period_end=result.cancel_at_period_end,
            metadata=dict(result.metadata) if result.metadata else {},
        )

    async def get_subscription_async(self, subscription_id: str) -> Subscription:
        """Retrieve a subscription by ID."""
        client = await self._get_client()
        result = await client.subscriptions.retrieve_async(subscription_id)

        return Subscription(
            id=result.id,
            customer_id=result.customer,
            status=SubscriptionStatus(result.status),
            current_period_start=datetime.fromtimestamp(result.current_period_start) if result.current_period_start else None,
            current_period_end=datetime.fromtimestamp(result.current_period_end) if result.current_period_end else None,
            cancel_at_period_end=result.cancel_at_period_end,
            metadata=dict(result.metadata) if result.metadata else {},
        )

    async def cancel_subscription_async(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> Subscription:
        """Cancel a subscription."""
        client = await self._get_client()

        if at_period_end:
            result = await client.subscriptions.update_async(
                subscription_id,
                cancel_at_period_end=True,
            )
        else:
            result = await client.subscriptions.cancel_async(subscription_id)

        return Subscription(
            id=result.id,
            customer_id=result.customer,
            status=SubscriptionStatus(result.status),
            current_period_start=datetime.fromtimestamp(result.current_period_start) if result.current_period_start else None,
            current_period_end=datetime.fromtimestamp(result.current_period_end) if result.current_period_end else None,
            cancel_at_period_end=result.cancel_at_period_end,
            metadata=dict(result.metadata) if result.metadata else {},
        )
