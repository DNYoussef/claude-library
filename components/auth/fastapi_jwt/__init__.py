"""
FastAPI JWT Authentication

Production-ready JWT authentication for FastAPI using dependency injection.

LEGO Component: auth/fastapi-jwt

Quick Start:
    from fastapi import FastAPI, Depends
    from auth.fastapi_jwt import (
        init_jwt_auth,
        JWTAuthConfig,
        get_current_user,
        require_role,
        User
    )

    app = FastAPI()

    @app.on_event("startup")
    async def startup():
        init_jwt_auth(JWTAuthConfig(
            secret_key=os.getenv("JWT_SECRET_KEY"),
            issuer="my-app"
        ))

    @app.get("/protected")
    async def protected(user: User = Depends(get_current_user)):
        return {"user_id": user.id, "email": user.email}

    @app.get("/admin")
    async def admin_only(user: User = Depends(require_role("admin"))):
        return {"admin": True}

Dependencies:
    pip install fastapi python-jose[cryptography]

Integration:
    Integrates with security/jwt-auth for consistent token handling
    across Python services. Use the same secret_key, issuer, and
    audience for cross-service authentication.
"""

from .jwt_auth import (
    # Configuration
    JWTAuthConfig,
    # Data models
    TokenData,
    User,
    # Exceptions
    AuthenticationError,
    AuthorizationError,
    # Service class (for custom setups)
    JWTAuthService,
    # Initialization
    init_jwt_auth,
    get_auth_service,
    # Standalone dependencies
    get_current_user,
    get_current_user_optional,
    require_role,
    require_any_role,
    # BOLA utilities
    verify_resource_ownership,
    verify_resource_ownership_or_admin,
)

__all__ = [
    # Configuration
    "JWTAuthConfig",
    # Data models
    "TokenData",
    "User",
    # Exceptions
    "AuthenticationError",
    "AuthorizationError",
    # Service class
    "JWTAuthService",
    # Initialization
    "init_jwt_auth",
    "get_auth_service",
    # Dependencies
    "get_current_user",
    "get_current_user_optional",
    "require_role",
    "require_any_role",
    # BOLA utilities
    "verify_resource_ownership",
    "verify_resource_ownership_or_admin",
]

__version__ = "1.0.0"
__author__ = "David Youssef"
