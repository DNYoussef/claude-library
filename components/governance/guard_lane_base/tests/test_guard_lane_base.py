from __future__ import annotations

import asyncio

from components.governance.guard_lane_base import (
    ApprovalSet,
    BaseGuardLane,
    ConsensusType,
    GuardEvent,
    LaneEvaluationResult,
    LaneRegistry,
    RiskTier,
    TriggerType,
)


class DummyLane(BaseGuardLane):
    @property
    def lane_name(self) -> str:
        return "DUMMY_GUARD"

    @property
    def lane_enum(self) -> str:
        return "DUMMY_GUARD"

    @property
    def supported_triggers(self) -> set[TriggerType]:
        return {TriggerType.PR_OPENED}

    async def evaluate_event(self, event: GuardEvent) -> LaneEvaluationResult:
        return LaneEvaluationResult(
            lane_name=self.lane_name,
            risk_tier=RiskTier.L1,
            approval_set=self.get_approval_set(RiskTier.L1),
            evidence_requirements=self.get_evidence_requirements(RiskTier.L1),
            auto_approved=False,
            rationale="dummy evaluation",
            confidence_score=0.9,
        )

    def get_evidence_requirements(self, tier: RiskTier) -> list[str]:
        return ["code_review"] if tier != RiskTier.L0 else []

    def get_approval_set(self, tier: RiskTier) -> ApprovalSet:
        return ApprovalSet(
            approver_persona_ids={"proof_architect", "capital_steward", "attack_chain_disruptor"},
            consensus_type=ConsensusType.MAJORITY,
            sla_hours=self.default_sla_hours(tier),
        )


def test_approval_set_thresholds() -> None:
    majority = ApprovalSet(
        approver_persona_ids={"a", "b", "c", "d"},
        consensus_type=ConsensusType.MAJORITY,
    )
    supermajority = ApprovalSet(
        approver_persona_ids={"a", "b", "c", "d", "e", "f"},
        consensus_type=ConsensusType.SUPERMAJORITY,
    )
    unanimous = ApprovalSet(
        approver_persona_ids={"a", "b", "c"},
        consensus_type=ConsensusType.UNANIMOUS,
    )
    assert majority.total_approvers_required() == 3
    assert supermajority.total_approvers_required() == 4
    assert unanimous.total_approvers_required() == 3


def test_registry_trigger_lookup() -> None:
    LaneRegistry.clear()
    lane = DummyLane()
    LaneRegistry.register(lane)
    matched = LaneRegistry.find_lane_for_trigger(TriggerType.PR_OPENED)
    assert lane in matched
    assert LaneRegistry.find_lane_for_trigger(TriggerType.DEAL_CLOSED) == []


def test_evidence_bundle_contains_hash() -> None:
    lane = DummyLane()
    event = GuardEvent(trigger=TriggerType.PR_OPENED, event_id="evt-1")
    result = asyncio.run(lane.evaluate_event(event))
    bundle = asyncio.run(lane.generate_evidence_bundle(event, result))
    assert bundle["bundle_type"] == "DUMMY_GUARD_evaluation"
    assert len(bundle["hash_sha256"]) == 64

