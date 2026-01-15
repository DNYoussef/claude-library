"""
loopctl - Loop Control for Cognitive Architecture

Provides the FrozenHarness evaluation system for grading artifacts
in the Ralph loop system.

Example:
    from cognitive_architecture.loopctl import FrozenHarness, check_emergency_stop

    # Check emergency stop first
    should_stop, reason = check_emergency_stop()
    if should_stop:
        print(reason)
        exit(1)

    # Grade an artifact
    harness = FrozenHarness()
    metrics = harness.grade(Path("output.txt"))
"""

from .core import (
    FrozenHarness,
    GradeMetrics,
    check_emergency_stop,
)

__all__ = [
    "FrozenHarness",
    "GradeMetrics",
    "check_emergency_stop",
]

__version__ = "1.0.0"
