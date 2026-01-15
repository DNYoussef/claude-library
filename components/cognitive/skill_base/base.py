"""
Skill Base Class Component

Abstract base class for Context Cascade skills. Based on plugin architecture
patterns from pluginlib and decorated-plugins.

References:
- https://github.com/Rockhopper-Technologies/pluginlib
- https://kaleidoescape.github.io/decorated-plugins/
- https://mathieularose.com/plugin-architecture-in-python

Features:
- Abstract lifecycle methods (setup, execute, teardown)
- Metadata registry (name, version, category, triggers)
- Hook system integration
- Validation and type checking
- Async-first design

Example:
    from library.components.cognitive.skill_base import SkillBase, skill_metadata

    @skill_metadata(
        name="my-skill",
        version="1.0.0",
        category="development",
        triggers=["fix", "build"],
    )
    class MySkill(SkillBase):
        async def execute(self, context: SkillContext) -> SkillResult:
            # Skill logic here
            return SkillResult(success=True, output={"result": "done"})
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar, Type, Union
from enum import Enum
from datetime import datetime
import asyncio
import logging

# LEGO Pattern: Import shared types from common/types with fallback
_types_imported = False

try:
    from library.common.types import (
        TaggedEntry, WhyCategory, QualityResult,
        ConfidenceLevel, InputContract, OutputContract
    )
    _types_imported = True
except ImportError:
    pass

if not _types_imported:
    try:
        from common.types import (
            TaggedEntry, WhyCategory, QualityResult,
            ConfidenceLevel, InputContract, OutputContract
        )
        _types_imported = True
    except ImportError:
        pass

if not _types_imported:
    # Fallback for standalone usage (LEGO pattern)
    from datetime import timezone

    @dataclass
    class TaggedEntry:
        who: str
        project: str
        why: str
        content: Any
        when: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    class WhyCategory(Enum):
        IMPLEMENTATION = "implementation"
        BUGFIX = "bugfix"
        REFACTOR = "refactor"
        TESTING = "testing"

    @dataclass
    class QualityResult:
        passed: bool
        score: float
        violations: List[Any] = field(default_factory=list)

    class ConfidenceLevel(Enum):
        HIGH = 0.8
        MEDIUM = 0.5
        LOW = 0.0

    @dataclass
    class InputContract:
        required: Dict[str, type] = field(default_factory=dict)
        optional: Dict[str, type] = field(default_factory=dict)

        def validate(self, inputs: Dict[str, Any]) -> tuple:
            errors = []
            for name, expected_type in self.required.items():
                if name not in inputs:
                    errors.append(f"Missing required input: {name}")
                elif not isinstance(inputs.get(name), expected_type):
                    errors.append(f"Invalid type for {name}: expected {expected_type.__name__}")
            return len(errors) == 0, errors

    @dataclass
    class OutputContract:
        required: Dict[str, type] = field(default_factory=dict)
        optional: Dict[str, type] = field(default_factory=dict)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="SkillBase")


class SkillCategory(Enum):
    """Skill categories for routing and organization."""
    DEVELOPMENT = "development"
    DELIVERY = "delivery"
    OPERATIONS = "operations"
    QUALITY = "quality"
    RESEARCH = "research"
    ORCHESTRATION = "orchestration"
    PLATFORMS = "platforms"
    SPECIALISTS = "specialists"
    SECURITY = "security"
    FOUNDRY = "foundry"
    TOOLING = "tooling"


class SkillPhase(Enum):
    """Skill execution phases (8-phase methodology from skill-forge)."""
    EXPERTISE_LOAD = "expertise_load"  # Phase 0: Load domain expertise
    SETUP = "setup"
    VALIDATE = "validate"
    EXECUTE = "execute"
    TEARDOWN = "teardown"


@dataclass
class QualityScore:
    """Quality scoring dimensions (from prompt-architect)."""
    clarity: float = 0.0          # 0.0-1.0, weight 0.25
    completeness: float = 0.0     # 0.0-1.0, weight 0.25
    precision: float = 0.0        # 0.0-1.0, weight 0.25
    technique_coverage: float = 0.0  # 0.0-1.0, weight 0.25

    @property
    def overall(self) -> float:
        """Weighted average of all dimensions."""
        return (
            self.clarity * 0.25 +
            self.completeness * 0.25 +
            self.precision * 0.25 +
            self.technique_coverage * 0.25
        )

    @property
    def passed(self) -> bool:
        """Check if overall score meets minimum threshold (0.7)."""
        return self.overall >= 0.7


@dataclass
class SkillContext:
    """Context passed to skill execution."""
    request: str
    args: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    project: Optional[str] = None
    parent_skill: Optional[str] = None
    memory: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Phase 0: Expertise loading (from skill-forge/agent-creator)
    expertise: Optional[Dict[str, Any]] = None
    expertise_file: Optional[str] = None
    # Uncertainty handling (from prompt-architect)
    confidence: float = 1.0
    assumptions: List[str] = field(default_factory=list)


@dataclass
class SkillResult:
    """Result of skill execution."""
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    phase: SkillPhase = SkillPhase.EXECUTE
    metadata: Dict[str, Any] = field(default_factory=dict)
    chain_to: Optional[str] = None  # Next skill to invoke
    # Quality scoring (from prompt-architect)
    quality_score: Optional[QualityScore] = None
    # Expertise delta - learnings to add to expertise (from skill-forge)
    expertise_delta: Optional[Dict[str, Any]] = None
    # Memory entries for persistence (WHO/WHEN/PROJECT/WHY)
    memory_entries: List[TaggedEntry] = field(default_factory=list)


@dataclass
class SkillMetadata:
    """Metadata for skill registration."""
    name: str
    version: str = "1.0.0"
    category: SkillCategory = SkillCategory.DEVELOPMENT
    description: str = ""
    triggers: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    chain_from: List[str] = field(default_factory=list)
    chain_to: List[str] = field(default_factory=list)
    enabled: bool = True
    author: str = "claude-code"
    # Input/Output contracts (from skill-forge/prompt-architect)
    input_contract: Optional[InputContract] = None
    output_contract: Optional[OutputContract] = None
    # Memory namespace pattern (from skill-forge)
    memory_namespace: str = ""  # e.g., "skill-forge/creations/{skill}"


# Registry for skill classes
_skill_registry: Dict[str, Type["SkillBase"]] = {}


def skill_metadata(
    name: str,
    version: str = "1.0.0",
    category: SkillCategory = SkillCategory.DEVELOPMENT,
    description: str = "",
    triggers: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
    chain_from: Optional[List[str]] = None,
    chain_to: Optional[List[str]] = None,
    enabled: bool = True,
    author: str = "claude-code",
    input_contract: Optional[InputContract] = None,
    output_contract: Optional[OutputContract] = None,
    memory_namespace: str = "",
):
    """
    Decorator to register skill metadata.

    Example:
        @skill_metadata(
            name="fix-bug",
            version="1.0.0",
            category=SkillCategory.DEVELOPMENT,
            triggers=["fix", "debug", "bug"],
            input_contract=InputContract(
                required={"bug_description": str},
                optional={"file_path": str}
            ),
            memory_namespace="fix-bug/fixes/{id}",
        )
        class FixBugSkill(SkillBase):
            ...
    """
    def decorator(cls: Type[T]) -> Type[T]:
        metadata = SkillMetadata(
            name=name,
            version=version,
            category=category,
            description=description or cls.__doc__ or "",
            triggers=triggers or [],
            dependencies=dependencies or [],
            chain_from=chain_from or [],
            chain_to=chain_to or [],
            enabled=enabled,
            author=author,
            input_contract=input_contract,
            output_contract=output_contract,
            memory_namespace=memory_namespace or f"{name}/executions/{{id}}",
        )
        cls._metadata = metadata
        _skill_registry[name] = cls
        return cls
    return decorator


def get_skill(name: str) -> Optional[Type["SkillBase"]]:
    """Get a registered skill class by name."""
    return _skill_registry.get(name)


def list_skills() -> List[str]:
    """List all registered skill names."""
    return list(_skill_registry.keys())


class SkillBase(ABC):
    """
    Abstract base class for Context Cascade skills.

    Skills are the primary unit of work orchestration. They:
    - Define lifecycle hooks (setup, execute, teardown)
    - Accept structured context
    - Return structured results
    - Support chaining to other skills

    Example:
        @skill_metadata(name="analyzer", category=SkillCategory.DEVELOPMENT)
        class AnalyzerSkill(SkillBase):
            async def execute(self, context: SkillContext) -> SkillResult:
                # Analyze user intent
                intent = await self.analyze_intent(context.request)
                return SkillResult(
                    success=True,
                    output={"intent": intent},
                    chain_to="planner",
                )
    """

    _metadata: SkillMetadata = None

    def __init__(self):
        if self._metadata is None:
            raise TypeError(
                f"{self.__class__.__name__} must be decorated with @skill_metadata"
            )
        self._hooks: Dict[SkillPhase, List[Callable]] = {
            phase: [] for phase in SkillPhase
        }

    @property
    def metadata(self) -> SkillMetadata:
        """Get skill metadata."""
        return self._metadata

    @property
    def name(self) -> str:
        """Get skill name."""
        return self._metadata.name

    def register_hook(
        self,
        phase: SkillPhase,
        hook: Callable[["SkillBase", SkillContext], Any],
    ):
        """Register a hook for a specific phase."""
        self._hooks[phase].append(hook)

    def create_memory_entry(
        self,
        project: str,
        why: Union[WhyCategory, str],
        content: Any,
    ) -> TaggedEntry:
        """Create a tagged entry for Memory MCP write.

        Args:
            project: Project name
            why: Reason from WhyCategory or custom string
            content: The data to store

        Returns:
            TaggedEntry ready for Memory MCP
        """
        why_value = why.value if isinstance(why, WhyCategory) else why
        return TaggedEntry(
            who=f"{self.name}:{self._metadata.version}",
            project=project,
            why=why_value,
            content=content,
        )

    def check_confidence(self, confidence: float) -> ConfidenceLevel:
        """Check confidence level and return appropriate action tier.

        From prompt-architect/skill-forge uncertainty handling:
        - >= 0.8: HIGH - proceed, document assumptions
        - 0.5-0.8: MEDIUM - present options, ask user
        - < 0.5: LOW - do NOT proceed, ask clarifying questions
        """
        if confidence >= ConfidenceLevel.HIGH.value:
            return ConfidenceLevel.HIGH
        elif confidence >= ConfidenceLevel.MEDIUM.value:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    async def load_expertise(self, context: SkillContext) -> Optional[Dict[str, Any]]:
        """Phase 0: Load domain expertise if available.

        From skill-forge/agent-creator Phase 0 methodology.
        Override to provide custom expertise loading.

        Returns:
            Expertise dict if available, None for discovery mode
        """
        if context.expertise_file:
            # Subclasses can override to load from file
            pass
        return context.expertise

    def validate_input_contract(self, context: SkillContext) -> tuple[bool, List[str]]:
        """Validate inputs against contract if defined."""
        if self._metadata.input_contract:
            return self._metadata.input_contract.validate(context.args)
        return True, []

    async def _run_hooks(self, phase: SkillPhase, context: SkillContext):
        """Run all hooks for a phase."""
        for hook in self._hooks[phase]:
            try:
                result = hook(self, context)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.warning(f"Hook error in {phase.value}: {e}")

    async def setup(self, context: SkillContext) -> SkillResult:
        """
        Optional setup phase. Override to perform initialization.

        Called before execute(). Use for:
        - Loading configuration
        - Validating prerequisites
        - Setting up resources
        """
        return SkillResult(success=True, phase=SkillPhase.SETUP)

    @abstractmethod
    async def execute(self, context: SkillContext) -> SkillResult:
        """
        Main execution phase. MUST be implemented by subclasses.

        This is where the skill's core logic lives.
        """
        pass

    async def teardown(self, context: SkillContext, result: SkillResult) -> SkillResult:
        """
        Optional teardown phase. Override to perform cleanup.

        Called after execute(), even if execute() failed. Use for:
        - Releasing resources
        - Logging results
        - Triggering follow-up actions
        """
        return result

    async def validate(self, context: SkillContext) -> SkillResult:
        """
        Optional validation phase. Override to validate inputs.

        Called after setup() but before execute(). Use for:
        - Input validation
        - Permission checks
        - Precondition verification
        """
        return SkillResult(success=True, phase=SkillPhase.VALIDATE)

    async def run(self, context: SkillContext) -> SkillResult:
        """
        Execute the full skill lifecycle (8-phase from skill-forge).

        Lifecycle order:
        0. Phase 0: Expertise Loading (from skill-forge/agent-creator)
        1. Contract Validation (input_contract check)
        2. Setup hooks + setup()
        3. Validate hooks + validate()
        4. Confidence check (uncertainty handling)
        5. Execute hooks + execute()
        6. Quality scoring
        7. Teardown hooks + teardown()
        """
        start_time = datetime.utcnow()
        result = SkillResult(success=False)

        try:
            # Phase 0: Expertise Loading (from skill-forge)
            await self._run_hooks(SkillPhase.EXPERTISE_LOAD, context)
            context.expertise = await self.load_expertise(context)

            # Contract validation (from prompt-architect)
            valid, errors = self.validate_input_contract(context)
            if not valid:
                return SkillResult(
                    success=False,
                    error=f"Input contract violation: {'; '.join(errors)}",
                    phase=SkillPhase.VALIDATE,
                )

            # Setup phase
            await self._run_hooks(SkillPhase.SETUP, context)
            result = await self.setup(context)
            if not result.success:
                return result

            # Validate phase
            await self._run_hooks(SkillPhase.VALIDATE, context)
            result = await self.validate(context)
            if not result.success:
                return result

            # Confidence check (uncertainty handling from prompt-architect)
            confidence_level = self.check_confidence(context.confidence)
            if confidence_level == ConfidenceLevel.LOW:
                return SkillResult(
                    success=False,
                    error="Confidence too low (<0.5). Ask clarifying questions before proceeding.",
                    phase=SkillPhase.VALIDATE,
                    metadata={"confidence": context.confidence, "assumptions": context.assumptions},
                )

            # Execute phase
            await self._run_hooks(SkillPhase.EXECUTE, context)
            result = await self.execute(context)

            # Add assumptions to metadata if confidence was medium
            if confidence_level == ConfidenceLevel.MEDIUM and context.assumptions:
                result.metadata["assumptions"] = context.assumptions
                result.metadata["confidence"] = context.confidence

        except Exception as e:
            logger.exception(f"Skill {self.name} failed")
            result = SkillResult(
                success=False,
                error=str(e),
                phase=SkillPhase.EXECUTE,
            )

        finally:
            # Teardown phase (always runs)
            try:
                await self._run_hooks(SkillPhase.TEARDOWN, context)
                result = await self.teardown(context, result)
            except Exception as e:
                logger.exception(f"Skill {self.name} teardown failed")
                if result.success:
                    result = SkillResult(
                        success=False,
                        error=f"Teardown failed: {e}",
                        phase=SkillPhase.TEARDOWN,
                    )

        # Calculate duration
        end_time = datetime.utcnow()
        result.duration_ms = (end_time - start_time).total_seconds() * 1000

        return result


class CompositeSkill(SkillBase):
    """
    A skill composed of multiple sub-skills.

    Executes sub-skills in sequence, passing results between them.

    Example:
        @skill_metadata(name="full-workflow", category=SkillCategory.ORCHESTRATION)
        class FullWorkflowSkill(CompositeSkill):
            def __init__(self):
                super().__init__()
                self.add_skill(AnalyzerSkill())
                self.add_skill(PlannerSkill())
                self.add_skill(ExecutorSkill())
    """

    def __init__(self):
        super().__init__()
        self._sub_skills: List[SkillBase] = []

    def add_skill(self, skill: SkillBase):
        """Add a sub-skill to the composition."""
        self._sub_skills.append(skill)

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute all sub-skills in sequence."""
        outputs = []
        last_result = None

        for skill in self._sub_skills:
            # Pass previous output to next skill
            if last_result and last_result.output:
                context.memory["previous_output"] = last_result.output

            last_result = await skill.run(context)
            outputs.append({
                "skill": skill.name,
                "success": last_result.success,
                "output": last_result.output,
            })

            if not last_result.success:
                return SkillResult(
                    success=False,
                    error=f"Sub-skill {skill.name} failed: {last_result.error}",
                    output=outputs,
                )

        return SkillResult(
            success=True,
            output=outputs,
        )
