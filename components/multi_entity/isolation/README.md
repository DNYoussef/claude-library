# Multi-Entity Tenant Isolation Component

Row-Level Security (RLS) based tenant isolation for SQLAlchemy applications. Enforces data separation at the database level for multi-tenant SaaS.

## Features

- Automatic tenant_id injection on queries
- Row-Level Security policy helpers for PostgreSQL
- SQLAlchemy event-based isolation
- Context-based tenant resolution
- ASGI middleware for FastAPI/Starlette
- Multiple tenant resolution strategies (header, subdomain, path)

## Usage

### Basic Setup

```python
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from library.components.multi_entity.isolation import (
    TenantMixin,
    TenantContext,
    setup_tenant_isolation,
)

Base = declarative_base()

# Add TenantMixin to models that need isolation
class Project(TenantMixin, Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String)

# Configure session
engine = create_engine("postgresql://...")
Session = sessionmaker(bind=engine)
setup_tenant_isolation(Session)

# Use with tenant context
with TenantContext("tenant_123"):
    session = Session()

    # Query automatically filtered by tenant_id
    projects = session.query(Project).all()

    # New records get tenant_id automatically
    session.add(Project(name="New Project"))
    session.commit()
```

### PostgreSQL Row-Level Security

For stronger isolation at the database level:

```python
from library.components.multi_entity.isolation import (
    setup_rls_session,
    generate_rls_migration,
)

# Configure engine for RLS
setup_rls_session(engine)

# Generate migration SQL
migration = generate_rls_migration(["projects", "tasks", "users"])
print(migration["upgrade"])
```

Generated SQL:
```sql
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects FORCE ROW LEVEL SECURITY;
CREATE POLICY projects_tenant_isolation ON projects
    FOR ALL TO PUBLIC
    USING (tenant_id = current_setting('app.current_tenant')::text)
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::text);
-- Same for tasks, users...
```

### FastAPI Middleware

```python
from fastapi import FastAPI, Depends
from library.components.multi_entity.isolation import (
    TenantMiddleware,
    extract_tenant_from_header,
    get_current_tenant,
)

app = FastAPI()

# Add middleware
app.add_middleware(
    TenantMiddleware,
    tenant_resolver=lambda r: r.headers.get("x-tenant-id"),
    require_tenant=True,  # Reject requests without tenant
)

@app.get("/projects")
def list_projects():
    tenant = get_current_tenant()
    # Query automatically scoped to tenant
    return {"tenant": tenant, "projects": [...]}
```

### Tenant Resolution Strategies

```python
from library.components.multi_entity.isolation import (
    extract_tenant_from_header,
    extract_tenant_from_subdomain,
    extract_tenant_from_path,
)

# From header: X-Tenant-ID: tenant_123
tenant = extract_tenant_from_header(request, "X-Tenant-ID")

# From subdomain: tenant1.example.com
tenant = extract_tenant_from_subdomain(request, "example.com")

# From path: /tenant/tenant1/projects
tenant = extract_tenant_from_path(request, "/tenant/")
```

### Function Decorator

```python
from library.components.multi_entity.isolation import require_tenant

@require_tenant
def process_data():
    tenant = get_current_tenant()
    # Guaranteed to have tenant context
    ...

# Raises RuntimeError if called outside TenantContext
process_data()  # Error!

with TenantContext("tenant_123"):
    process_data()  # OK
```

## API Reference

### Context Management

```python
# Context manager
with TenantContext(tenant_id: str):
    ...

# Direct access
tenant_id = get_current_tenant() -> Optional[str]
token = set_current_tenant(tenant_id) -> Token

# Decorator
@require_tenant
def my_function(): ...
```

### TenantMixin

```python
class MyModel(TenantMixin, Base):
    __tablename__ = "my_table"
    # tenant_id column automatically added

    # Override column name if needed
    __tenant_id_column__ = "tenant_id"
    __tenant_id_nullable__ = False
```

### SQLAlchemy Setup

```python
# Enable automatic tenant filtering
setup_tenant_isolation(Session)

# Enable PostgreSQL RLS session variable
setup_rls_session(engine)
```

### RLS Policy Helpers

```python
# Generate standard policy
policy = create_tenant_policy("projects", "tenant_id")
print(policy.to_sql())

# Generate migration for multiple tables
migration = generate_rls_migration(["projects", "tasks"])
print(migration["upgrade"])
print(migration["downgrade"])

# Low-level SQL generators
enable_rls("projects")   # ALTER TABLE projects ENABLE ROW LEVEL SECURITY
disable_rls("projects")  # ALTER TABLE projects DISABLE ROW LEVEL SECURITY
force_rls("projects")    # Force RLS for table owner too
```

### TenantMiddleware

```python
app.add_middleware(
    TenantMiddleware,
    tenant_resolver=Callable[[Request], Optional[str]],
    require_tenant=bool,  # Default: False
)
```

## Best Practices

1. **Always use TenantMixin** for tenant-scoped models
2. **Enable PostgreSQL RLS** for database-level enforcement
3. **Use middleware** in web applications for automatic context
4. **Validate tenant access** in critical operations
5. **Test with multiple tenants** to ensure isolation

## Sources

- [sqlalchemy-tenants](https://github.com/Telemaco019/sqlalchemy-tenants)
- [Atlas RLS Guide](https://atlasgo.io/guides/orms/sqlalchemy/row-level-security)
- [PostgreSQL RLS for Multi-Tenant SaaS](https://medium.com/@anand_thakkar/row-level-security-rls-in-postgresql-for-multi-tenant-saas-apps-ef8c324031d0)
