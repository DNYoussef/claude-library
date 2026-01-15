"""
loopctl - Loop Control for Cognitive Architecture

Provides the FrozenHarness evaluation system for grading artifacts
in the Ralph loop system, plus Decision Authority Model for hierarchical control.

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

    # Decision authority
    from cognitive_architecture.loopctl import DecisionAuthority, AuthorityLevel

    authority = DecisionAuthority()
    result = authority.make_decision(
        level=AuthorityLevel.LOOP3,
        action="propose",
        target="learning_rate",
        reason="Optimization suggests change"
    )
"""

from .core import (
    FrozenHarness,
    GradeMetrics,
    check_emergency_stop,
)

from .authority import (
    AuthorityLevel,
    DecisionAction,
    Decision,
    DecisionResult,
    DecisionAuthority,
)

__all__ = [
    # Core harness
    "FrozenHarness",
    "GradeMetrics",
    "check_emergency_stop",
    # Decision authority
    "AuthorityLevel",
    "DecisionAction",
    "Decision",
    "DecisionResult",
    "DecisionAuthority",
]

__version__ = "1.1.0"
