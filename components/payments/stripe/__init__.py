"""
Stripe Payment Integration Component

Production-ready Stripe integration with:
- Payment intent management
- Customer lifecycle
- Subscription handling
- Webhook processing with signature verification
- Decimal-only money handling (NO floats)

Based on official stripe-python SDK with async support.

References:
- https://github.com/stripe/stripe-python
- https://stripe.com/docs/api

Installation:
    pip install stripe[async]

Example:
    from library.components.payments.stripe import (
        StripeClient, StripeConfig,
        StripeWebhookHandler, WebhookEventType,
    )
    from decimal import Decimal

    # Create client
    client = StripeClient(StripeConfig(api_key="sk_test_..."))

    # Create payment
    from library.common.types import Money
    intent = await client.create_payment_intent_async(
        amount=Money(Decimal("19.99"), "USD"),
        customer_id="cus_..."
    )

    # Setup webhooks
    handler = StripeWebhookHandler(webhook_secret="whsec_...")

    @handler.on(WebhookEventType.PAYMENT_INTENT_SUCCEEDED)
    async def on_payment(event):
        print(f"Payment succeeded: {event.object['id']}")
"""

from .client import (
    StripeClient,
    StripeConfig,
    Customer,
    PaymentIntent,
    Subscription,
    PaymentStatus,
    SubscriptionStatus,
)

from .webhooks import (
    StripeWebhookHandler,
    WebhookEvent,
    WebhookEventType,
    SignatureVerificationError,
    WebhookProcessingError,
    create_stripe_webhook_route,
)

__all__ = [
    # Client
    "StripeClient",
    "StripeConfig",
    # Models
    "Customer",
    "PaymentIntent",
    "Subscription",
    "PaymentStatus",
    "SubscriptionStatus",
    # Webhooks
    "StripeWebhookHandler",
    "WebhookEvent",
    "WebhookEventType",
    "SignatureVerificationError",
    "WebhookProcessingError",
    "create_stripe_webhook_route",
]
