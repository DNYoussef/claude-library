# Stripe Payment Integration Component

Production-ready async Stripe integration with webhook handling.

## Features

- Async payment intent management
- Customer CRUD operations
- Subscription lifecycle
- Secure webhook processing with HMAC verification
- Idempotent webhook handling
- **Decimal-only money handling (NO floats)**

## Installation

```bash
pip install stripe[async]
```

## Usage

### Basic Client

```python
from library.components.payments.stripe import StripeClient, StripeConfig
from library.common.types import Money
from decimal import Decimal

# Configure
config = StripeConfig(api_key="sk_test_...")
client = StripeClient(config)

# Create customer
customer = await client.create_customer_async(
    email="user@example.com",
    name="John Doe",
    metadata={"user_id": "123"}
)

# Create payment intent ($19.99)
intent = await client.create_payment_intent_async(
    amount=Money(Decimal("19.99"), "USD"),
    customer_id=customer.id
)

print(f"Payment intent: {intent.id}, status: {intent.status}")
```

### Webhook Handling

```python
from library.components.payments.stripe import (
    StripeWebhookHandler,
    WebhookEventType,
)

# Create handler
handler = StripeWebhookHandler(
    webhook_secret="whsec_...",
    tolerance=300,  # 5 minute tolerance
)

# Register handlers
@handler.on(WebhookEventType.PAYMENT_INTENT_SUCCEEDED)
async def handle_payment_success(event):
    payment = event.object
    print(f"Payment succeeded: {payment['id']}")
    # Update order status, send receipt, etc.

@handler.on(WebhookEventType.SUBSCRIPTION_CREATED)
async def handle_subscription(event):
    subscription = event.object
    print(f"New subscription: {subscription['id']}")

# FastAPI integration
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    try:
        event = await handler.handle_webhook(payload, signature)
        return {"status": "ok", "event_id": event.id}
    except SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")
```

### Subscriptions

```python
# Create subscription
subscription = await client.create_subscription_async(
    customer_id="cus_...",
    price_id="price_...",  # From Stripe dashboard
)

# Cancel at period end
await client.cancel_subscription_async(
    subscription.id,
    at_period_end=True  # Finish current period
)
```

## CRITICAL: Money Handling

**NEVER use floats for money.** Always use Decimal:

```python
# CORRECT
from decimal import Decimal
amount = Money(Decimal("19.99"), "USD")

# WRONG - Raises FloatNotAllowedError
amount = Money(19.99, "USD")
```

## Event Types

| Event | Description |
|-------|-------------|
| `PAYMENT_INTENT_SUCCEEDED` | Payment completed successfully |
| `PAYMENT_INTENT_FAILED` | Payment failed |
| `SUBSCRIPTION_CREATED` | New subscription started |
| `SUBSCRIPTION_DELETED` | Subscription canceled |
| `INVOICE_PAID` | Invoice paid |
| `CHARGE_REFUNDED` | Refund processed |

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_key` | `STRIPE_SECRET_KEY` env | Stripe secret key |
| `api_version` | `2024-12-18.acacia` | API version |
| `webhook_secret` | `STRIPE_WEBHOOK_SECRET` env | Webhook signing secret |
| `tolerance` | `300` | Signature timestamp tolerance (seconds) |

## Sources

- [stripe-python](https://github.com/stripe/stripe-python) - Official SDK
- [Stripe API Docs](https://stripe.com/docs/api)
- [Webhook Signatures](https://stripe.com/docs/webhooks/signatures)
