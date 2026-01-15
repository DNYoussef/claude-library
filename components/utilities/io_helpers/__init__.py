"""
I/O Helpers Component

Atomic file operations with backup support for safe file writes.

Usage:
    from library.components.utilities.io_helpers import (
        yaml_safe_write,
        yaml_safe_read,
        safe_text_write,
        AtomicWriter,
        BackupConfig,
    )
"""

from .yaml_safe_write import (
    WriteResult,
    BackupConfig,
    AtomicWriter,
    yaml_safe_write,
    yaml_safe_read,
    yaml_safe_write_sync,
    yaml_safe_read_sync,
    safe_text_write,
    restore_from_backup,
    list_backups,
)

__all__ = [
    "WriteResult",
    "BackupConfig",
    "AtomicWriter",
    "yaml_safe_write",
    "yaml_safe_read",
    "yaml_safe_write_sync",
    "yaml_safe_read_sync",
    "safe_text_write",
    "restore_from_backup",
    "list_backups",
]
