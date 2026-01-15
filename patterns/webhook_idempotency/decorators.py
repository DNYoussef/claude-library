"""
Idempotency Decorators - Simpler alternatives to full middleware.
"""

from functools import wraps
from typing import Callable, Awaitable, Optional
import logging

from .store import IdempotencyStore, CachedResponse
from .utils import generate_idempotency_key

logger = logging.getLogger(__name__)


def idempotent_handler(
    store: IdempotencyStore,
    key_extractor: Optional[Callable] = None,
    ttl_seconds: int = 86400
):
    """
    Decorator for making any async function idempotent.

    Unlike the middleware decorator, this works with any async function,
    not just FastAPI handlers.

    Args:
        store: IdempotencyStore instance
        key_extractor: Function to extract idempotency key from args
        ttl_seconds: Cache TTL

    Usage:
        @idempotent_handler(store, key_extractor=lambda payload: payload['id'])
        async def process_event(payload: dict):
            # Process the event
            return {"processed": True}
    """
    def decorator(func: Callable[..., Awaitable]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract or generate key
            if key_extractor:
                idem_key = key_extractor(*args, **kwargs)
            else:
                # Generate from stringified args
                idem_key = generate_idempotency_key(str(args) + str(kwargs))

            # Check cache
            cached = await store.get(idem_key)
            if cached is not None:
                logger.info(f"Returning cached result for {func.__name__}")
                return cached.body

            # Acquire lock
            if not await store.acquire_lock(idem_key):
                raise RuntimeError("Concurrent execution of same idempotency key")

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Cache result
                cached_response = CachedResponse(
                    status_code=200,
                    body=str(result),
                    headers={},
                    processed_at="",
                    idempotency_key=idem_key
                )
                await store.set(idem_key, cached_response, ttl_seconds)

                return result

            finally:
                await store.release_lock(idem_key)

        return wrapper
    return decorator


def ensure_idempotent(
    store: IdempotencyStore,
    key: str,
    ttl_seconds: int = 86400
):
    """
    Context manager for idempotent execution blocks.

    Usage:
        async with ensure_idempotent(store, event_id) as ctx:
            if ctx.already_processed:
                return ctx.cached_result
            # Do the work
            result = process_event()
            ctx.set_result(result)
    """
    class IdempotentContext:
        def __init__(self):
            self.already_processed = False
            self.cached_result = None
            self._result = None
            self._lock_acquired = False

        async def __aenter__(self):
            # Check cache
            cached = await store.get(key)
            if cached is not None:
                self.already_processed = True
                self.cached_result = cached.body
                return self

            # Acquire lock
            self._lock_acquired = await store.acquire_lock(key)
            if not self._lock_acquired:
                raise RuntimeError("Could not acquire idempotency lock")

            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if self._lock_acquired:
                # Cache result if we have one and no error
                if exc_type is None and self._result is not None:
                    cached_response = CachedResponse(
                        status_code=200,
                        body=str(self._result),
                        headers={},
                        processed_at="",
                        idempotency_key=key
                    )
                    await store.set(key, cached_response, ttl_seconds)

                await store.release_lock(key)

            return False  # Don't suppress exceptions

        def set_result(self, result):
            """Set the result to be cached."""
            self._result = result

    return IdempotentContext()
