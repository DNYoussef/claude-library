"""
Atomic YAML Writes with Backup

Safe file I/O utilities for YAML files with atomic operations and backup support.
Prevents data loss from interrupted writes and provides rollback capability.

LEGO Component: Uses pathlib for cross-platform compatibility

Usage:
    from library.components.utilities.io_helpers import (
        yaml_safe_write, yaml_safe_read, AtomicWriter
    )

    # Simple write with backup
    await yaml_safe_write("config.yaml", {"key": "value"})

    # Read with validation
    data = await yaml_safe_read("config.yaml")

    # Manual atomic write
    async with AtomicWriter("config.yaml") as writer:
        writer.write_yaml({"key": "value"})
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Optional yaml import
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logger.warning("PyYAML not available. Install with: pip install pyyaml")


@dataclass
class WriteResult:
    """Result of a file write operation."""
    success: bool
    path: Path
    backup_path: Optional[Path] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "path": str(self.path),
            "backup_path": str(self.backup_path) if self.backup_path else None,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BackupConfig:
    """Configuration for backup behavior."""
    enabled: bool = True
    backup_suffix: str = ".bak"
    backup_dir: Optional[Path] = None  # If None, backup in same directory
    max_backups: int = 5  # Maximum number of backups to keep
    timestamp_format: str = "%Y%m%d_%H%M%S"


class AtomicWriter:
    """
    Context manager for atomic file writes.

    Writes to a temporary file first, then atomically renames to target.
    This prevents data corruption from interrupted writes.

    Usage:
        async with AtomicWriter("config.yaml") as writer:
            writer.write_yaml({"key": "value"})

        # Or for sync operations:
        with AtomicWriter("config.yaml", sync=True) as writer:
            writer.write_text("content")
    """

    def __init__(
        self,
        path: Union[str, Path],
        backup_config: Optional[BackupConfig] = None,
        encoding: str = "utf-8",
        sync: bool = False
    ):
        """
        Initialize atomic writer.

        Args:
            path: Target file path
            backup_config: Backup configuration (optional)
            encoding: File encoding (default: utf-8)
            sync: Use synchronous operations (default: False for async)
        """
        self._path = Path(path)
        self._backup_config = backup_config or BackupConfig()
        self._encoding = encoding
        self._sync = sync
        self._temp_path: Optional[Path] = None
        self._backup_path: Optional[Path] = None
        self._content: Optional[str] = None
        self._closed = False

    @property
    def path(self) -> Path:
        """Get target file path."""
        return self._path

    @property
    def backup_path(self) -> Optional[Path]:
        """Get backup file path if created."""
        return self._backup_path

    def write_text(self, content: str) -> None:
        """
        Write text content to be saved.

        Args:
            content: Text content to write
        """
        self._content = content

    def write_yaml(self, data: Any, **kwargs: Any) -> None:
        """
        Write data as YAML.

        Args:
            data: Data to serialize to YAML
            **kwargs: Additional arguments for yaml.dump
        """
        if not YAML_AVAILABLE:
            raise RuntimeError("PyYAML not available. Install with: pip install pyyaml")

        default_kwargs = {
            "default_flow_style": False,
            "allow_unicode": True,
            "sort_keys": False,
        }
        default_kwargs.update(kwargs)
        self._content = yaml.dump(data, **default_kwargs)

    async def __aenter__(self) -> "AtomicWriter":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit with atomic write."""
        if exc_type is not None:
            # Exception occurred, don't write
            self._cleanup_temp()
            return

        await self._commit_async()

    def __enter__(self) -> "AtomicWriter":
        """Sync context manager entry."""
        if not self._sync:
            raise RuntimeError("Use 'async with' for async operations or set sync=True")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Sync context manager exit with atomic write."""
        if exc_type is not None:
            self._cleanup_temp()
            return

        self._commit_sync()

    async def _commit_async(self) -> WriteResult:
        """Commit the write operation asynchronously."""
        if self._content is None:
            return WriteResult(
                success=False,
                path=self._path,
                error="No content to write"
            )

        try:
            # Create backup if file exists
            if self._backup_config.enabled and self._path.exists():
                self._backup_path = await self._create_backup_async()

            # Write to temp file first
            self._temp_path = await self._write_temp_async()

            # Atomic rename
            await asyncio.to_thread(self._atomic_rename)

            logger.info(f"Atomic write successful: {self._path}")
            return WriteResult(
                success=True,
                path=self._path,
                backup_path=self._backup_path
            )

        except Exception as e:
            logger.error(f"Atomic write failed: {e}")
            self._cleanup_temp()
            return WriteResult(
                success=False,
                path=self._path,
                backup_path=self._backup_path,
                error=str(e)
            )

    def _commit_sync(self) -> WriteResult:
        """Commit the write operation synchronously."""
        if self._content is None:
            return WriteResult(
                success=False,
                path=self._path,
                error="No content to write"
            )

        try:
            # Create backup if file exists
            if self._backup_config.enabled and self._path.exists():
                self._backup_path = self._create_backup_sync()

            # Write to temp file first
            self._temp_path = self._write_temp_sync()

            # Atomic rename
            self._atomic_rename()

            logger.info(f"Atomic write successful: {self._path}")
            return WriteResult(
                success=True,
                path=self._path,
                backup_path=self._backup_path
            )

        except Exception as e:
            logger.error(f"Atomic write failed: {e}")
            self._cleanup_temp()
            return WriteResult(
                success=False,
                path=self._path,
                backup_path=self._backup_path,
                error=str(e)
            )

    async def _write_temp_async(self) -> Path:
        """Write content to a temporary file asynchronously."""
        parent_dir = self._path.parent
        await asyncio.to_thread(parent_dir.mkdir, parents=True, exist_ok=True)

        # Create temp file in same directory for atomic rename
        fd, temp_path_str = tempfile.mkstemp(
            suffix=".tmp",
            prefix=f".{self._path.name}.",
            dir=parent_dir
        )
        temp_path = Path(temp_path_str)

        try:
            await asyncio.to_thread(
                lambda: Path(temp_path).write_text(self._content, encoding=self._encoding)
            )
            os.close(fd)
        except Exception:
            os.close(fd)
            temp_path.unlink(missing_ok=True)
            raise

        return temp_path

    def _write_temp_sync(self) -> Path:
        """Write content to a temporary file synchronously."""
        parent_dir = self._path.parent
        parent_dir.mkdir(parents=True, exist_ok=True)

        # Create temp file in same directory for atomic rename
        fd, temp_path_str = tempfile.mkstemp(
            suffix=".tmp",
            prefix=f".{self._path.name}.",
            dir=parent_dir
        )
        temp_path = Path(temp_path_str)

        try:
            temp_path.write_text(self._content, encoding=self._encoding)
            os.close(fd)
        except Exception:
            os.close(fd)
            temp_path.unlink(missing_ok=True)
            raise

        return temp_path

    async def _create_backup_async(self) -> Path:
        """Create a backup of the existing file asynchronously."""
        return await asyncio.to_thread(self._create_backup_sync)

    def _create_backup_sync(self) -> Path:
        """Create a backup of the existing file synchronously."""
        if self._backup_config.backup_dir:
            backup_dir = self._backup_config.backup_dir
            backup_dir.mkdir(parents=True, exist_ok=True)
        else:
            backup_dir = self._path.parent

        timestamp = datetime.now().strftime(self._backup_config.timestamp_format)
        backup_name = f"{self._path.stem}_{timestamp}{self._backup_config.backup_suffix}"
        backup_path = backup_dir / backup_name

        shutil.copy2(self._path, backup_path)
        logger.debug(f"Created backup: {backup_path}")

        # Clean up old backups
        self._cleanup_old_backups(backup_dir)

        return backup_path

    def _cleanup_old_backups(self, backup_dir: Path) -> None:
        """Remove old backups exceeding max_backups limit."""
        pattern = f"{self._path.stem}_*{self._backup_config.backup_suffix}"
        backups = sorted(backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime)

        while len(backups) > self._backup_config.max_backups:
            old_backup = backups.pop(0)
            old_backup.unlink()
            logger.debug(f"Removed old backup: {old_backup}")

    def _atomic_rename(self) -> None:
        """Perform atomic rename from temp to target."""
        if self._temp_path is None:
            raise RuntimeError("No temp file to rename")

        # On Windows, need to remove target first (not atomic)
        # On Unix, rename is atomic
        if os.name == "nt" and self._path.exists():
            self._path.unlink()

        self._temp_path.rename(self._path)
        self._temp_path = None

    def _cleanup_temp(self) -> None:
        """Clean up temporary file if it exists."""
        if not self._temp_path or not self._temp_path.exists():
            return
        try:
            self._temp_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to clean up temp file: {e}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def yaml_safe_write(
    path: Union[str, Path],
    data: Any,
    backup: bool = True,
    **yaml_kwargs: Any
) -> WriteResult:
    """
    Safely write data to a YAML file with atomic operation and backup.

    Args:
        path: Target file path
        data: Data to serialize to YAML
        backup: Whether to create backup (default: True)
        **yaml_kwargs: Additional arguments for yaml.dump

    Returns:
        WriteResult with success status and paths
    """
    backup_config = BackupConfig(enabled=backup)
    async with AtomicWriter(path, backup_config=backup_config) as writer:
        writer.write_yaml(data, **yaml_kwargs)

    return WriteResult(
        success=True,
        path=Path(path),
        backup_path=writer.backup_path
    )


async def yaml_safe_read(
    path: Union[str, Path],
    default: Any = None,
    encoding: str = "utf-8"
) -> Any:
    """
    Safely read a YAML file.

    Args:
        path: File path to read
        default: Default value if file doesn't exist or is invalid
        encoding: File encoding (default: utf-8)

    Returns:
        Parsed YAML data or default value
    """
    if not YAML_AVAILABLE:
        raise RuntimeError("PyYAML not available. Install with: pip install pyyaml")

    file_path = Path(path)
    if not file_path.exists():
        return default

    try:
        content = await asyncio.to_thread(
            file_path.read_text, encoding=encoding
        )
        return yaml.safe_load(content)
    except Exception as e:
        logger.error(f"Failed to read YAML file {path}: {e}")
        return default


def yaml_safe_write_sync(
    path: Union[str, Path],
    data: Any,
    backup: bool = True,
    **yaml_kwargs: Any
) -> WriteResult:
    """
    Synchronous version of yaml_safe_write.

    Args:
        path: Target file path
        data: Data to serialize to YAML
        backup: Whether to create backup (default: True)
        **yaml_kwargs: Additional arguments for yaml.dump

    Returns:
        WriteResult with success status and paths
    """
    backup_config = BackupConfig(enabled=backup)
    with AtomicWriter(path, backup_config=backup_config, sync=True) as writer:
        writer.write_yaml(data, **yaml_kwargs)

    return WriteResult(
        success=True,
        path=Path(path),
        backup_path=writer.backup_path
    )


def yaml_safe_read_sync(
    path: Union[str, Path],
    default: Any = None,
    encoding: str = "utf-8"
) -> Any:
    """
    Synchronous version of yaml_safe_read.

    Args:
        path: File path to read
        default: Default value if file doesn't exist or is invalid
        encoding: File encoding (default: utf-8)

    Returns:
        Parsed YAML data or default value
    """
    if not YAML_AVAILABLE:
        raise RuntimeError("PyYAML not available. Install with: pip install pyyaml")

    file_path = Path(path)
    if not file_path.exists():
        return default

    try:
        content = file_path.read_text(encoding=encoding)
        return yaml.safe_load(content)
    except Exception as e:
        logger.error(f"Failed to read YAML file {path}: {e}")
        return default


async def safe_text_write(
    path: Union[str, Path],
    content: str,
    backup: bool = True,
    encoding: str = "utf-8"
) -> WriteResult:
    """
    Safely write text to a file with atomic operation and backup.

    Args:
        path: Target file path
        content: Text content to write
        backup: Whether to create backup (default: True)
        encoding: File encoding (default: utf-8)

    Returns:
        WriteResult with success status and paths
    """
    backup_config = BackupConfig(enabled=backup)
    async with AtomicWriter(path, backup_config=backup_config, encoding=encoding) as writer:
        writer.write_text(content)

    return WriteResult(
        success=True,
        path=Path(path),
        backup_path=writer.backup_path
    )


async def restore_from_backup(
    backup_path: Union[str, Path],
    target_path: Optional[Union[str, Path]] = None
) -> WriteResult:
    """
    Restore a file from backup.

    Args:
        backup_path: Path to backup file
        target_path: Target path (if None, derived from backup name)

    Returns:
        WriteResult with success status
    """
    backup = Path(backup_path)
    if not backup.exists():
        return WriteResult(
            success=False,
            path=backup,
            error=f"Backup file not found: {backup}"
        )

    if target_path is None:
        # Derive target from backup name (remove timestamp and .bak suffix)
        name = backup.stem
        # Remove timestamp suffix like _20240101_120000
        parts = name.rsplit("_", 2)
        if len(parts) >= 3:
            original_name = parts[0]
            target_path = backup.parent / f"{original_name}.yaml"
        else:
            return WriteResult(
                success=False,
                path=backup,
                error="Cannot derive target path from backup name"
            )

    target = Path(target_path)

    try:
        await asyncio.to_thread(shutil.copy2, backup, target)
        logger.info(f"Restored {target} from backup {backup}")
        return WriteResult(
            success=True,
            path=target,
            backup_path=backup
        )
    except Exception as e:
        return WriteResult(
            success=False,
            path=target,
            backup_path=backup,
            error=str(e)
        )


def list_backups(
    path: Union[str, Path],
    backup_dir: Optional[Union[str, Path]] = None,
    backup_suffix: str = ".bak"
) -> List[Path]:
    """
    List all backups for a file.

    Args:
        path: Original file path
        backup_dir: Backup directory (if None, same as file directory)
        backup_suffix: Backup file suffix

    Returns:
        List of backup file paths, sorted by modification time (newest first)
    """
    file_path = Path(path)
    search_dir = Path(backup_dir) if backup_dir else file_path.parent

    if not search_dir.exists():
        return []

    pattern = f"{file_path.stem}_*{backup_suffix}"
    backups = list(search_dir.glob(pattern))
    return sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True)
