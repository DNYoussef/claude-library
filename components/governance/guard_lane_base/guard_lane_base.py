"""
Guard lane base abstractions for governance workflows.

This module is intentionally self-contained so projects can copy it without
pulling in framework-specific enum packages.
"""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import ceil
from typing import Any


class TriggerType(str, Enum):
    PR_OPENED = "PR_OPENED"
    PR_MERGED = "PR_MERGED"
    CODE_PUSHED = "CODE_PUSHED"
    DEPLOY_REQUESTED = "DEPLOY_REQUESTED"
    DEPLOY_COMPLETED = "DEPLOY_COMPLETED"
    ROLLBACK_INITIATED = "ROLLBACK_INITIATED"
    DATA_ACCESS_REQUESTED = "DATA_ACCESS_REQUESTED"
    DATA_EXPORTED = "DATA_EXPORTED"
    PII_DETECTED = "PII_DETECTED"
    EVIDENCE_SUBMITTED = "EVIDENCE_SUBMITTED"
    AUDIT_REQUESTED = "AUDIT_REQUESTED"
    CONTRACT_DRAFTED = "CONTRACT_DRAFTED"
    CONTRACT_SIGNED = "CONTRACT_SIGNED"
    COMMUNICATION_SENT = "COMMUNICATION_SENT"
    EXTERNAL_MESSAGE = "EXTERNAL_MESSAGE"
    TICKET_CREATED = "TICKET_CREATED"
    TICKET_ESCALATED = "TICKET_ESCALATED"
    DEAL_PROPOSED = "DEAL_PROPOSED"
    DEAL_CLOSED = "DEAL_CLOSED"
    PRICING_CHANGED = "PRICING_CHANGED"


class RiskTier(str, Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class ConsensusType(str, Enum):
    ANY = "ANY"
    MAJORITY = "MAJORITY"
    SUPERMAJORITY = "SUPERMAJORITY"
    UNANIMOUS = "UNANIMOUS"


@dataclass(frozen=True)
class GuardEvent:
    trigger: TriggerType
    event_id: str
    actor_id: str | None = None
    project_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ApprovalSet:
    approver_persona_ids: set[str] = field(default_factory=set)
    consensus_type: ConsensusType = ConsensusType.MAJORITY
    delegation_allowed: bool = True
    sla_hours: int = 0

    def total_approvers_required(self) -> int:
        total = len(self.approver_persona_ids)
        if total == 0:
            return 0
        if self.consensus_type == ConsensusType.ANY:
            return 1
        if self.consensus_type == ConsensusType.UNANIMOUS:
            return total
        if self.consensus_type == ConsensusType.SUPERMAJORITY:
            return max(1, ceil((2 * total) / 3))
        return (total // 2) + 1


@dataclass(frozen=True)
class LaneEvaluationResult:
    lane_name: str
    risk_tier: RiskTier
    approval_set: ApprovalSet
    evidence_requirements: list[str] = field(default_factory=list)
    auto_approved: bool = False
    rationale: str = ""
    confidence_score: float = 0.0
    escalate: bool = False


class BaseGuardLane(ABC):
    """Abstract base class for governance guard lanes."""

    SLA_DEFAULTS = {
        RiskTier.L0: 0,
        RiskTier.L1: 4,
        RiskTier.L2: 8,
        RiskTier.L3: 24,
        RiskTier.L4: 72,
    }

    @property
    @abstractmethod
    def lane_name(self) -> str:
        """Unique lane name."""

    @property
    @abstractmethod
    def lane_enum(self) -> Any:
        """Enum value for persistence integration."""

    @property
    @abstractmethod
    def supported_triggers(self) -> set[TriggerType]:
        """Supported triggers for this lane."""

    @abstractmethod
    async def evaluate_event(self, event: GuardEvent) -> LaneEvaluationResult:
        """Evaluate an event and return risk/approval requirements."""

    @abstractmethod
    def get_evidence_requirements(self, tier: RiskTier) -> list[str]:
        """Required evidence by risk tier."""

    @abstractmethod
    def get_approval_set(self, tier: RiskTier) -> ApprovalSet:
        """Approval requirements by risk tier."""

    def can_handle(self, trigger: TriggerType) -> bool:
        return trigger in self.supported_triggers

    def default_sla_hours(self, tier: RiskTier) -> int:
        return self.SLA_DEFAULTS[tier]

    async def generate_evidence_bundle(
        self,
        event: GuardEvent,
        result: LaneEvaluationResult,
        *,
        parent_bundle_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate deterministic evidence bundle metadata with SHA-256 hash."""
        content = {
            "lane_name": result.lane_name,
            "event_id": event.event_id,
            "trigger": event.trigger.value,
            "risk_tier": result.risk_tier.value,
            "approval_set": {
                "approver_persona_ids": sorted(result.approval_set.approver_persona_ids),
                "consensus_type": result.approval_set.consensus_type.value,
                "delegation_allowed": result.approval_set.delegation_allowed,
                "sla_hours": result.approval_set.sla_hours,
                "required_approvers": result.approval_set.total_approvers_required(),
            },
            "evidence_requirements": result.evidence_requirements,
            "auto_approved": result.auto_approved,
            "rationale": result.rationale,
            "confidence_score": result.confidence_score,
            "escalate": result.escalate,
            "payload": event.payload,
            "metadata": event.metadata,
            "created_at": event.created_at,
        }
        canonical = json.dumps(content, sort_keys=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()
        return {
            "bundle_type": f"{self.lane_name}_evaluation",
            "content": content,
            "hash_sha256": digest,
            "parent_bundle_id": parent_bundle_id,
        }


class LaneRegistry:
    """Simple in-memory registry for lane dispatch."""

    _lanes: dict[str, BaseGuardLane] = {}

    @classmethod
    def register(cls, lane: BaseGuardLane) -> None:
        cls._lanes[lane.lane_name] = lane

    @classmethod
    def get(cls, lane_name: str) -> BaseGuardLane | None:
        return cls._lanes.get(lane_name)

    @classmethod
    def list(cls) -> list[BaseGuardLane]:
        return list(cls._lanes.values())

    @classmethod
    def clear(cls) -> None:
        cls._lanes.clear()

    @classmethod
    def find_lane_for_trigger(cls, trigger: TriggerType) -> list[BaseGuardLane]:
        return [lane for lane in cls._lanes.values() if lane.can_handle(trigger)]


def register_lane(lane: BaseGuardLane) -> BaseGuardLane:
    """Register a lane and return it for decorator-style usage."""
    LaneRegistry.register(lane)
    return lane

