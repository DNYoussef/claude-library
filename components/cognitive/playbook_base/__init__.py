"""
Playbook Base Class Component

Abstract base class for Context Cascade playbooks.

Features:
- Multi-phase orchestration
- Checkpoint and recovery
- Skill and agent coordination
- Error handling with retries

Example:
    from library.components.cognitive.playbook_base import (
        PlaybookBase,
        playbook_metadata,
        PlaybookContext,
        PlaybookResult,
        PhaseSpec,
    )

    @playbook_metadata(
        name="feature-dev",
        phases=[
            PhaseSpec("analyze", skills=["analyzer"]),
            PhaseSpec("implement", skills=["code"], checkpoint=True),
        ],
    )
    class FeatureDevPlaybook(PlaybookBase):
        async def run_phase(self, phase, context) -> PhaseResult:
            # Phase logic
            pass
"""

from .base import (
    PlaybookBase,
    PlaybookContext,
    PlaybookResult,
    PlaybookMetadata,
    PlaybookCategory,
    PhaseSpec,
    PhaseResult,
    PhaseStatus,
    playbook_metadata,
    get_playbook,
    list_playbooks,
)

__all__ = [
    "PlaybookBase",
    "PlaybookContext",
    "PlaybookResult",
    "PlaybookMetadata",
    "PlaybookCategory",
    "PhaseSpec",
    "PhaseResult",
    "PhaseStatus",
    "playbook_metadata",
    "get_playbook",
    "list_playbooks",
]
