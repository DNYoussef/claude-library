# FastAPI JWT Authentication

Production-ready JWT authentication for FastAPI using dependency injection.

## Features

- FastAPI dependency injection pattern for clean route protection
- Role-based access control (single role or any-of-roles)
- Optional authentication for public endpoints with user context
- BOLA (Broken Object Level Authorization) mitigation utilities
- Integrates with `security/jwt-auth` for token creation

## Installation

```bash
pip install fastapi python-jose[cryptography]
```

## Quick Start

```python
import os
from fastapi import FastAPI, Depends
from auth.fastapi_jwt import (
    init_jwt_auth,
    JWTAuthConfig,
    get_current_user,
    get_current_user_optional,
    require_role,
    require_any_role,
    User,
)

app = FastAPI()

# Initialize at startup
@app.on_event("startup")
async def startup():
    init_jwt_auth(JWTAuthConfig(
        secret_key=os.getenv("JWT_SECRET_KEY"),
        issuer="my-app",
        audience="my-app-users",
    ))

# Protected route
@app.get("/api/profile")
async def get_profile(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
    }

# Admin-only route
@app.get("/api/admin/users")
async def get_all_users(user: User = Depends(require_role("admin"))):
    return {"admin": True}

# Multiple roles allowed (any match)
@app.get("/api/staff/dashboard")
async def staff_dashboard(user: User = Depends(require_any_role(["admin", "manager"]))):
    return {"staff": True}

# Optional auth (public with user context)
@app.get("/api/posts")
async def get_posts(user: Optional[User] = Depends(get_current_user_optional)):
    if user:
        # Return personalized content
        pass
    return {"posts": []}
```

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `secret_key` | str | required | HMAC signing key (min 32 chars) |
| `algorithm` | str | "HS256" | JWT algorithm |
| `issuer` | str | None | Token issuer claim |
| `audience` | str | None | Token audience claim |
| `access_token_expire_minutes` | int | 30 | Access token lifetime |
| `refresh_token_expire_days` | int | 7 | Refresh token lifetime |

## Usage Patterns

### Pattern 1: Global Service (Recommended)

```python
# Initialize once at startup
init_jwt_auth(JWTAuthConfig(secret_key=os.getenv("JWT_SECRET")))

# Use standalone dependencies
@app.get("/protected")
async def protected(user: User = Depends(get_current_user)):
    return {"user": user}
```

### Pattern 2: Explicit Service Instance

```python
# Create service manually
auth_service = JWTAuthService(JWTAuthConfig(
    secret_key=os.getenv("JWT_SECRET")
))

# Use service methods as dependencies
@app.get("/protected")
async def protected(user: User = Depends(auth_service.get_current_user)):
    return {"user": user}
```

### Pattern 3: Router with Dependencies

```python
from fastapi import APIRouter

router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(require_role("admin"))],
)

@router.get("/users")
async def get_users():
    # All routes in this router require admin role
    return {"users": []}
```

## BOLA Mitigation

Prevent Broken Object Level Authorization attacks:

```python
from auth.fastapi_jwt import verify_resource_ownership, verify_resource_ownership_or_admin

@app.get("/users/{user_id}/profile")
async def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    # Users can only access their own profile
    verify_resource_ownership(current_user.id, user_id)
    return {"profile": ...}

@app.put("/users/{user_id}/settings")
async def update_settings(
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    # Users can edit their own, admins can edit any
    verify_resource_ownership_or_admin(current_user, user_id)
    return {"updated": True}
```

## Integration with security/jwt-auth

This component handles **token verification and user extraction**. For **token creation**, use `security/jwt-auth`:

```python
from security.jwt_auth import JWTAuth, JWTConfig

# Token creation service
jwt_auth = JWTAuth(JWTConfig(
    secret_key=os.getenv("JWT_SECRET_KEY"),
    issuer="my-app",
    audience="my-app-users",
))

@app.post("/auth/login")
async def login(credentials: LoginRequest):
    user = await authenticate_user(credentials)

    # Create tokens using security/jwt-auth
    access_token = jwt_auth.create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    })
    refresh_token = jwt_auth.create_refresh_token({
        "sub": str(user.id),
    })

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@app.post("/auth/refresh")
async def refresh(request: RefreshRequest):
    # Use security/jwt-auth for refresh
    new_access = jwt_auth.refresh_access_token(request.refresh_token)
    if not new_access:
        raise HTTPException(401, "Invalid refresh token")
    return {"access_token": new_access}
```

## User Model

```python
@dataclass
class User:
    id: Union[int, str]
    email: str
    role: str = "user"
    name: Optional[str] = None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def has_role(self, role: str) -> bool:
        return self.role == role

    def has_any_role(self, roles: List[str]) -> bool:
        return self.role in roles
```

## Error Handling

```python
from auth.fastapi_jwt import AuthenticationError, AuthorizationError

@app.exception_handler(AuthenticationError)
async def auth_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "authentication_failed", "message": exc.detail},
    )

@app.exception_handler(AuthorizationError)
async def authz_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "authorization_failed", "message": exc.detail},
    )
```

## Security Best Practices

1. **Environment Variables**: Never hardcode secrets
2. **HTTPS Only**: Always use HTTPS in production
3. **Short-Lived Tokens**: Use 15-30 minute access tokens
4. **Refresh Rotation**: Rotate refresh tokens on use
5. **BOLA Checks**: Always verify resource ownership
6. **Logging**: Log failed authentication attempts
