"""
Multi-Entity Tenant Isolation Component

Row-Level Security (RLS) based tenant isolation for SQLAlchemy applications.

References:
- https://github.com/Telemaco019/sqlalchemy-tenants
- https://atlasgo.io/guides/orms/sqlalchemy/row-level-security

Example:
    from library.components.multi_entity.isolation import (
        TenantContext,
        TenantMixin,
        setup_tenant_isolation,
    )

    class Project(TenantMixin, Base):
        __tablename__ = "projects"
        name = Column(String)

    # In request middleware
    with TenantContext(tenant_id="tenant_123"):
        projects = session.query(Project).all()  # Auto-filtered
"""

from .tenant import (
    # Context management
    TenantContext,
    get_current_tenant,
    set_current_tenant,
    require_tenant,
    # Mixin
    TenantMixin,
    # SQLAlchemy setup
    setup_tenant_isolation,
    setup_rls_session,
    # RLS helpers
    RLSPolicy,
    enable_rls,
    disable_rls,
    force_rls,
    create_tenant_policy,
    generate_rls_migration,
    # Request helpers
    extract_tenant_from_header,
    extract_tenant_from_subdomain,
    extract_tenant_from_path,
    # Middleware
    TenantMiddleware,
)

__all__ = [
    # Context management
    "TenantContext",
    "get_current_tenant",
    "set_current_tenant",
    "require_tenant",
    # Mixin
    "TenantMixin",
    # SQLAlchemy setup
    "setup_tenant_isolation",
    "setup_rls_session",
    # RLS helpers
    "RLSPolicy",
    "enable_rls",
    "disable_rls",
    "force_rls",
    "create_tenant_policy",
    "generate_rls_migration",
    # Request helpers
    "extract_tenant_from_header",
    "extract_tenant_from_subdomain",
    "extract_tenant_from_path",
    # Middleware
    "TenantMiddleware",
]
