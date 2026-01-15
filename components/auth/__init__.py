"""
Authentication Components Library

This package contains reusable authentication components for various frameworks.

Available Components:
    - fastapi_jwt: FastAPI JWT authentication with dependency injection

Related Components:
    - security/jwt-auth: Core JWT token management (token creation/verification)

Usage:
    # FastAPI JWT authentication
    from auth.fastapi_jwt import (
        init_jwt_auth,
        JWTAuthConfig,
        get_current_user,
        require_role,
        User,
    )

    # For TypeScript Express, see auth/jwt-middleware-ts/

Architecture:
    - fastapi-jwt: Token VERIFICATION and user extraction (FastAPI routes)
    - security/jwt-auth: Token CREATION and management (login endpoints)

    These components work together for complete JWT authentication.
"""

__all__ = ["fastapi_jwt"]
