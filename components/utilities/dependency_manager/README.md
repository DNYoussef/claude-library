# Runtime Dependency Manager

Utilities for checking and managing component dependencies at runtime.

## Features

- Check if component dependencies are installed
- Get missing dependencies for a component
- Domain-based dependency groups
- Catalog-aware dependency resolution

## Installation

The library uses optional dependency groups. Install the dependencies you need:

```bash
# Install specific domain
pip install claude-library[api]     # FastAPI, Pydantic
pip install claude-library[database]  # SQLAlchemy, asyncpg
pip install claude-library[memory]    # ChromaDB

# Install all dependencies
pip install claude-library[all]
```

## Usage

### Quick Check

```python
from library.components.utilities.dependency_manager import (
    check_dependencies,
    get_missing_dependencies,
)

# Check if packages are installed
ok, missing = check_dependencies(['fastapi', 'pydantic'])
if not ok:
    print(f"Missing: {missing}")
    print(f"Install: pip install {' '.join(missing)}")
```

### Component Check

```python
from library.components.utilities.dependency_manager import DependencyChecker

checker = DependencyChecker()

# Check specific component
result = checker.check_component('api/fastapi_router')
if not result:
    print(f"Missing: {result.missing}")
    print(checker.get_install_command(result))

# Check entire domain
result = checker.check_domain('api')
```

### Domain Dependencies

```python
from library.components.utilities.dependency_manager import (
    get_domain_dependencies,
    check_domain,
)

# Get dependencies for a domain
deps = get_domain_dependencies('api')
print(deps.packages)  # ['fastapi>=0.100.0', 'pydantic>=2.0.0']

# Check if domain dependencies are installed
ok, missing = check_domain('api')
```

## Available Domains

| Domain | Group | Packages |
|--------|-------|----------|
| api | api | fastapi, pydantic |
| database | database | sqlalchemy, asyncpg |
| cache | cache | redis |
| http | http | httpx |
| auth | auth | python-jose |
| observability | observability | opentelemetry-api, opentelemetry-sdk |
| memory | memory | chromadb |
| content | content | yt-dlp, anthropic |
| analysis | analysis | pandas, scikit-learn, pymoo |
| scheduling | scheduling | apscheduler |
| realtime | realtime | websockets |
| payments | payments | stripe, plaid-python |
| testing | testing | pytest, pytest-asyncio |

## Exports

| Export | Description |
|--------|-------------|
| `DependencyChecker` | Full checker with catalog support |
| `DependencyResult` | Result dataclass with ok/missing/installed |
| `DomainDependencies` | Domain dependency info |
| `check_dependencies` | Quick check function |
| `get_missing_dependencies` | Get missing packages |
| `get_domain_dependencies` | Get deps for domain |
| `check_domain` | Check all domain deps |
