# Guard Lane Base Component

Abstract base class for building governance guard lanes with risk tier evaluation.

## Features

- Abstract guard lane pattern (ABC)
- TriggerType enum (20 event types)
- GuardEvent standardized event structure
- ApprovalSet with consensus calculation
- LaneEvaluationResult with escalation support
- LaneRegistry for polymorphic dispatch
- Evidence bundle generation with SHA-256 hashing
- SLA hour defaults by risk tier

## Source

Original implementation: life-os-dashboard guardspine module
This library now includes a self-contained Python implementation in
`guard_lane_base.py` with copy-ready defaults and registry helpers.

## Usage

```python
# When using in a project, adapt imports to your project structure:
from guardspine.lanes import (
    BaseGuardLane,
    TriggerType,
    GuardEvent,
    ApprovalSet,
    LaneEvaluationResult,
    LaneRegistry,
)
from schema.council.enums import RiskTierEnum, ConsensusTypeEnum, GuardLaneEnum

class CodeGuard(BaseGuardLane):
    """CODE_GUARD implementation for code quality gates."""

    @property
    def lane_name(self) -> str:
        return "CODE_GUARD"

    @property
    def lane_enum(self) -> GuardLaneEnum:
        return GuardLaneEnum.CODE_GUARD

    @property
    def supported_triggers(self) -> Set[TriggerType]:
        return {TriggerType.PR_OPENED, TriggerType.PR_MERGED, TriggerType.CODE_PUSHED}

    async def evaluate_event(self, event: GuardEvent) -> LaneEvaluationResult:
        # Determine risk tier based on event content
        is_security_change = event.metadata.get("security_related", False)
        risk_tier = RiskTierEnum.L3 if is_security_change else RiskTierEnum.L1

        return LaneEvaluationResult(
            lane_name=self.lane_name,
            risk_tier=risk_tier,
            approval_set=self.get_approval_set(risk_tier),
            evidence_requirements=self.get_evidence_requirements(risk_tier),
            auto_approved=(risk_tier == RiskTierEnum.L0),
            rationale=f"Security change: {is_security_change}",
            confidence_score=0.9
        )

    def get_evidence_requirements(self, tier: RiskTierEnum) -> List[str]:
        requirements = {
            RiskTierEnum.L0: [],
            RiskTierEnum.L1: ["code_review"],
            RiskTierEnum.L2: ["code_review", "test_results"],
            RiskTierEnum.L3: ["code_review", "test_results", "security_scan"],
            RiskTierEnum.L4: ["code_review", "test_results", "security_scan", "audit_log"],
        }
        return requirements.get(tier, [])

    def get_approval_set(self, tier: RiskTierEnum) -> ApprovalSet:
        if tier == RiskTierEnum.L0:
            return ApprovalSet(sla_hours=0)
        elif tier == RiskTierEnum.L1:
            return ApprovalSet(
                approver_persona_ids={"proof_architect"},
                sla_hours=4
            )
        elif tier in (RiskTierEnum.L2, RiskTierEnum.L3):
            return ApprovalSet(
                approver_persona_ids={"proof_architect", "attack_chain_disruptor"},
                consensus_type=ConsensusTypeEnum.MAJORITY,
                sla_hours=8 if tier == RiskTierEnum.L2 else 24
            )
        else:  # L4
            return ApprovalSet(
                approver_persona_ids={"proof_architect", "attack_chain_disruptor", "capital_steward"},
                consensus_type=ConsensusTypeEnum.UNANIMOUS,
                sla_hours=72,
                delegation_allowed=False
            )

# Register the lane
LaneRegistry.register(CodeGuard())

# Find lanes for a trigger
lanes = LaneRegistry.find_lane_for_trigger(TriggerType.PR_OPENED)
```

## Abstract Methods Required

| Method | Return Type | Purpose |
|--------|-------------|---------|
| `lane_name` (property) | `str` | Unique lane identifier |
| `lane_enum` (property) | `GuardLaneEnum` | Enum value for DB storage |
| `supported_triggers` (property) | `Set[TriggerType]` | Event types this lane handles |
| `evaluate_event()` | `LaneEvaluationResult` | Core evaluation logic |
| `get_evidence_requirements()` | `List[str]` | Evidence types per risk tier |
| `get_approval_set()` | `ApprovalSet` | Approval requirements per tier |

## TriggerType Values (20 types)

| Lane | Triggers |
|------|----------|
| CODE_GUARD | PR_OPENED, PR_MERGED, CODE_PUSHED |
| DEPLOY_GUARD | DEPLOY_REQUESTED, DEPLOY_COMPLETED, ROLLBACK_INITIATED |
| DATA_GUARD | DATA_ACCESS_REQUESTED, DATA_EXPORTED, PII_DETECTED |
| EVIDENCE_GUARD | EVIDENCE_SUBMITTED, AUDIT_REQUESTED |
| CONTRACT_GUARD | CONTRACT_DRAFTED, CONTRACT_SIGNED |
| COMMS_GUARD | COMMUNICATION_SENT, EXTERNAL_MESSAGE |
| TICKET_GUARD | TICKET_CREATED, TICKET_ESCALATED |
| DEAL_GUARD | DEAL_PROPOSED, DEAL_CLOSED, PRICING_CHANGED |

## Risk Tier SLA Defaults

| Tier | SLA Hours | Auto-Approve |
|------|-----------|--------------|
| L0 | 0 | Yes |
| L1 | 4 | No |
| L2 | 8 | No |
| L3 | 24 | No |
| L4 | 72 | No (human required) |

## ApprovalSet Consensus Calculation

```python
approval = ApprovalSet(
    approver_persona_ids={"p1", "p2", "p3", "p4"},
    consensus_type=ConsensusTypeEnum.MAJORITY
)
# total_approvers_required() returns 3 (>50% of 4)

approval = ApprovalSet(
    approver_persona_ids={"p1", "p2", "p3", "p4", "p5", "p6"},
    consensus_type=ConsensusTypeEnum.SUPERMAJORITY
)
# total_approvers_required() returns 5 (>2/3 of 6)
```

## Evidence Bundle Generation

```python
bundle = await guard.generate_evidence_bundle(event, result)
# Returns:
# {
#   "bundle_type": "CODE_GUARD_evaluation",
#   "content": {...},
#   "hash_sha256": "abc123...",
#   "parent_bundle_id": None
# }
```

## Related Components

- `auditor_base` - Similar ABC pattern for content auditors
- `quality_gate` - Quality gate utilities
- `circuit_breaker` - Failure handling pattern

## Tests

Included tests cover:
- Approval consensus thresholds
- Lane registry trigger dispatch
- Evidence bundle hashing

Run: `pytest components/governance/guard_lane_base/tests/test_guard_lane_base.py -v`
