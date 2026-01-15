"""
Tests for Webhook Idempotency Pattern.

Run with: pytest library/patterns/webhook-idempotency/tests/
"""

import pytest
import asyncio
from datetime import datetime
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from store import InMemoryIdempotencyStore, CachedResponse


class TestInMemoryStore:
    """Test InMemoryIdempotencyStore."""

    @pytest.fixture
    def store(self):
        return InMemoryIdempotencyStore()

    @pytest.mark.asyncio
    async def test_set_and_get(self, store):
        """Can store and retrieve a response."""
        response = CachedResponse(
            status_code=200,
            body='{"status": "ok"}',
            headers={"Content-Type": "application/json"},
            processed_at=datetime.utcnow().isoformat(),
            idempotency_key="test-key-123"
        )

        await store.set("test-key-123", response)
        retrieved = await store.get("test-key-123")

        assert retrieved is not None
        assert retrieved.status_code == 200
        assert retrieved.body == '{"status": "ok"}'

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store):
        """Get returns None for missing key."""
        result = await store.get("nonexistent-key")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists(self, store):
        """Exists correctly reports key presence."""
        response = CachedResponse(
            status_code=200,
            body="test",
            headers={},
            processed_at="",
            idempotency_key="test"
        )

        assert await store.exists("test-key") is False
        await store.set("test-key", response)
        assert await store.exists("test-key") is True

    @pytest.mark.asyncio
    async def test_delete(self, store):
        """Can delete a key."""
        response = CachedResponse(
            status_code=200,
            body="test",
            headers={},
            processed_at="",
            idempotency_key="test"
        )

        await store.set("test-key", response)
        assert await store.exists("test-key") is True

        deleted = await store.delete("test-key")
        assert deleted is True
        assert await store.exists("test-key") is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store):
        """Delete returns False for missing key."""
        result = await store.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_release_lock(self, store):
        """Can acquire and release a lock."""
        # Acquire lock
        acquired = await store.acquire_lock("resource-1")
        assert acquired is True

        # Second acquire should fail
        second_acquire = await store.acquire_lock("resource-1")
        assert second_acquire is False

        # Release and try again
        await store.release_lock("resource-1")
        third_acquire = await store.acquire_lock("resource-1")
        assert third_acquire is True

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, store):
        """Keys expire after TTL."""
        response = CachedResponse(
            status_code=200,
            body="test",
            headers={},
            processed_at="",
            idempotency_key="test"
        )

        # Set with 0-second TTL (immediate expiry)
        await store.set("expiring-key", response, ttl_seconds=0)

        # Should be expired immediately
        await asyncio.sleep(0.01)  # Small delay
        result = await store.get("expiring-key")
        assert result is None


class TestIdempotentBehavior:
    """Test idempotent behavior patterns."""

    @pytest.fixture
    def store(self):
        return InMemoryIdempotencyStore()

    @pytest.mark.asyncio
    async def test_duplicate_request_returns_cached(self, store):
        """Duplicate requests return cached response."""
        # First request - process and cache
        first_response = CachedResponse(
            status_code=200,
            body='{"processed": true}',
            headers={"X-Request-Id": "first"},
            processed_at=datetime.utcnow().isoformat(),
            idempotency_key="payment-123"
        )
        await store.set("payment-123", first_response)

        # Second request - should get cached
        cached = await store.get("payment-123")
        assert cached is not None
        assert cached.body == '{"processed": true}'
        assert cached.headers["X-Request-Id"] == "first"

    @pytest.mark.asyncio
    async def test_different_keys_processed_separately(self, store):
        """Different keys are processed independently."""
        response1 = CachedResponse(
            status_code=200,
            body="response-1",
            headers={},
            processed_at="",
            idempotency_key="key-1"
        )
        response2 = CachedResponse(
            status_code=200,
            body="response-2",
            headers={},
            processed_at="",
            idempotency_key="key-2"
        )

        await store.set("key-1", response1)
        await store.set("key-2", response2)

        result1 = await store.get("key-1")
        result2 = await store.get("key-2")

        assert result1.body == "response-1"
        assert result2.body == "response-2"

    @pytest.mark.asyncio
    async def test_concurrent_lock_prevents_duplicate(self, store):
        """Concurrent requests for same key are serialized via lock."""
        # First request acquires lock
        lock1 = await store.acquire_lock("payment-456")
        assert lock1 is True

        # Concurrent request cannot acquire
        lock2 = await store.acquire_lock("payment-456")
        assert lock2 is False

        # After release, next request can proceed
        await store.release_lock("payment-456")
        lock3 = await store.acquire_lock("payment-456")
        assert lock3 is True


class TestCachedResponse:
    """Test CachedResponse data class."""

    def test_to_dict(self):
        """Can convert to dictionary."""
        response = CachedResponse(
            status_code=200,
            body="test",
            headers={"X-Test": "value"},
            processed_at="2024-01-01T00:00:00",
            idempotency_key="key-123"
        )

        d = response.to_dict()
        assert d["status_code"] == 200
        assert d["body"] == "test"
        assert d["headers"]["X-Test"] == "value"

    def test_from_dict(self):
        """Can create from dictionary."""
        d = {
            "status_code": 200,
            "body": "test",
            "headers": {"X-Test": "value"},
            "processed_at": "2024-01-01T00:00:00",
            "idempotency_key": "key-123"
        }

        response = CachedResponse.from_dict(d)
        assert response.status_code == 200
        assert response.body == "test"
        assert response.headers["X-Test"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
