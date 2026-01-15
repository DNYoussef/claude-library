"""
Stripe Webhook Handler

Secure webhook processing with signature verification and idempotency.
Based on Stripe's official webhook handling best practices.

References:
- https://stripe.com/docs/webhooks
- https://stripe.com/docs/webhooks/signatures
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Awaitable
from datetime import datetime
import hashlib
import hmac
import time
import json
import os


class WebhookEventType(Enum):
    """Common Stripe webhook event types."""
    # Payment Intent Events
    PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"
    PAYMENT_INTENT_FAILED = "payment_intent.payment_failed"
    PAYMENT_INTENT_CANCELED = "payment_intent.canceled"
    PAYMENT_INTENT_CREATED = "payment_intent.created"

    # Customer Events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"

    # Subscription Events
    SUBSCRIPTION_CREATED = "customer.subscription.created"
    SUBSCRIPTION_UPDATED = "customer.subscription.updated"
    SUBSCRIPTION_DELETED = "customer.subscription.deleted"
    SUBSCRIPTION_TRIAL_ENDING = "customer.subscription.trial_will_end"

    # Invoice Events
    INVOICE_PAID = "invoice.paid"
    INVOICE_PAYMENT_FAILED = "invoice.payment_failed"
    INVOICE_UPCOMING = "invoice.upcoming"

    # Checkout Events
    CHECKOUT_COMPLETED = "checkout.session.completed"
    CHECKOUT_EXPIRED = "checkout.session.expired"

    # Charge Events
    CHARGE_SUCCEEDED = "charge.succeeded"
    CHARGE_FAILED = "charge.failed"
    CHARGE_REFUNDED = "charge.refunded"

    # Dispute Events
    CHARGE_DISPUTE_CREATED = "charge.dispute.created"
    CHARGE_DISPUTE_CLOSED = "charge.dispute.closed"


@dataclass
class WebhookEvent:
    """Parsed Stripe webhook event."""
    id: str
    type: str
    data: Dict[str, Any]
    created: datetime
    livemode: bool
    api_version: Optional[str] = None

    @property
    def object(self) -> Dict[str, Any]:
        """Get the event object data."""
        return self.data.get("object", {})


class SignatureVerificationError(Exception):
    """Raised when webhook signature verification fails."""
    pass


class WebhookProcessingError(Exception):
    """Raised when webhook processing fails."""
    pass


class StripeWebhookHandler:
    """
    Secure Stripe webhook handler with signature verification.

    Features:
    - HMAC signature verification
    - Timestamp tolerance (prevents replay attacks)
    - Event type routing
    - Idempotency support (via processed_events cache)

    Example:
        handler = StripeWebhookHandler(
            webhook_secret=os.environ["STRIPE_WEBHOOK_SECRET"]
        )

        @handler.on(WebhookEventType.PAYMENT_INTENT_SUCCEEDED)
        async def handle_payment_success(event: WebhookEvent):
            payment_intent = event.object
            # Process successful payment...

        # In FastAPI endpoint:
        @app.post("/webhooks/stripe")
        async def stripe_webhook(request: Request):
            payload = await request.body()
            signature = request.headers.get("stripe-signature")
            await handler.handle_webhook(payload, signature)
            return {"status": "ok"}
    """

    def __init__(
        self,
        webhook_secret: Optional[str] = None,
        tolerance: int = 300,  # 5 minutes
        enable_idempotency: bool = True,
        max_cached_events: int = 10000,
    ):
        self.webhook_secret = webhook_secret or os.environ.get("STRIPE_WEBHOOK_SECRET", "")
        self.tolerance = tolerance
        self.enable_idempotency = enable_idempotency
        self.max_cached_events = max_cached_events

        # Event handlers by type
        self._handlers: Dict[str, List[Callable[[WebhookEvent], Awaitable[None]]]] = {}

        # Processed event IDs for idempotency
        self._processed_events: Dict[str, datetime] = {}

        if not self.webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET required for webhook verification")

    def on(self, event_type: WebhookEventType):
        """
        Decorator to register an event handler.

        Example:
            @handler.on(WebhookEventType.PAYMENT_INTENT_SUCCEEDED)
            async def handle_payment(event: WebhookEvent):
                ...
        """
        def decorator(func: Callable[[WebhookEvent], Awaitable[None]]):
            type_str = event_type.value
            if type_str not in self._handlers:
                self._handlers[type_str] = []
            self._handlers[type_str].append(func)
            return func
        return decorator

    def register_handler(
        self,
        event_type: WebhookEventType,
        handler: Callable[[WebhookEvent], Awaitable[None]],
    ):
        """Register a handler function for an event type."""
        type_str = event_type.value
        if type_str not in self._handlers:
            self._handlers[type_str] = []
        self._handlers[type_str].append(handler)

    def verify_signature(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Raw request body bytes
            signature: Stripe-Signature header value

        Returns:
            Parsed event data

        Raises:
            SignatureVerificationError: If verification fails
        """
        if not signature:
            raise SignatureVerificationError("Missing signature header")

        # Parse signature header
        # Format: t=timestamp,v1=signature,v0=signature(deprecated)
        sig_parts = {}
        for part in signature.split(","):
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            sig_parts[key] = value

        timestamp_str = sig_parts.get("t")
        expected_sig = sig_parts.get("v1")

        if not timestamp_str or not expected_sig:
            raise SignatureVerificationError("Invalid signature format")

        try:
            timestamp = int(timestamp_str)
        except ValueError:
            raise SignatureVerificationError("Invalid timestamp in signature")

        # Check timestamp tolerance (prevent replay attacks)
        current_time = int(time.time())
        if abs(current_time - timestamp) > self.tolerance:
            raise SignatureVerificationError(
                f"Timestamp outside tolerance window ({self.tolerance}s)"
            )

        # Compute expected signature
        signed_payload = f"{timestamp}.".encode() + payload
        computed_sig = hmac.new(
            self.webhook_secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(computed_sig, expected_sig):
            raise SignatureVerificationError("Signature verification failed")

        # Parse and return event
        try:
            return json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise SignatureVerificationError(f"Invalid payload: {e}")

    def parse_event(self, event_data: Dict[str, Any]) -> WebhookEvent:
        """Parse raw event data into WebhookEvent."""
        return WebhookEvent(
            id=event_data["id"],
            type=event_data["type"],
            data=event_data.get("data", {}),
            created=datetime.fromtimestamp(event_data["created"]),
            livemode=event_data.get("livemode", False),
            api_version=event_data.get("api_version"),
        )

    def _is_already_processed(self, event_id: str) -> bool:
        """Check if event was already processed (idempotency)."""
        if not self.enable_idempotency:
            return False
        return event_id in self._processed_events

    def _mark_processed(self, event_id: str):
        """Mark event as processed."""
        if not self.enable_idempotency:
            return

        self._processed_events[event_id] = datetime.utcnow()

        # Cleanup old entries if cache is too large
        if len(self._processed_events) > self.max_cached_events:
            # Remove oldest 20%
            sorted_events = sorted(
                self._processed_events.items(),
                key=lambda x: x[1],
            )
            to_remove = len(sorted_events) // 5
            for event_id, _ in sorted_events[:to_remove]:
                del self._processed_events[event_id]

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> WebhookEvent:
        """
        Process a webhook request.

        Args:
            payload: Raw request body bytes
            signature: Stripe-Signature header value

        Returns:
            Parsed WebhookEvent

        Raises:
            SignatureVerificationError: If signature is invalid
            WebhookProcessingError: If handler fails
        """
        # Verify signature and parse
        event_data = self.verify_signature(payload, signature)
        event = self.parse_event(event_data)

        # Check idempotency
        if self._is_already_processed(event.id):
            return event  # Already processed, return early

        # Get handlers for this event type
        handlers = self._handlers.get(event.type, [])

        # Execute all handlers
        errors = []
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                errors.append(f"{handler.__name__}: {e}")

        # Mark as processed (even if some handlers failed)
        self._mark_processed(event.id)

        if errors:
            raise WebhookProcessingError(
                f"Handler errors: {'; '.join(errors)}"
            )

        return event


# FastAPI middleware helper
def create_stripe_webhook_route(handler: StripeWebhookHandler):
    """
    Create a FastAPI route handler for Stripe webhooks.

    Example:
        from fastapi import FastAPI, Request

        app = FastAPI()
        webhook_handler = StripeWebhookHandler(webhook_secret="whsec_...")

        @app.post("/webhooks/stripe")
        async def stripe_webhook(request: Request):
            return await create_stripe_webhook_route(webhook_handler)(request)
    """
    async def route_handler(request):
        from fastapi import HTTPException
        from fastapi.responses import JSONResponse

        payload = await request.body()
        signature = request.headers.get("stripe-signature", "")

        try:
            event = await handler.handle_webhook(payload, signature)
            return JSONResponse({"status": "ok", "event_id": event.id})
        except SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except WebhookProcessingError as e:
            # Log but return 200 to prevent Stripe retries
            # In production, log this error properly
            return JSONResponse({"status": "error", "message": str(e)})

    return route_handler
