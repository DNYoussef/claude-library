# Security Domain

Components for authentication, authorization, and security.

## Components

| Component | Description |
|-----------|-------------|
| `jwt_auth/` | JWT token generation and validation |

## Usage

```python
from library.components.security.jwt_auth import (
    JWTAuth,
    TokenConfig,
    Claims,
    generate_token,
    verify_token,
)
```

## Related Domains

- `auth/` - Authentication middleware (FastAPI, Express)
