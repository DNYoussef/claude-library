"""
FastAPI JWT Authentication Dependencies

Production-ready JWT authentication for FastAPI using dependency injection.
Integrates with library.components.security.jwt_auth for token operations.

LEGO Component: auth/fastapi-jwt

Usage:
    from fastapi import Depends
    from auth.fastapi_jwt import get_current_user, require_role, User

    @app.get("/protected")
    async def protected_route(user: User = Depends(get_current_user)):
        return {"user_id": user.id, "email": user.email}

    @app.get("/admin")
    async def admin_route(user: User = Depends(require_role("admin"))):
        return {"admin": True}

Dependencies:
    pip install fastapi python-jose[cryptography]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

# Use library common types where applicable
# REQUIRED: Copy common/types.py alongside this component for standalone use
try:
    from library.common.types import Severity
except ImportError:
    from common.types import Severity


logger = logging.getLogger(__name__)

# HTTP Bearer token scheme (auto_error=True for required, False for optional)
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class JWTAuthConfig:
    """
    JWT Authentication configuration.

    Load from environment variables in production:
        config = JWTAuthConfig(
            secret_key=os.getenv("JWT_SECRET_KEY"),
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        )

    Attributes:
        secret_key: Secret for signing/verifying tokens. Min 32 chars for HS256.
        algorithm: JWT algorithm (default: HS256)
        issuer: Optional token issuer claim
        audience: Optional token audience claim
        access_token_expire_minutes: Access token lifetime (default: 30)
        refresh_token_expire_days: Refresh token lifetime (default: 7)
    """

    secret_key: str
    algorithm: str = "HS256"
    issuer: Optional[str] = None
    audience: Optional[str] = None
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    def __post_init__(self) -> None:
        if not self.secret_key:
            raise ValueError("secret_key is required")
        if len(self.secret_key) < 32:
            raise ValueError(
                f"secret_key must be at least 32 characters for {self.algorithm} security"
            )


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class TokenData:
    """Decoded JWT token payload."""

    user_id: Union[int, str]
    email: str
    exp: datetime
    role: str = "user"
    name: Optional[str] = None
    token_type: str = "access"
    jti: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class User:
    """
    Authenticated user model.

    Represents the current user extracted from a valid JWT token.
    Used as the return type for authentication dependencies.
    """

    id: Union[int, str]
    email: str
    role: str = "user"
    name: Optional[str] = None

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"

    def has_role(self, role: str) -> bool:
        """Check if user has specific role."""
        return self.role == role

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return self.role in roles


# =============================================================================
# EXCEPTIONS
# =============================================================================


class AuthenticationError(HTTPException):
    """
    Authentication error (401 Unauthorized).

    Raised when token is missing, invalid, or expired.
    """

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """
    Authorization error (403 Forbidden).

    Raised when user lacks required permissions.
    """

    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


# =============================================================================
# JWT AUTHENTICATION SERVICE
# =============================================================================


class JWTAuthService:
    """
    JWT Authentication Service.

    Handles token verification and user extraction for FastAPI.
    Use with dependency injection for clean route protection.

    Example:
        auth_service = JWTAuthService(config)

        @app.get("/protected")
        async def protected(user: User = Depends(auth_service.get_current_user)):
            return {"user": user}
    """

    def __init__(self, config: JWTAuthConfig):
        """
        Initialize JWT authentication service.

        Args:
            config: JWT configuration with secret key and settings
        """
        self.config = config
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def verify_token(
        self, token: str, expected_type: str = "access"
    ) -> Optional[TokenData]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string
            expected_type: Expected token type ('access' or 'refresh')

        Returns:
            TokenData if valid, None if invalid

        Security:
            - Validates signature
            - Checks expiration
            - Verifies issuer (if configured)
            - Verifies audience (if configured)
            - Checks token type to prevent confusion attacks
        """
        try:
            # Build decode options
            options: Dict[str, Any] = {}
            if self.config.issuer:
                options["verify_iss"] = True
            if self.config.audience:
                options["verify_aud"] = True

            # Decode and verify
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer if self.config.issuer else None,
                audience=self.config.audience if self.config.audience else None,
                options=options,
            )

            # Check token type
            token_type = payload.get("type", "access")
            if token_type != expected_type:
                self._logger.warning(
                    f"Token type mismatch: expected {expected_type}, got {token_type}"
                )
                return None

            # Extract user ID (support both 'sub' and 'user_id')
            user_id = payload.get("sub") or payload.get("user_id")
            if user_id is None:
                self._logger.warning("Token missing user identifier")
                return None

            # Extract email
            email = payload.get("email", "")

            # Extract expiration
            exp_timestamp = payload.get("exp")
            exp = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else datetime.utcnow()

            # Build extra claims (non-standard)
            excluded_keys = {"sub", "user_id", "email", "exp", "iat", "type", "jti", "iss", "aud", "role", "name"}
            extra = {k: v for k, v in payload.items() if k not in excluded_keys}

            return TokenData(
                user_id=user_id,
                email=email,
                exp=exp,
                role=payload.get("role", "user"),
                name=payload.get("name"),
                token_type=token_type,
                jti=payload.get("jti"),
                extra=extra,
            )

        except JWTError as e:
            self._logger.warning(f"JWT verification failed: {e}")
            return None

    def extract_user(self, token_data: TokenData) -> User:
        """
        Extract User from TokenData.

        Args:
            token_data: Verified token data

        Returns:
            User instance
        """
        return User(
            id=token_data.user_id,
            email=token_data.email,
            role=token_data.role,
            name=token_data.name,
        )

    # =========================================================================
    # DEPENDENCY INJECTION METHODS
    # =========================================================================

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> User:
        """
        FastAPI dependency to get current authenticated user.

        Usage:
            @app.get("/protected")
            async def protected(user: User = Depends(auth_service.get_current_user)):
                return {"user_id": user.id}

        Raises:
            AuthenticationError: If token is invalid or expired
        """
        token = credentials.credentials
        token_data = self.verify_token(token, expected_type="access")

        if not token_data:
            raise AuthenticationError("Invalid or expired token")

        return self.extract_user(token_data)

    async def get_current_user_optional(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    ) -> Optional[User]:
        """
        FastAPI dependency to optionally get current user.

        Returns None if no token provided (does not raise error).
        Useful for public endpoints with optional personalization.

        Usage:
            @app.get("/posts")
            async def get_posts(user: Optional[User] = Depends(auth_service.get_current_user_optional)):
                if user:
                    # Personalized response
                    pass
                return {"posts": []}
        """
        if not credentials:
            return None

        try:
            token_data = self.verify_token(credentials.credentials, expected_type="access")
            if token_data:
                return self.extract_user(token_data)
        except Exception:
            pass

        return None

    def require_role(self, required_role: str) -> Callable:
        """
        Dependency factory for role-based access control.

        Usage:
            @app.get("/admin/users")
            async def get_all_users(user: User = Depends(auth_service.require_role("admin"))):
                return {"admin": True}

        Args:
            required_role: Required user role

        Returns:
            FastAPI dependency function
        """

        async def role_checker(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ) -> User:
            user = await self.get_current_user(credentials)
            if user.role != required_role:
                raise AuthorizationError(f"Role '{required_role}' required")
            return user

        return role_checker

    def require_any_role(self, required_roles: List[str]) -> Callable:
        """
        Dependency factory for role-based access control (any role matches).

        Usage:
            @app.get("/staff/dashboard")
            async def staff_dashboard(
                user: User = Depends(auth_service.require_any_role(["admin", "manager"]))
            ):
                return {"staff": True}

        Args:
            required_roles: List of acceptable roles (user must have at least one)

        Returns:
            FastAPI dependency function
        """

        async def role_checker(
            credentials: HTTPAuthorizationCredentials = Depends(security),
        ) -> User:
            user = await self.get_current_user(credentials)
            if user.role not in required_roles:
                roles_str = ", ".join(required_roles)
                raise AuthorizationError(f"One of roles required: {roles_str}")
            return user

        return role_checker


# =============================================================================
# STANDALONE DEPENDENCY FUNCTIONS
# =============================================================================

# Global service instance (configure via init_jwt_auth)
_auth_service: Optional[JWTAuthService] = None


def init_jwt_auth(config: JWTAuthConfig) -> JWTAuthService:
    """
    Initialize the global JWT authentication service.

    Call this at application startup:
        from fastapi import FastAPI
        from auth.fastapi_jwt import init_jwt_auth, JWTAuthConfig

        app = FastAPI()

        @app.on_event("startup")
        async def startup():
            init_jwt_auth(JWTAuthConfig(
                secret_key=os.getenv("JWT_SECRET_KEY"),
                issuer="my-app"
            ))

    Args:
        config: JWT authentication configuration

    Returns:
        Configured JWTAuthService instance
    """
    global _auth_service
    _auth_service = JWTAuthService(config)
    logger.info("JWT authentication service initialized")
    return _auth_service


def get_auth_service() -> JWTAuthService:
    """Get the global JWT authentication service."""
    if _auth_service is None:
        raise RuntimeError(
            "JWT auth service not initialized. Call init_jwt_auth() at startup."
        )
    return _auth_service


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    FastAPI dependency to get current authenticated user.

    Requires init_jwt_auth() to be called at startup.

    Usage:
        @app.get("/protected")
        async def protected(user: User = Depends(get_current_user)):
            return {"user_id": user.id}

    Raises:
        AuthenticationError: If token is invalid or expired
        RuntimeError: If init_jwt_auth() was not called
    """
    service = get_auth_service()
    return await service.get_current_user(credentials)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
) -> Optional[User]:
    """
    FastAPI dependency to optionally get current user.

    Returns None if no token (does not raise error).

    Usage:
        @app.get("/posts")
        async def get_posts(user: Optional[User] = Depends(get_current_user_optional)):
            if user:
                # Personalized
                pass
            return {"posts": []}
    """
    service = get_auth_service()
    return await service.get_current_user_optional(credentials)


def require_role(required_role: str) -> Callable:
    """
    Dependency factory for role-based access control.

    Usage:
        @app.get("/admin/users")
        async def get_all_users(user: User = Depends(require_role("admin"))):
            return {"users": []}

    Args:
        required_role: Required user role

    Returns:
        FastAPI dependency function
    """
    service = get_auth_service()
    return service.require_role(required_role)


def require_any_role(required_roles: List[str]) -> Callable:
    """
    Dependency factory for role-based access control (any role matches).

    Usage:
        @app.get("/staff")
        async def staff(user: User = Depends(require_any_role(["admin", "manager"]))):
            return {"staff": True}

    Args:
        required_roles: List of acceptable roles

    Returns:
        FastAPI dependency function
    """
    service = get_auth_service()
    return service.require_any_role(required_roles)


# =============================================================================
# BOLA MITIGATION UTILITIES
# =============================================================================


def verify_resource_ownership(user_id: Union[int, str], resource_user_id: Union[int, str]) -> None:
    """
    OWASP API1:2023 - Broken Object Level Authorization (BOLA) mitigation.

    Verify that the current user owns the requested resource.

    Usage:
        @app.get("/users/{user_id}/profile")
        async def get_profile(
            user_id: int,
            current_user: User = Depends(get_current_user)
        ):
            verify_resource_ownership(current_user.id, user_id)
            return {"profile": ...}

    Args:
        user_id: Current authenticated user ID
        resource_user_id: User ID associated with the resource

    Raises:
        AuthorizationError: If user doesn't own the resource
    """
    # Normalize to string for comparison
    if str(user_id) != str(resource_user_id):
        logger.warning(
            f"BOLA attempt: user {user_id} tried to access resource of user {resource_user_id}"
        )
        raise AuthorizationError("You do not have permission to access this resource")


def verify_resource_ownership_or_admin(
    user: User, resource_user_id: Union[int, str]
) -> None:
    """
    Verify resource ownership OR admin role.

    Allows admins to access any resource while regular users
    can only access their own resources.

    Args:
        user: Current authenticated user
        resource_user_id: User ID associated with the resource

    Raises:
        AuthorizationError: If user doesn't own resource and isn't admin
    """
    if user.is_admin:
        return

    if str(user.id) != str(resource_user_id):
        logger.warning(
            f"BOLA attempt: user {user.id} tried to access resource of user {resource_user_id}"
        )
        raise AuthorizationError("You do not have permission to access this resource")
from functools import lru_cache
