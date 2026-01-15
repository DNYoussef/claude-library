"""
Quality Gate Component

Async quality gates with threshold validation for pipeline orchestration.

Usage:
    from library.components.utilities.quality_gate import (
        QualityGate,
        GateConfig,
        GateType,
        GateStatus,
        GateResult,
        GateManager,
        GateFailedError,
        RichMetricResult,
        create_sync_gate,
        create_quality_gate,
        create_dependency_gate,
        create_compile_gate,
    )
"""

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

# Alias for convenience
QualityGate = GateManager

__all__ = [
    "GateType",
    "GateStatus",
    "GateConfig",
    "GateResult",
    "GateManager",
    "GateFailedError",
    "RichMetricResult",
    "QualityGate",
    "create_sync_gate",
    "create_quality_gate",
    "create_dependency_gate",
    "create_compile_gate",
]
