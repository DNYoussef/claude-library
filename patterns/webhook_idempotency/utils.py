"""
Utility Functions for Idempotency Pattern.
"""

import hashlib
import json
from typing import Optional
from fastapi import Request


def generate_idempotency_key(data: str) -> str:
    """
    Generate an idempotency key from data.

    Uses SHA-256 hash to create a consistent key for the same input.

    Args:
        data: String data to hash

    Returns:
        64-character hex string
    """
    return hashlib.sha256(data.encode()).hexdigest()


def generate_idempotency_key_from_dict(data: dict) -> str:
    """
    Generate idempotency key from a dictionary.

    Sorts keys for consistent ordering.

    Args:
        data: Dictionary to hash

    Returns:
        64-character hex string
    """
    # Sort keys for consistent hashing
    sorted_json = json.dumps(data, sort_keys=True)
    return generate_idempotency_key(sorted_json)


async def extract_key_from_request(
    request: Request,
    header_name: str = "Idempotency-Key",
    fallback_to_body: bool = True
) -> Optional[str]:
    """
    Extract idempotency key from a FastAPI request.

    Priority:
    1. Idempotency-Key header
    2. X-Idempotency-Key header (alternative)
    3. Body hash (if fallback_to_body=True)

    Args:
        request: FastAPI Request object
        header_name: Primary header to check
        fallback_to_body: Whether to generate from body if header missing

    Returns:
        Idempotency key or None
    """
    # Check primary header
    key = request.headers.get(header_name)
    if key:
        return key

    # Check alternative header
    key = request.headers.get("X-Idempotency-Key")
    if key:
        return key

    # Fallback to body hash
    if fallback_to_body:
        body = await request.body()
        if body:
            return generate_idempotency_key(body.decode())

    return None


def extract_stripe_idempotency_key(request: Request) -> Optional[str]:
    """
    Extract idempotency key for Stripe webhooks.

    Stripe uses the event ID as a natural idempotency key.

    Args:
        request: FastAPI Request with Stripe webhook payload

    Returns:
        Stripe event ID or None
    """
    # Stripe sends event ID in the payload
    try:
        body = request.state._body if hasattr(request.state, '_body') else None
        if body:
            payload = json.loads(body)
            return payload.get('id')  # Stripe event ID like "evt_xxx"
    except (json.JSONDecodeError, AttributeError):
        pass

    return None


def extract_webhook_signature_key(
    request: Request,
    signature_header: str = "X-Webhook-Signature"
) -> Optional[str]:
    """
    Extract idempotency key from webhook signature.

    Many webhook providers include a signature header that's unique per event.

    Args:
        request: FastAPI Request
        signature_header: Header containing the signature

    Returns:
        Signature hash or None
    """
    signature = request.headers.get(signature_header)
    if signature:
        # Hash the signature to normalize length
        return generate_idempotency_key(signature)
    return None
