# Webhook Idempotency Pattern

**CRITICAL RULE: EVERY webhook handler MUST be idempotent.**

This pattern ensures webhooks are processed exactly once, even when:
- The sender retries the webhook
- Network issues cause duplicate delivery
- Your handler fails partway through

## Why This Matters

Webhooks are inherently unreliable. Payment processors like Stripe guarantee
"at least once" delivery, meaning you WILL receive duplicates. Without
idempotency:

```
1. Stripe sends payment.success webhook
2. Your handler processes payment, credits user
3. Your handler crashes before sending 200 response
4. Stripe retries webhook (thinking it failed)
5. Your handler processes AGAIN, double-credits user!
```

With idempotency:

```
1. Stripe sends payment.success webhook
2. Your handler processes payment, credits user, caches response
3. Your handler crashes before sending 200 response
4. Stripe retries webhook
5. Your handler sees cached response, returns it immediately (no double-credit)
```

## Installation

Copy the `webhook-idempotency` directory to your project's `lib/` or add to Python path.

## Quick Start

### Option 1: Decorator (Recommended)

```python
from fastapi import FastAPI, Request
from library.patterns.webhook_idempotency import idempotent, InMemoryIdempotencyStore

app = FastAPI()
store = InMemoryIdempotencyStore()  # Use Redis in production!

@app.post("/webhooks/stripe")
@idempotent(store)
async def handle_stripe_webhook(request: Request):
    # This handler runs ONLY ONCE per idempotency key
    payload = await request.json()
    await process_payment(payload)
    return {"status": "processed"}
```

### Option 2: Middleware (Global)

```python
from fastapi import FastAPI
from library.patterns.webhook_idempotency import (
    FastAPIIdempotencyMiddleware,
    RedisIdempotencyStore
)

app = FastAPI()
store = RedisIdempotencyStore("redis://localhost:6379")

app.add_middleware(
    FastAPIIdempotencyMiddleware,
    store=store,
    paths=["/webhooks/", "/api/payments/"]
)
```

### Option 3: Context Manager

```python
from library.patterns.webhook_idempotency import (
    ensure_idempotent,
    InMemoryIdempotencyStore
)

store = InMemoryIdempotencyStore()

async def process_event(event_id: str, payload: dict):
    async with ensure_idempotent(store, event_id) as ctx:
        if ctx.already_processed:
            return ctx.cached_result

        result = await do_expensive_operation(payload)
        ctx.set_result(result)
        return result
```

## Storage Backends

### InMemoryIdempotencyStore (Development Only)

```python
store = InMemoryIdempotencyStore()
```

**Warning**: Data lost on restart. Not suitable for production.

### RedisIdempotencyStore (Recommended for Production)

```python
from library.patterns.webhook_idempotency import RedisIdempotencyStore

store = RedisIdempotencyStore(
    redis_url="redis://localhost:6379",
    prefix="idem:"  # Key prefix for namespacing
)
```

Features:
- Automatic TTL expiration
- Distributed locking (SETNX)
- Multi-process/multi-server safe

### PostgresIdempotencyStore (Alternative Production Option)

```python
from library.patterns.webhook_idempotency import PostgresIdempotencyStore

store = PostgresIdempotencyStore(
    connection_string="postgresql://user:pass@localhost/db",
    table_name="idempotency_keys"
)
```

Required table:
```sql
CREATE TABLE idempotency_keys (
    key VARCHAR(255) PRIMARY KEY,
    response JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_idempotency_expires ON idempotency_keys(expires_at);
```

## Idempotency Keys

### Automatic Generation

When no `Idempotency-Key` header is provided, the pattern generates a key
from the request body hash:

```python
# Request body: {"event_id": "123", "amount": 100}
# Generated key: sha256(body) = "a1b2c3d4..."
```

### Explicit Keys

For better control, pass an explicit key in the header:

```bash
curl -X POST /webhooks/stripe \
  -H "Idempotency-Key: evt_1234567890" \
  -d '{"event": "payment.success"}'
```

### Provider-Specific Keys

Many webhook providers include a unique event ID. Use it as your key:

```python
from library.patterns.webhook_idempotency import extract_stripe_idempotency_key

@app.post("/webhooks/stripe")
async def handle_stripe(request: Request):
    # Uses Stripe's event ID (evt_xxx) as key
    event_id = await extract_stripe_idempotency_key(request)
    # ...
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `key_header` | `"Idempotency-Key"` | HTTP header for idempotency key |
| `ttl_seconds` | `86400` (24h) | How long to cache responses |
| `key_from_body` | `True` | Generate key from body if header missing |
| `methods` | `["POST", "PUT", "PATCH"]` | HTTP methods to apply to |

## Response Caching

Cached responses include a header indicating replay:

```
X-Idempotent-Replay: true
X-Idempotent-Key: a1b2c3d4...
```

Only these status codes are cached:
- 2xx: Successful responses
- 4xx: Client errors (user should fix and retry with new key)

NOT cached:
- 5xx: Server errors (sender should retry with same key)

## Concurrent Request Handling

When two requests with the same key arrive simultaneously:

1. First request acquires lock, starts processing
2. Second request sees lock, returns 409 Conflict immediately

```json
{
    "error": "Request already in progress",
    "idempotency_key": "a1b2c3d4..."
}
```

## Testing

```bash
cd library/patterns/webhook-idempotency
pytest tests/ -v
```

## Integration with Money Handling

Webhook idempotency pairs naturally with the money-handling pattern:

```python
from library.patterns.money_handling import Money
from library.patterns.webhook_idempotency import idempotent

@app.post("/webhooks/payment")
@idempotent(store)
async def handle_payment(request: Request):
    data = await request.json()

    # Use Money class for amount (NEVER float!)
    amount = Money.from_cents(data['amount_cents'])

    await credit_account(data['user_id'], amount)
    return {"credited": str(amount)}
```

## Best Practices

1. **Always use idempotency for**:
   - Payment webhooks
   - Inventory updates
   - Email sending
   - Any operation with side effects

2. **Use Redis/Postgres in production**:
   - In-memory store loses data on restart
   - Distributed locking requires shared storage

3. **Set appropriate TTL**:
   - Too short: Duplicates may slip through
   - Too long: Storage grows unnecessarily
   - 24 hours is a good default

4. **Include idempotency key in logs**:
   - Helps debug duplicate processing issues

5. **Monitor for 409 Conflict responses**:
   - High rates indicate sender issues

## Troubleshooting

### "Request already in progress" (409)

Two requests with same key arrived simultaneously. This is normal - the sender
should retry.

### Duplicate processing despite idempotency

Check:
- Is your store actually persistent (not in-memory in production)?
- Is TTL long enough?
- Are you using the same idempotency key?

### Lock stuck (processing never completes)

Locks auto-expire after timeout (default 30s). If a process crashes, the lock
will eventually release.

## Source

Original implementation for AI Exoskeleton Library Completion Sprint.

## Related Patterns

- `money-handling` - Use together for payment webhooks
- `stripe-integration` - Uses this pattern internally
