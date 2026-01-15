# I/O Helpers Component

Atomic file operations with backup support for safe file writes.

## Features

- **Atomic writes**: Write to temp file, then rename (prevents corruption)
- **Automatic backups**: Timestamped backups before overwrite
- **Backup rotation**: Configurable max backups with automatic cleanup
- **Async and sync**: Support for both asyncio and synchronous operations
- **YAML support**: Convenience functions for YAML files

## Installation

Requires `pyyaml` for YAML operations:

```bash
pip install pyyaml
```

## Usage

### Simple YAML Write

```python
import asyncio
from library.components.utilities.io_helpers import yaml_safe_write

async def main():
    data = {"database": {"host": "localhost", "port": 5432}}
    result = await yaml_safe_write("config.yaml", data)
    if result.success:
        print(f"Written to {result.path}")

asyncio.run(main())
```

### Simple YAML Read

```python
from library.components.utilities.io_helpers import yaml_safe_read

data = await yaml_safe_read("config.yaml", default={})
```

### Sync Operations

```python
from library.components.utilities.io_helpers import (
    yaml_safe_write_sync,
    yaml_safe_read_sync
)

result = yaml_safe_write_sync("config.yaml", {"key": "value"})
data = yaml_safe_read_sync("config.yaml", default={})
```

### Custom Backup Configuration

```python
from library.components.utilities.io_helpers import (
    AtomicWriter,
    BackupConfig
)

backup_config = BackupConfig(
    enabled=True,
    backup_suffix=".backup",
    max_backups=10,
)

async with AtomicWriter("config.yaml", backup_config=backup_config) as writer:
    writer.write_yaml({"key": "value"})
```

### Working with Backups

```python
from library.components.utilities.io_helpers import (
    list_backups,
    restore_from_backup
)

backups = list_backups("config.yaml")
if backups:
    result = await restore_from_backup(backups[0])
```

## API Reference

### AtomicWriter

```python
class AtomicWriter:
    def write_text(content: str) -> None
    def write_yaml(data: Any, **kwargs) -> None
    # Async: async with AtomicWriter(...) as writer:
    # Sync: with AtomicWriter(..., sync=True) as writer:
```

### Functions

```python
async def yaml_safe_write(path, data, backup=True) -> WriteResult
async def yaml_safe_read(path, default=None) -> Any
async def safe_text_write(path, content, backup=True) -> WriteResult
async def restore_from_backup(backup_path, target_path=None) -> WriteResult
def list_backups(path, backup_dir=None, backup_suffix=".bak") -> List[Path]
```
