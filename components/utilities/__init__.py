"""
Utilities Component Package

LEGO-compatible utility components for common operations.

Components:
- quality_gate: Async quality gates with threshold validation
- circuit_breaker: Generic circuit breaker with exponential backoff
- health_monitor: Async health polling with alerting
- io_helpers: Atomic file operations with backup support

All components import shared types from library.common.types.

Usage:
    # Import from package
    from library.components.utilities import (
        GateManager, CircuitBreaker, HealthMonitor, yaml_safe_write
    )

    # Or import from specific modules
    from library.components.utilities.quality_gate import GateManager
    from library.components.utilities.circuit_breaker import CircuitBreaker
"""

# Version info
__version__ = "1.0.0"
__author__ = "David Youssef"

# Re-export key components
from .quality_gate import (
    GateType,
    GateStatus,
    GateConfig,
    GateResult,
    GateManager,
    GateFailedError,
    RichMetricResult,
    create_sync_gate,
    create_quality_gate,
    create_dependency_gate,
    create_compile_gate,
)

from .circuit_breaker import (
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerMetrics,
    CircuitBreakerStatus,
    CircuitBreaker,
    CircuitBreakerManager,
)

from .health_monitor import (
    HealthState,
    HealthCheckResult,
    HealthStatus,
    HealthCheckConfig,
    AlertConfig,
    HealthMonitor,
)

from .io_helpers import (
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
    # Quality Gate
    "GateType",
    "GateStatus",
    "GateConfig",
    "GateResult",
    "GateManager",
    "GateFailedError",
    "RichMetricResult",
    "create_sync_gate",
    "create_quality_gate",
    "create_dependency_gate",
    "create_compile_gate",
    # Circuit Breaker
    "CircuitState",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitBreakerMetrics",
    "CircuitBreakerStatus",
    "CircuitBreaker",
    "CircuitBreakerManager",
    # Health Monitor
    "HealthState",
    "HealthCheckResult",
    "HealthStatus",
    "HealthCheckConfig",
    "AlertConfig",
    "HealthMonitor",
    # IO Helpers
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
