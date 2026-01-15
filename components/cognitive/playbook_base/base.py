"""
Playbook Base Class Component

Abstract base class for Context Cascade playbooks.

Playbooks are high-level orchestration workflows that:
- Define multi-phase execution plans
- Coordinate multiple skills and agents
- Handle complex task decomposition
- Provide checkpoint and recovery support

References:
- Context Cascade playbooks structure
- Ansible playbook patterns

Example:
    from library.components.cognitive.playbook_base import PlaybookBase, playbook_metadata

    @playbook_metadata(
        name="feature-development",
        phases=["analyze", "design", "implement", "test", "deploy"],
    )
    class FeatureDevelopmentPlaybook(PlaybookBase):
        async def run_phase(self, phase: str, context: PlaybookContext) -> PhaseResult:
            if phase == "analyze":
                return await self.analyze(context)
            # ... handle other phases
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar
from enum import Enum
from datetime import datetime
import asyncio
import logging
import json

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="PlaybookBase")


class PlaybookCategory(Enum):
    """Playbook categories."""
    DELIVERY = "delivery"
    QUALITY = "quality"
    RESEARCH = "research"
    OPERATIONS = "operations"
    ORCHESTRATION = "orchestration"


class PhaseStatus(Enum):
    """Phase execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CHECKPOINT = "checkpoint"


@dataclass
class PhaseSpec:
    """Specification for a playbook phase."""
    name: str
    description: str = ""
    skills: List[str] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)
    timeout: Optional[float] = None
    retry: int = 0
    checkpoint: bool = False  # Save state after this phase
    skip_on_error: bool = False


@dataclass
class PlaybookContext:
    """Context passed through playbook execution."""
    request: str
    args: Dict[str, Any] = field(default_factory=dict)
    project: Optional[str] = None
    session_id: Optional[str] = None
    phase_outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    checkpoint_path: Optional[str] = None


@dataclass
class PhaseResult:
    """Result of a phase execution."""
    phase_name: str
    status: PhaseStatus
    output: Any = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    skills_invoked: List[str] = field(default_factory=list)
    agents_spawned: List[str] = field(default_factory=list)


@dataclass
class PlaybookResult:
    """Result of full playbook execution."""
    success: bool
    phases: List[PhaseResult] = field(default_factory=list)
    final_output: Any = None
    error: Optional[str] = None
    total_duration_ms: Optional[float] = None
    checkpoint_restored: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlaybookMetadata:
    """Metadata for playbook registration."""
    name: str
    description: str = ""
    category: PlaybookCategory = PlaybookCategory.DELIVERY
    phases: List[PhaseSpec] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "claude-code"
    timeout: Optional[float] = None  # Total playbook timeout
    checkpoint_enabled: bool = True


# Registry for playbook classes
_playbook_registry: Dict[str, Type["PlaybookBase"]] = {}


def playbook_metadata(
    name: str,
    description: str = "",
    category: PlaybookCategory = PlaybookCategory.DELIVERY,
    phases: Optional[List[PhaseSpec]] = None,
    version: str = "1.0.0",
    author: str = "claude-code",
    timeout: Optional[float] = None,
    checkpoint_enabled: bool = True,
):
    """
    Decorator to register playbook metadata.

    Example:
        @playbook_metadata(
            name="feature-development",
            phases=[
                PhaseSpec("analyze", skills=["analyzer"]),
                PhaseSpec("design", skills=["architect"]),
                PhaseSpec("implement", skills=["code"], checkpoint=True),
                PhaseSpec("test", skills=["e2e-test"]),
                PhaseSpec("deploy", skills=["deployment"]),
            ],
        )
        class FeatureDevelopmentPlaybook(PlaybookBase):
            ...
    """
    def decorator(cls: Type[T]) -> Type[T]:
        metadata = PlaybookMetadata(
            name=name,
            description=description or cls.__doc__ or "",
            category=category,
            phases=phases or [],
            version=version,
            author=author,
            timeout=timeout,
            checkpoint_enabled=checkpoint_enabled,
        )
        cls._metadata = metadata
        _playbook_registry[name] = cls
        return cls
    return decorator


def get_playbook(name: str) -> Optional[Type["PlaybookBase"]]:
    """Get a registered playbook class by name."""
    return _playbook_registry.get(name)


def list_playbooks() -> List[str]:
    """List all registered playbook names."""
    return list(_playbook_registry.keys())


class PlaybookBase(ABC):
    """
    Abstract base class for Context Cascade playbooks.

    Playbooks orchestrate multi-phase workflows:
    - Define ordered phases with dependencies
    - Invoke skills and agents per phase
    - Support checkpoints for recovery
    - Handle errors and retries

    Example:
        @playbook_metadata(
            name="bug-fix-workflow",
            phases=[
                PhaseSpec("diagnose", skills=["debug"]),
                PhaseSpec("fix", skills=["fix-bug"], checkpoint=True),
                PhaseSpec("verify", skills=["e2e-test"]),
            ],
        )
        class BugFixWorkflowPlaybook(PlaybookBase):
            async def run_phase(self, phase: str, context: PlaybookContext) -> PhaseResult:
                if phase == "diagnose":
                    return await self.diagnose_bug(context)
                elif phase == "fix":
                    return await self.fix_bug(context)
                elif phase == "verify":
                    return await self.verify_fix(context)
    """

    _metadata: PlaybookMetadata = None

    def __init__(self):
        if self._metadata is None:
            raise TypeError(
                f"{self.__class__.__name__} must be decorated with @playbook_metadata"
            )

    @property
    def metadata(self) -> PlaybookMetadata:
        """Get playbook metadata."""
        return self._metadata

    @property
    def name(self) -> str:
        """Get playbook name."""
        return self._metadata.name

    @abstractmethod
    async def run_phase(self, phase: str, context: PlaybookContext) -> PhaseResult:
        """
        Execute a single phase. MUST be implemented by subclasses.

        Each phase typically:
        1. Gets input from context.phase_outputs
        2. Invokes skills/agents
        3. Returns PhaseResult with output
        """
        pass

    async def save_checkpoint(self, context: PlaybookContext, phase: str):
        """Save checkpoint after a phase."""
        if not context.checkpoint_path:
            return

        checkpoint_data = {
            "playbook": self.name,
            "current_phase": phase,
            "phase_outputs": context.phase_outputs,
            "metadata": context.metadata,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            with open(context.checkpoint_path, "w") as f:
                json.dump(checkpoint_data, f, indent=2, default=str)
            logger.info(f"Checkpoint saved at phase: {phase}")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    async def load_checkpoint(self, context: PlaybookContext) -> Optional[str]:
        """Load checkpoint and return the phase to resume from."""
        if not context.checkpoint_path:
            return None

        try:
            with open(context.checkpoint_path, "r") as f:
                data = json.load(f)

            if data.get("playbook") != self.name:
                return None

            context.phase_outputs = data.get("phase_outputs", {})
            context.metadata = data.get("metadata", {})

            return data.get("current_phase")
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None

    async def run(self, context: PlaybookContext) -> PlaybookResult:
        """
        Execute the full playbook.

        Lifecycle:
        1. Check for checkpoint to resume
        2. Execute phases in order
        3. Save checkpoints as configured
        4. Handle errors and retries
        """
        start_time = datetime.utcnow()
        result = PlaybookResult(success=False)
        phases_to_run = [p.name for p in self._metadata.phases]
        start_phase_idx = 0

        # Check for checkpoint
        if self._metadata.checkpoint_enabled:
            resume_phase = await self.load_checkpoint(context)
            if resume_phase:
                try:
                    start_phase_idx = phases_to_run.index(resume_phase) + 1
                    result.checkpoint_restored = True
                    logger.info(f"Resuming from checkpoint after phase: {resume_phase}")
                except ValueError:
                    pass

        # Execute phases
        for i in range(start_phase_idx, len(self._metadata.phases)):
            phase_spec = self._metadata.phases[i]
            phase_start = datetime.utcnow()

            # Execute with retries
            phase_result = None
            last_error = None
            for attempt in range(phase_spec.retry + 1):
                try:
                    if phase_spec.timeout:
                        phase_result = await asyncio.wait_for(
                            self.run_phase(phase_spec.name, context),
                            timeout=phase_spec.timeout,
                        )
                    else:
                        phase_result = await self.run_phase(phase_spec.name, context)

                    if phase_result.status == PhaseStatus.SUCCESS:
                        break
                    last_error = phase_result.error

                except asyncio.TimeoutError:
                    last_error = f"Phase timed out after {phase_spec.timeout}s"
                    phase_result = PhaseResult(
                        phase_name=phase_spec.name,
                        status=PhaseStatus.FAILED,
                        error=last_error,
                    )
                except Exception as e:
                    last_error = str(e)
                    phase_result = PhaseResult(
                        phase_name=phase_spec.name,
                        status=PhaseStatus.FAILED,
                        error=last_error,
                    )

                if attempt < phase_spec.retry:
                    logger.warning(
                        f"Phase {phase_spec.name} failed (attempt {attempt + 1}), retrying..."
                    )
                    await asyncio.sleep(1)  # Brief delay before retry

            # Calculate duration
            phase_end = datetime.utcnow()
            if phase_result:
                phase_result.duration_ms = (phase_end - phase_start).total_seconds() * 1000
                result.phases.append(phase_result)

            # Store output for next phase
            if phase_result and phase_result.output:
                context.phase_outputs[phase_spec.name] = phase_result.output

            # Handle failure
            if phase_result and phase_result.status == PhaseStatus.FAILED:
                if phase_spec.skip_on_error:
                    logger.warning(f"Skipping failed phase: {phase_spec.name}")
                    continue
                else:
                    result.error = f"Phase {phase_spec.name} failed: {last_error}"
                    break

            # Save checkpoint
            if phase_spec.checkpoint and self._metadata.checkpoint_enabled:
                await self.save_checkpoint(context, phase_spec.name)

        # Determine success
        failed_phases = [
            p for p in result.phases
            if p.status == PhaseStatus.FAILED
        ]
        result.success = len(failed_phases) == 0

        # Set final output
        if result.phases:
            result.final_output = context.phase_outputs

        # Calculate total duration
        end_time = datetime.utcnow()
        result.total_duration_ms = (end_time - start_time).total_seconds() * 1000

        return result

    def visualize(self) -> str:
        """Generate ASCII visualization of the playbook."""
        lines = [
            f"Playbook: {self.name}",
            "=" * 40,
            "",
        ]

        for i, phase in enumerate(self._metadata.phases):
            status = "[pending]"
            arrow = "  |" if i < len(self._metadata.phases) - 1 else "   "
            checkpoint = " [checkpoint]" if phase.checkpoint else ""
            lines.append(f"  [{i + 1}] {phase.name}{checkpoint}")
            if phase.skills:
                lines.append(f"      Skills: {', '.join(phase.skills)}")
            if phase.agents:
                lines.append(f"      Agents: {', '.join(phase.agents)}")
            lines.append(f"  {arrow}")
            lines.append(f"  v")

        return "\n".join(lines[:-2])  # Remove last arrow
