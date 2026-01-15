"""
Auditor Base Pattern - Structured Audit Framework

Provides base classes for building auditors that emit structured results
with confidence scores and action recommendations.

Source: Extracted from context-cascade/cognitive-architecture/integration/auditors.py
"""

from .auditor_base import (
    Illocution,
    Affect,
    ActionClass,
    AuditorResult,
    BaseAuditor,
)

__all__ = [
    "Illocution",
    "Affect",
    "ActionClass",
    "AuditorResult",
    "BaseAuditor",
]
