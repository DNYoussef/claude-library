"""
Idempotency Middleware - FastAPI integration for idempotent endpoints.

Provides:
- @idempotent decorator for individual endpoints
- FastAPIIdempotencyMiddleware for global application
"""

from functools import wraps
from typing import Optional, Callable, Awaitable, List
import json
import hashlib
import logging
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .store import IdempotencyStore, CachedResponse

logger = logging.getLogger(__name__)


def idempotent(
    store: IdempotencyStore,
    key_header: str = "Idempotency-Key",
    ttl_seconds: int = 86400,
    key_from_body: bool = True,
    methods: Optional[List[str]] = None
):
    """
    Decorator for idempotent endpoint handlers.

    Args:
        store: IdempotencyStore instance
        key_header: HTTP header for idempotency key (default: Idempotency-Key)
        ttl_seconds: How long to cache responses (default: 24 hours)
        key_from_body: If True, generate key from body when header missing
        methods: HTTP methods to apply idempotency (default: POST, PUT, PATCH)

    Usage:
        store = InMemoryIdempotencyStore()

        @app.post("/webhooks/stripe")
        @idempotent(store)
        async def handle_stripe_webhook(request: Request):
            # This handler is guaranteed to run only once per key
            return {"status": "processed"}
    """
    if methods is None:
        methods = ["POST", "PUT", "PATCH"]

    def decorator(func: Callable[..., Awaitable[Response]]):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Only apply to specified methods
            if request.method not in methods:
                return await func(request, *args, **kwargs)

            # Get or generate idempotency key
            idem_key = request.headers.get(key_header)

            if not idem_key and key_from_body:
                # Generate from request body
                body = await request.body()
                idem_key = hashlib.sha256(body).hexdigest()
                # Reset body for handler (consumed by read)
                request._body = body

            if not idem_key:
                # No key provided and not generating from body
                logger.warning(f"No idempotency key for {request.method} {request.url.path}")
                return await func(request, *args, **kwargs)

            # Check for cached response
            cached = await store.get(idem_key)
            if cached is not None:
                logger.info(f"Idempotent replay for key: {idem_key[:16]}...")
                return Response(
                    content=cached.body,
                    status_code=cached.status_code,
                    headers={
                        **cached.headers,
                        "X-Idempotent-Replay": "true",
                        "X-Idempotent-Key": idem_key[:16] + "...",
                    },
                    media_type="application/json"
                )

            # Try to acquire lock (prevent concurrent processing of same key)
            if not await store.acquire_lock(idem_key):
                # Another request is processing this key
                logger.warning(f"Concurrent request for key: {idem_key[:16]}...")
                return Response(
                    content=json.dumps({
                        "error": "Request already in progress",
                        "idempotency_key": idem_key[:16] + "..."
                    }),
                    status_code=409,  # Conflict
                    media_type="application/json"
                )

            try:
                # Execute the actual handler
                response = await func(request, *args, **kwargs)

                # Cache the response
                if 200 <= response.status_code < 500:
                    # Only cache successful responses and client errors
                    # Don't cache 5xx errors - they should be retried
                    body = response.body.decode() if hasattr(response, 'body') else ""
                    cached_response = CachedResponse(
                        status_code=response.status_code,
                        body=body,
                        headers=dict(response.headers),
                        processed_at=datetime.utcnow().isoformat(),
                        idempotency_key=idem_key
                    )
                    await store.set(idem_key, cached_response, ttl_seconds)

                return response

            finally:
                # Always release the lock
                await store.release_lock(idem_key)

        return wrapper
    return decorator


class FastAPIIdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Global middleware for idempotency on all matching endpoints.

    Usage:
        from fastapi import FastAPI
        from library.patterns.webhook_idempotency import (
            FastAPIIdempotencyMiddleware,
            InMemoryIdempotencyStore
        )

        app = FastAPI()
        store = InMemoryIdempotencyStore()
        app.add_middleware(
            FastAPIIdempotencyMiddleware,
            store=store,
            paths=["/api/webhooks", "/api/payments"]
        )
    """

    def __init__(
        self,
        app: ASGIApp,
        store: IdempotencyStore,
        paths: Optional[List[str]] = None,
        key_header: str = "Idempotency-Key",
        ttl_seconds: int = 86400,
        methods: Optional[List[str]] = None
    ):
        """
        Initialize middleware.

        Args:
            app: FastAPI/Starlette application
            store: IdempotencyStore instance
            paths: URL path prefixes to apply idempotency to
            key_header: HTTP header for idempotency key
            ttl_seconds: Cache TTL
            methods: HTTP methods to apply to
        """
        super().__init__(app)
        self.store = store
        self.paths = paths or []
        self.key_header = key_header
        self.ttl_seconds = ttl_seconds
        self.methods = methods or ["POST", "PUT", "PATCH"]

    def _should_apply(self, request: Request) -> bool:
        """Check if idempotency should apply to this request."""
        # Check method
        if request.method not in self.methods:
            return False

        # Check path prefixes
        if self.paths:
            return any(request.url.path.startswith(p) for p in self.paths)

        # If no paths specified, apply to all matching methods
        return True

    async def dispatch(self, request: Request, call_next):
        """Process request with idempotency check."""
        if not self._should_apply(request):
            return await call_next(request)

        # Get idempotency key
        idem_key = request.headers.get(self.key_header)

        if not idem_key:
            # Generate from body for webhooks
            body = await request.body()
            idem_key = hashlib.sha256(body).hexdigest()

            # Reconstruct request with body
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive

        # Check cache
        cached = await self.store.get(idem_key)
        if cached is not None:
            return Response(
                content=cached.body,
                status_code=cached.status_code,
                headers={
                    **cached.headers,
                    "X-Idempotent-Replay": "true"
                },
                media_type="application/json"
            )

        # Acquire lock
        if not await self.store.acquire_lock(idem_key):
            return Response(
                content=json.dumps({"error": "Request already in progress"}),
                status_code=409,
                media_type="application/json"
            )

        try:
            response = await call_next(request)

            # Cache successful responses
            if 200 <= response.status_code < 500:
                body_bytes = b""
                async for chunk in response.body_iterator:
                    body_bytes += chunk

                cached_response = CachedResponse(
                    status_code=response.status_code,
                    body=body_bytes.decode(),
                    headers=dict(response.headers),
                    processed_at=datetime.utcnow().isoformat(),
                    idempotency_key=idem_key
                )
                await self.store.set(idem_key, cached_response, self.ttl_seconds)

                return Response(
                    content=body_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )

            return response

        finally:
            await self.store.release_lock(idem_key)
