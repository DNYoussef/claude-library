"""
Multi-Entity Tenant Isolation Component

Row-Level Security (RLS) based tenant isolation for SQLAlchemy applications.
Enforces data separation at the database level for multi-tenant SaaS.

Based on:
- sqlalchemy-tenants: https://github.com/Telemaco019/sqlalchemy-tenants
- PostgreSQL RLS patterns: https://atlasgo.io/guides/orms/sqlalchemy/row-level-security

Features:
- Automatic tenant_id injection on queries
- Row-Level Security policy helpers
- SQLAlchemy event-based isolation
- Context-based tenant resolution
- Compatible with FastAPI/Starlette middleware

Example:
    from library.components.multi_entity.isolation import (
        TenantContext,
        TenantMixin,
        enable_rls,
    )

    class Project(TenantMixin, Base):
        __tablename__ = "projects"
        name = Column(String)

    # In request middleware
    with TenantContext(tenant_id="tenant_123"):
        projects = session.query(Project).all()  # Auto-filtered by tenant
"""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from sqlalchemy import Column, String, event, text
from sqlalchemy.orm import Session, Query
from sqlalchemy.engine import Engine, Connection

# Context variable for current tenant
_current_tenant: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_tenant", default=None
)

T = TypeVar("T")


# =============================================================================
# TENANT CONTEXT
# =============================================================================


def get_current_tenant() -> Optional[str]:
    """Get the current tenant ID from context."""
    return _current_tenant.get()


def set_current_tenant(tenant_id: Optional[str]) -> contextvars.Token:
    """Set the current tenant ID in context."""
    return _current_tenant.set(tenant_id)


@contextmanager
def TenantContext(tenant_id: str):
    """
    Context manager for tenant-scoped operations.

    All database operations within this context will be automatically
    filtered/scoped to the specified tenant.

    Example:
        with TenantContext("tenant_123"):
            # All queries here are tenant-scoped
            projects = session.query(Project).all()
            session.add(Project(name="New Project"))  # tenant_id auto-set

    Args:
        tenant_id: The tenant identifier
    """
    token = set_current_tenant(tenant_id)
    try:
        yield
    finally:
        _current_tenant.reset(token)


def require_tenant(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that requires a tenant context.

    Raises:
        RuntimeError: If no tenant is set in context
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        if get_current_tenant() is None:
            raise RuntimeError(
                f"Function {func.__name__} requires a tenant context. "
                "Use TenantContext() or set_current_tenant() first."
            )
        return func(*args, **kwargs)
    return wrapper


# =============================================================================
# TENANT MIXIN
# =============================================================================


class TenantMixin:
    """
    Mixin for SQLAlchemy models that require tenant isolation.

    Adds a tenant_id column and integrates with the tenant context
    for automatic filtering.

    Example:
        class Project(TenantMixin, Base):
            __tablename__ = "projects"
            id = Column(Integer, primary_key=True)
            name = Column(String)

        # tenant_id column is automatically added
    """

    # Override in subclass if needed
    __tenant_id_column__ = "tenant_id"
    __tenant_id_nullable__ = False

    tenant_id: str = Column(
        String(64),
        nullable=False,
        index=True,
        doc="Tenant identifier for row-level isolation",
    )


# =============================================================================
# SQLALCHEMY EVENT HOOKS
# =============================================================================


def setup_tenant_isolation(session_class: Type[Session]):
    """
    Configure SQLAlchemy session for automatic tenant isolation.

    This sets up event listeners that:
    1. Inject tenant_id on INSERT
    2. Filter queries by tenant_id
    3. Set PostgreSQL session variable for RLS

    Args:
        session_class: The SQLAlchemy Session class to configure

    Example:
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        setup_tenant_isolation(Session)
    """
    @event.listens_for(session_class, "do_orm_execute")
    def _filter_by_tenant(orm_execute_state):
        """Add tenant filter to all SELECT queries."""
        if not orm_execute_state.is_select:
            return

        tenant_id = get_current_tenant()
        if tenant_id is None:
            return

        # Add WHERE clause for tenant_id
        mapper = orm_execute_state.bind_mapper
        if not mapper or not hasattr(mapper.class_, "tenant_id"):
            return

        orm_execute_state.statement = orm_execute_state.statement.filter(
            mapper.class_.tenant_id == tenant_id
        )

    @event.listens_for(session_class, "before_flush")
    def _inject_tenant_id(session, flush_context, instances):
        """Set tenant_id on new objects before INSERT."""
        tenant_id = get_current_tenant()
        if tenant_id is None:
            return

        for obj in session.new:
            if hasattr(obj, "tenant_id") and obj.tenant_id is None:
                obj.tenant_id = tenant_id


def setup_rls_session(engine: Engine):
    """
    Configure engine to set PostgreSQL session variable for RLS.

    This is required when using PostgreSQL Row-Level Security policies
    that reference current_setting('app.current_tenant').

    Args:
        engine: SQLAlchemy Engine

    Example:
        engine = create_engine("postgresql://...")
        setup_rls_session(engine)

        # PostgreSQL RLS policy:
        # CREATE POLICY tenant_isolation ON projects
        #   USING (tenant_id = current_setting('app.current_tenant')::text);
    """
    @event.listens_for(engine, "before_cursor_execute")
    def _set_tenant_variable(
        conn, cursor, statement, parameters, context, executemany
    ):
        """Set PostgreSQL session variable before each query."""
        tenant_id = get_current_tenant()
        if tenant_id is not None:
            cursor.execute(
                "SET LOCAL app.current_tenant = %s",
                (tenant_id,)
            )


# =============================================================================
# RLS POLICY HELPERS
# =============================================================================


@dataclass
class RLSPolicy:
    """
    Represents a PostgreSQL Row-Level Security policy.

    Example:
        policy = RLSPolicy(
            table="projects",
            name="tenant_isolation",
            using="tenant_id = current_setting('app.current_tenant')::text",
        )
        policy.to_sql()  # Returns CREATE POLICY statement
    """

    table: str
    name: str
    using: str  # USING clause for SELECT/UPDATE/DELETE
    with_check: Optional[str] = None  # WITH CHECK for INSERT/UPDATE
    command: str = "ALL"  # ALL, SELECT, INSERT, UPDATE, DELETE
    role: str = "PUBLIC"

    def to_sql(self) -> str:
        """Generate CREATE POLICY SQL statement."""
        sql = f"CREATE POLICY {self.name} ON {self.table}"
        sql += f" FOR {self.command}"
        sql += f" TO {self.role}"
        sql += f" USING ({self.using})"
        if self.with_check:
            sql += f" WITH CHECK ({self.with_check})"
        return sql

    def drop_sql(self) -> str:
        """Generate DROP POLICY SQL statement."""
        return f"DROP POLICY IF EXISTS {self.name} ON {self.table}"


def enable_rls(table_name: str) -> str:
    """Generate SQL to enable RLS on a table."""
    return f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"


def disable_rls(table_name: str) -> str:
    """Generate SQL to disable RLS on a table."""
    return f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY"


def force_rls(table_name: str) -> str:
    """Generate SQL to force RLS for table owner too."""
    return f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY"


def create_tenant_policy(table_name: str, tenant_column: str = "tenant_id") -> RLSPolicy:
    """
    Create a standard tenant isolation policy.

    Args:
        table_name: Name of the table
        tenant_column: Column containing tenant ID

    Returns:
        RLSPolicy configured for tenant isolation
    """
    return RLSPolicy(
        table=table_name,
        name=f"{table_name}_tenant_isolation",
        using=f"{tenant_column} = current_setting('app.current_tenant')::text",
        with_check=f"{tenant_column} = current_setting('app.current_tenant')::text",
    )


def generate_rls_migration(
    tables: List[str],
    tenant_column: str = "tenant_id",
) -> Dict[str, str]:
    """
    Generate RLS migration SQL for multiple tables.

    Args:
        tables: List of table names
        tenant_column: Column containing tenant ID

    Returns:
        Dict with 'upgrade' and 'downgrade' SQL

    Example:
        migration = generate_rls_migration(["projects", "tasks", "users"])
        print(migration["upgrade"])
    """
    upgrade_lines = []
    downgrade_lines = []

    for table in tables:
        policy = create_tenant_policy(table, tenant_column)

        # Enable RLS
        upgrade_lines.append(enable_rls(table))
        upgrade_lines.append(force_rls(table))
        upgrade_lines.append(policy.to_sql())

        # Downgrade
        downgrade_lines.append(policy.drop_sql())
        downgrade_lines.append(disable_rls(table))

    return {
        "upgrade": ";\n".join(upgrade_lines) + ";",
        "downgrade": ";\n".join(downgrade_lines) + ";",
    }


# =============================================================================
# MIDDLEWARE HELPERS
# =============================================================================


def extract_tenant_from_header(
    request: Any,
    header_name: str = "X-Tenant-ID",
) -> Optional[str]:
    """
    Extract tenant ID from request header.

    Args:
        request: HTTP request object (FastAPI, Starlette, etc.)
        header_name: Header containing tenant ID

    Returns:
        Tenant ID or None
    """
    return request.headers.get(header_name)


def extract_tenant_from_subdomain(
    request: Any,
    base_domain: str,
) -> Optional[str]:
    """
    Extract tenant ID from subdomain.

    Args:
        request: HTTP request object
        base_domain: Base domain (e.g., "example.com")

    Returns:
        Tenant ID (subdomain) or None

    Example:
        # Request to tenant1.example.com
        tenant = extract_tenant_from_subdomain(request, "example.com")
        # Returns "tenant1"
    """
    host = request.headers.get("host", "")
    if host.endswith(f".{base_domain}"):
        return host[: -len(f".{base_domain}")]
    return None


def extract_tenant_from_path(
    request: Any,
    prefix: str = "/tenant/",
) -> Optional[str]:
    """
    Extract tenant ID from URL path.

    Args:
        request: HTTP request object
        prefix: Path prefix before tenant ID

    Returns:
        Tenant ID or None

    Example:
        # Request to /tenant/tenant1/projects
        tenant = extract_tenant_from_path(request, "/tenant/")
        # Returns "tenant1"
    """
    path = request.url.path
    if path.startswith(prefix):
        remaining = path[len(prefix):]
        tenant_id = remaining.split("/")[0]
        return tenant_id if tenant_id else None
    return None


# =============================================================================
# FASTAPI MIDDLEWARE
# =============================================================================


class TenantMiddleware:
    """
    ASGI middleware for tenant context management.

    Example:
        from fastapi import FastAPI
        from library.components.multi_entity.isolation import TenantMiddleware

        app = FastAPI()
        app.add_middleware(
            TenantMiddleware,
            tenant_resolver=lambda r: r.headers.get("X-Tenant-ID"),
        )
    """

    def __init__(
        self,
        app,
        tenant_resolver: Callable[[Any], Optional[str]],
        require_tenant: bool = False,
    ):
        """
        Args:
            app: ASGI application
            tenant_resolver: Function to extract tenant from request
            require_tenant: If True, reject requests without tenant
        """
        self.app = app
        self.tenant_resolver = tenant_resolver
        self.require_tenant = require_tenant

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create a minimal request object for resolver
        class Request:
            def __init__(self, scope):
                self.headers = dict(scope.get("headers", []))
                # Decode header names/values
                self.headers = {
                    k.decode() if isinstance(k, bytes) else k:
                    v.decode() if isinstance(v, bytes) else v
                    for k, v in self.headers.items()
                }
                self.url = type("URL", (), {"path": scope.get("path", "/")})()

        request = Request(scope)
        tenant_id = self.tenant_resolver(request)

        if self.require_tenant and tenant_id is None:
            # Return 400 Bad Request
            response_body = b'{"detail": "Tenant ID required"}'
            await send({
                "type": "http.response.start",
                "status": 400,
                "headers": [(b"content-type", b"application/json")],
            })
            await send({
                "type": "http.response.body",
                "body": response_body,
            })
            return

        # Set tenant context and call app
        with TenantContext(tenant_id) if tenant_id else nullcontext():
            await self.app(scope, receive, send)


@contextmanager
def nullcontext():
    """Null context manager for when no tenant is set."""
    yield
