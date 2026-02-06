# Auth Domain

Authentication middleware components for web frameworks.

## Components

| Component | Description |
|-----------|-------------|
| `fastapi_jwt/` | FastAPI JWT authentication middleware |
| `jwt_middleware_ts/` | Express JWT authentication middleware (TypeScript) |

## Usage

### FastAPI

```python
from library.components.auth.fastapi_jwt import (
    JWTAuthService,
    get_current_user,
    require_role,
    init_jwt_auth,
)

@router.get('/me')
async def me(user: User = Depends(get_current_user)):
    return user
```

### Express

```typescript
import { JWTAuth, authenticate, requireRole } from '@library/auth/jwt-middleware';

app.use('/api', authenticate({ secret: process.env.JWT_SECRET }));
```

## Related Domains

- `security/` - JWT token generation
