"""
Webhook Idempotency Pattern - Library Component

CRITICAL RULE: EVERY webhook handler MUST use idempotency to prevent duplicate processing.

This pattern ensures webhooks are processed exactly once, even if:
- The sender retries the webhook
- Network issues cause duplicates
- The handler fails partway through

Usage:
    from library.patterns.webhook_idempotency import IdempotencyStore, idempotent

    # Create a store (in-memory for dev, Redis/Postgres for prod)
    store = InMemoryIdempotencyStore()

    # Use as decorator
    @idempotent(store)
    async def handle_stripe_webhook(request: Request):
        # This will only execute once per idempotency key
        process_payment(request)
"""

from .store import (
    IdempotencyStore,
    InMemoryIdempotencyStore,
    RedisIdempotencyStore,
    PostgresIdempotencyStore,
)
from .middleware import idempotent, FastAPIIdempotencyMiddleware
from .decorators import idempotent_handler, ensure_idempotent
from .utils import generate_idempotency_key, extract_key_from_request

__all__ = [
    # Stores
    'IdempotencyStore',
    'InMemoryIdempotencyStore',
    'RedisIdempotencyStore',
    'PostgresIdempotencyStore',
    # Middleware
    'idempotent',
    'FastAPIIdempotencyMiddleware',
    # Decorators
    'idempotent_handler',
    'ensure_idempotent',
    # Utilities
    'generate_idempotency_key',
    'extract_key_from_request',
]
