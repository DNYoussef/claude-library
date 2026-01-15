"""
Skill Base Class Component

Abstract base class for Context Cascade skills.

Features:
- Abstract lifecycle methods (setup, execute, teardown)
- Metadata registry (name, version, category, triggers)
- Hook system integration
- Async-first design

References:
- https://github.com/Rockhopper-Technologies/pluginlib
- https://kaleidoescape.github.io/decorated-plugins/

Example:
    from library.components.cognitive.skill_base import (
        SkillBase,
        skill_metadata,
        SkillContext,
        SkillResult,
        SkillCategory,
    )

    @skill_metadata(
        name="my-skill",
        version="1.0.0",
        category=SkillCategory.DEVELOPMENT,
    )
    class MySkill(SkillBase):
        async def execute(self, context: SkillContext) -> SkillResult:
            return SkillResult(success=True, output={"result": "done"})
"""

from .base import (
    # Core classes
    SkillBase,
    CompositeSkill,
    SkillContext,
    SkillResult,
    SkillMetadata,
    SkillCategory,
    SkillPhase,
    # New in v2.0: Contracts (from skill-forge/prompt-architect)
    InputContract,
    OutputContract,
    QualityScore,
    ConfidenceLevel,
    # Registry functions
    skill_metadata,
    get_skill,
    list_skills,
)

__all__ = [
    # Core classes
    "SkillBase",
    "CompositeSkill",
    "SkillContext",
    "SkillResult",
    "SkillMetadata",
    "SkillCategory",
    "SkillPhase",
    # New in v2.0: Contracts (from skill-forge/prompt-architect)
    "InputContract",
    "OutputContract",
    "QualityScore",
    "ConfidenceLevel",
    # Registry functions
    "skill_metadata",
    "get_skill",
    "list_skills",
]
