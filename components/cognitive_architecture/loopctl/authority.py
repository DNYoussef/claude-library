"""
Decision Authority Model - Hierarchical Decision Control for FrozenHarness

Implements the decision authority hierarchy from DUAL-MOO-CONTROL-SPEC.md:

Authority Levels (highest to lowest):
1. FrozenHarness (HARNESS) - Can veto any decision
2. Human Override (HUMAN) - Can override with audit trail
3. Loop 3 Meta-Optimizer (LOOP3) - Can propose, not enforce
4. Loop 1 Agent (LOOP1) - Execute only within bounds

Rules:
- Lower authority cannot modify higher
- All decisions logged with authority level
- Veto requires explanation

VERIX Example:
    [assert|confident] Authority levels enforce separation of concerns
    [ground:architecture-spec] [conf:0.95] [state:confirmed]

Usage:
    from cognitive_architecture.loopctl.authority import (
        AuthorityLevel,
        DecisionAuthority,
        Decision,
    )

    authority = DecisionAuthority()

    # Harness vetoes a decision
    result = authority.make_decision(
        level=AuthorityLevel.HARNESS,
        action="veto",
        target="parameter_change",
        reason="Quality threshold not met",
    )

    # Lower level tries to override - blocked
    result = authority.make_decision(
        level=AuthorityLevel.LOOP1,
        action="modify",
        target="harness_weights",  # Blocked - higher authority owns this
    )
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class AuthorityLevel(IntEnum):
    """
    Decision authority levels (higher number = higher authority).

    HARNESS (4): FrozenHarness - highest authority, can veto anything
    HUMAN (3): Human Override - can override with audit trail
    LOOP3 (2): Loop 3 Meta-Optimizer - can propose, not enforce
    LOOP1 (1): Loop 1 Agent - execute within bounds only
    """
    LOOP1 = 1   # Loop 1 Agent - lowest
    LOOP3 = 2   # Loop 3 Meta-Optimizer
    HUMAN = 3   # Human Override
    HARNESS = 4 # FrozenHarness - highest


class DecisionAction:
    """Standard decision actions."""
    APPROVE = "approve"
    REJECT = "reject"
    VETO = "veto"
    OVERRIDE = "override"
    PROPOSE = "propose"
    EXECUTE = "execute"
    MODIFY = "modify"


@dataclass
class Decision:
    """
    A recorded decision with authority metadata.

    Attributes:
        id: Unique decision identifier
        timestamp: When decision was made
        authority_level: Authority level that made the decision
        action: Action taken (approve, reject, veto, override, etc.)
        target: What was the subject of the decision
        reason: Explanation for the decision
        metadata: Additional context
        vetoed_by: If vetoed, which higher authority did it
        overridden_by: If overridden, which authority did it
    """
    id: str
    timestamp: datetime
    authority_level: AuthorityLevel
    action: str
    target: str
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    vetoed_by: Optional[AuthorityLevel] = None
    overridden_by: Optional[AuthorityLevel] = None

    @property
    def is_vetoed(self) -> bool:
        """Check if this decision was vetoed."""
        return self.vetoed_by is not None

    @property
    def is_overridden(self) -> bool:
        """Check if this decision was overridden."""
        return self.overridden_by is not None

    @property
    def effective(self) -> bool:
        """Check if this decision is still effective (not vetoed/overridden)."""
        return not self.is_vetoed and not self.is_overridden

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "authority_level": self.authority_level.name,
            "authority_value": self.authority_level.value,
            "action": self.action,
            "target": self.target,
            "reason": self.reason,
            "metadata": self.metadata,
            "vetoed_by": self.vetoed_by.name if self.vetoed_by else None,
            "overridden_by": self.overridden_by.name if self.overridden_by else None,
            "effective": self.effective,
        }


@dataclass
class DecisionResult:
    """
    Result of a decision attempt.

    Attributes:
        allowed: Whether the decision was allowed
        decision: The decision record (if allowed)
        blocked_reason: Why the decision was blocked (if not allowed)
        blocking_authority: Which authority blocked it (if blocked)
    """
    allowed: bool
    decision: Optional[Decision] = None
    blocked_reason: str = ""
    blocking_authority: Optional[AuthorityLevel] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "allowed": self.allowed,
            "decision": self.decision.to_dict() if self.decision else None,
            "blocked_reason": self.blocked_reason,
            "blocking_authority": (
                self.blocking_authority.name if self.blocking_authority else None
            ),
        }


class DecisionAuthority:
    """
    Decision authority manager for hierarchical control.

    Enforces authority hierarchy rules:
    - Lower authority cannot modify higher authority decisions
    - All decisions are logged with authority level
    - Vetoes require explanations

    Usage:
        authority = DecisionAuthority()

        # Make a decision
        result = authority.make_decision(
            level=AuthorityLevel.LOOP3,
            action="propose",
            target="learning_rate",
            reason="Optimization suggests lower rate"
        )

        # Check if target is modifiable
        if authority.can_modify("harness_weights", AuthorityLevel.LOOP1):
            # Safe to modify
            pass
    """

    # Targets owned by each authority level
    # Higher authority owns more critical targets
    DEFAULT_OWNERSHIP: Dict[AuthorityLevel, Set[str]] = {
        AuthorityLevel.HARNESS: {
            "harness_weights",
            "harness_version",
            "evaluation_criteria",
            "quality_thresholds",
            "veto_rules",
            "integrity_check",
        },
        AuthorityLevel.HUMAN: {
            "override_rules",
            "human_preferences",
            "safety_limits",
            "audit_policy",
        },
        AuthorityLevel.LOOP3: {
            "optimization_parameters",
            "learning_rate",
            "pareto_weights",
            "meta_loop_config",
        },
        AuthorityLevel.LOOP1: {
            "execution_context",
            "task_parameters",
            "runtime_config",
        },
    }

    def __init__(
        self,
        ownership: Optional[Dict[AuthorityLevel, Set[str]]] = None,
        enable_logging: bool = True,
    ):
        """
        Initialize DecisionAuthority.

        Args:
            ownership: Custom target ownership map (uses defaults if None)
            enable_logging: Whether to log all decisions
        """
        self._ownership = ownership or self.DEFAULT_OWNERSHIP.copy()
        self._enable_logging = enable_logging
        self._decisions: List[Decision] = []
        self._decision_counter = 0
        self._veto_callbacks: List[Callable[[Decision], None]] = []
        self._override_callbacks: List[Callable[[Decision], None]] = []

        logger.info("DecisionAuthority initialized")

    def _generate_id(self) -> str:
        """Generate unique decision ID."""
        self._decision_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"decision_{timestamp}_{self._decision_counter:04d}"

    def get_owner(self, target: str) -> Optional[AuthorityLevel]:
        """
        Get the authority level that owns a target.

        Args:
            target: Target to check

        Returns:
            AuthorityLevel that owns the target, or None if unowned
        """
        for level, targets in self._ownership.items():
            if target in targets:
                return level
        return None

    def can_modify(self, target: str, level: AuthorityLevel) -> bool:
        """
        Check if an authority level can modify a target.

        Args:
            target: Target to modify
            level: Authority level attempting modification

        Returns:
            True if modification is allowed
        """
        owner = self.get_owner(target)
        if owner is None:
            return True  # Unowned targets can be modified by anyone
        return level >= owner

    def make_decision(
        self,
        level: AuthorityLevel,
        action: str,
        target: str,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DecisionResult:
        """
        Make a decision at the specified authority level.

        Args:
            level: Authority level making the decision
            action: Action being taken
            target: Subject of the decision
            reason: Explanation for the decision
            metadata: Additional context

        Returns:
            DecisionResult with allowed status and decision record
        """
        # Check if this level can modify the target
        owner = self.get_owner(target)
        if owner is not None and level < owner:
            # Blocked - lower authority cannot modify higher authority targets
            blocked_reason = (
                f"Authority level {level.name} cannot modify target '{target}' "
                f"owned by {owner.name}"
            )
            logger.warning(blocked_reason)
            return DecisionResult(
                allowed=False,
                blocked_reason=blocked_reason,
                blocking_authority=owner,
            )

        # Decision allowed - create record
        decision = Decision(
            id=self._generate_id(),
            timestamp=datetime.now(),
            authority_level=level,
            action=action,
            target=target,
            reason=reason,
            metadata=metadata or {},
        )

        self._decisions.append(decision)

        if self._enable_logging:
            logger.info(
                f"Decision {decision.id}: {level.name} {action} on '{target}'"
            )

        return DecisionResult(allowed=True, decision=decision)

    def veto(
        self,
        decision_id: str,
        vetoing_level: AuthorityLevel,
        reason: str,
    ) -> DecisionResult:
        """
        Veto a previous decision.

        Args:
            decision_id: ID of decision to veto
            vetoing_level: Authority level issuing the veto
            reason: Explanation for the veto (required)

        Returns:
            DecisionResult indicating veto success
        """
        if not reason:
            return DecisionResult(
                allowed=False,
                blocked_reason="Veto requires explanation (reason parameter)",
            )

        # Find the decision
        decision = self.get_decision(decision_id)
        if decision is None:
            return DecisionResult(
                allowed=False,
                blocked_reason=f"Decision {decision_id} not found",
            )

        # Check authority - can only veto decisions from lower authority
        if vetoing_level <= decision.authority_level:
            return DecisionResult(
                allowed=False,
                blocked_reason=(
                    f"Authority level {vetoing_level.name} cannot veto "
                    f"decision from {decision.authority_level.name}"
                ),
                blocking_authority=decision.authority_level,
            )

        # Apply veto
        decision.vetoed_by = vetoing_level
        decision.metadata["veto_reason"] = reason
        decision.metadata["veto_timestamp"] = datetime.now().isoformat()

        if self._enable_logging:
            logger.warning(
                f"Decision {decision_id} vetoed by {vetoing_level.name}: {reason}"
            )

        # Execute veto callbacks
        for callback in self._veto_callbacks:
            try:
                callback(decision)
            except Exception as e:
                logger.error(f"Veto callback error: {e}")

        return DecisionResult(allowed=True, decision=decision)

    def override(
        self,
        decision_id: str,
        overriding_level: AuthorityLevel,
        reason: str,
    ) -> DecisionResult:
        """
        Override a previous decision (for HUMAN level only).

        Args:
            decision_id: ID of decision to override
            overriding_level: Authority level issuing the override (must be HUMAN)
            reason: Explanation for the override

        Returns:
            DecisionResult indicating override success
        """
        if overriding_level != AuthorityLevel.HUMAN:
            return DecisionResult(
                allowed=False,
                blocked_reason="Only HUMAN authority can issue overrides",
            )

        if not reason:
            return DecisionResult(
                allowed=False,
                blocked_reason="Override requires explanation (reason parameter)",
            )

        decision = self.get_decision(decision_id)
        if decision is None:
            return DecisionResult(
                allowed=False,
                blocked_reason=f"Decision {decision_id} not found",
            )

        # Apply override
        decision.overridden_by = overriding_level
        decision.metadata["override_reason"] = reason
        decision.metadata["override_timestamp"] = datetime.now().isoformat()

        if self._enable_logging:
            logger.info(
                f"Decision {decision_id} overridden by HUMAN: {reason}"
            )

        # Execute override callbacks
        for callback in self._override_callbacks:
            try:
                callback(decision)
            except Exception as e:
                logger.error(f"Override callback error: {e}")

        return DecisionResult(allowed=True, decision=decision)

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get a decision by ID."""
        for decision in self._decisions:
            if decision.id == decision_id:
                return decision
        return None

    def get_decisions(
        self,
        level: Optional[AuthorityLevel] = None,
        target: Optional[str] = None,
        action: Optional[str] = None,
        effective_only: bool = False,
    ) -> List[Decision]:
        """
        Get decisions matching criteria.

        Args:
            level: Filter by authority level
            target: Filter by target
            action: Filter by action
            effective_only: Only return non-vetoed/overridden decisions

        Returns:
            List of matching decisions
        """
        results = []
        for decision in self._decisions:
            if level is not None and decision.authority_level != level:
                continue
            if target is not None and decision.target != target:
                continue
            if action is not None and decision.action != action:
                continue
            if effective_only and not decision.effective:
                continue
            results.append(decision)
        return results

    def get_veto_rate(self) -> float:
        """Calculate veto rate (vetoes / total decisions)."""
        if not self._decisions:
            return 0.0
        vetoed = sum(1 for d in self._decisions if d.is_vetoed)
        return vetoed / len(self._decisions)

    def get_override_rate(self) -> float:
        """Calculate override rate (overrides / vetoes)."""
        vetoed = sum(1 for d in self._decisions if d.is_vetoed)
        if vetoed == 0:
            return 0.0
        overridden = sum(1 for d in self._decisions if d.is_overridden)
        return overridden / vetoed

    def get_statistics(self) -> Dict[str, Any]:
        """Get decision statistics for monitoring."""
        by_level = {}
        for level in AuthorityLevel:
            level_decisions = [
                d for d in self._decisions if d.authority_level == level
            ]
            by_level[level.name] = {
                "total": len(level_decisions),
                "effective": sum(1 for d in level_decisions if d.effective),
                "vetoed": sum(1 for d in level_decisions if d.is_vetoed),
                "overridden": sum(1 for d in level_decisions if d.is_overridden),
            }

        return {
            "total_decisions": len(self._decisions),
            "effective_decisions": sum(1 for d in self._decisions if d.effective),
            "veto_rate": self.get_veto_rate(),
            "override_rate": self.get_override_rate(),
            "by_level": by_level,
        }

    def register_veto_callback(
        self,
        callback: Callable[[Decision], None]
    ) -> None:
        """Register callback for veto events."""
        self._veto_callbacks.append(callback)

    def register_override_callback(
        self,
        callback: Callable[[Decision], None]
    ) -> None:
        """Register callback for override events."""
        self._override_callbacks.append(callback)

    def persist(self, output_path: Optional[Path] = None) -> Path:
        """
        Persist all decisions to JSON file.

        Args:
            output_path: Path for output file

        Returns:
            Path to persisted file
        """
        if output_path is None:
            output_path = Path("decisions_log.json")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "statistics": self.get_statistics(),
            "decisions": [d.to_dict() for d in self._decisions],
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        return output_path

    def clear(self) -> int:
        """Clear all decisions and return count cleared."""
        count = len(self._decisions)
        self._decisions = []
        return count
