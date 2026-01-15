"""
Agent Base Class Component

Abstract base class for Context Cascade agents. Based on the 260-agent
registry structure with YAML frontmatter patterns.

References:
- Context Cascade agents/README.md
- https://github.com/Rockhopper-Technologies/pluginlib

Features:
- Agent lifecycle (initialize, execute, cleanup)
- Capability and tool requirements
- MCP server integration
- Memory tagging protocol (WHO/WHEN/PROJECT/WHY)
- Hook integration points
- Quality gates and artifact contracts

Example:
    from library.components.cognitive.agent_base import AgentBase, agent_metadata

    @agent_metadata(
        name="code-reviewer",
        category=AgentCategory.QUALITY,
        capabilities=["code-review", "security-analysis"],
    )
    class CodeReviewerAgent(AgentBase):
        async def execute(self, task: AgentTask) -> AgentResult:
            # Review code logic
            return AgentResult(success=True, output={"review": "..."})
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar
from enum import Enum
from datetime import datetime
import asyncio
import logging
import uuid

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

T = TypeVar("T", bound="AgentBase")


class AgentCategory(Enum):
    """Agent categories matching Context Cascade taxonomy."""
    DELIVERY = "delivery"
    QUALITY = "quality"
    RESEARCH = "research"
    ORCHESTRATION = "orchestration"
    SECURITY = "security"
    PLATFORMS = "platforms"
    SPECIALISTS = "specialists"
    TOOLING = "tooling"
    FOUNDRY = "foundry"
    OPERATIONS = "operations"


class AgentType(Enum):
    """Agent types by function."""
    COORDINATOR = "coordinator"
    CODER = "coder"
    ANALYST = "analyst"
    OPTIMIZER = "optimizer"
    RESEARCHER = "researcher"
    SPECIALIST = "specialist"
    EXECUTOR = "executor"


class AgentPhase(Enum):
    """Agent execution phases."""
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"


class AgentStatus(Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


# MemoryTag is now TaggedEntry from common/types
# Re-export for backwards compatibility
MemoryTag = TaggedEntry


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics (from agent-creator Phase 4)."""
    tasks_completed: int = 0
    total_duration_ms: float = 0.0
    error_count: int = 0
    escalation_count: int = 0

    @property
    def avg_duration_ms(self) -> float:
        """Average task duration in milliseconds."""
        if self.tasks_completed == 0:
            return 0.0
        return self.total_duration_ms / self.tasks_completed

    @property
    def error_rate(self) -> float:
        """Error rate (failures / attempts)."""
        if self.tasks_completed == 0:
            return 0.0
        return self.error_count / self.tasks_completed

    def record_completion(self, duration_ms: float, success: bool, escalated: bool = False):
        """Record a task completion."""
        self.tasks_completed += 1
        self.total_duration_ms += duration_ms
        if not success:
            self.error_count += 1
        if escalated:
            self.escalation_count += 1


@dataclass
class AgentTask:
    """Task passed to agent execution."""
    description: str
    instructions: str
    args: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    parent_skill: Optional[str] = None
    parent_agent: Optional[str] = None
    session_id: Optional[str] = None
    timeout: Optional[float] = None  # seconds
    memory_tag: Optional[MemoryTag] = None
    # Phase 0: Expertise loading (from agent-creator)
    expertise: Optional[Dict[str, Any]] = None
    expertise_file: Optional[str] = None
    # Uncertainty handling (from agent-creator)
    confidence: float = 1.0
    assumptions: List[str] = field(default_factory=list)


@dataclass
class AgentResult:
    """Result of agent execution."""
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    status: AgentStatus = AgentStatus.SUCCESS
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    memory_entries: List[TaggedEntry] = field(default_factory=list)
    # Quality result (using shared type from common/types)
    quality_result: Optional[QualityResult] = None
    # Expertise delta - learnings for expertise update (from agent-creator)
    expertise_delta: Optional[Dict[str, Any]] = None
    # Performance metrics for this execution
    escalated: bool = False


@dataclass
class QualityGate:
    """Quality gate specification."""
    name: str
    type: str  # test|lint|security|performance
    threshold: float = 0.0
    required: bool = True
    script: Optional[str] = None


@dataclass
class ArtifactContract:
    """Artifact contract for agent outputs."""
    name: str
    type: str  # file|data|report
    required: bool = True
    schema: Optional[Dict[str, Any]] = None


@dataclass
class MCPServer:
    """MCP server requirement."""
    name: str
    required: bool = True
    auto_enable: bool = True


@dataclass
class AgentMetadata:
    """Metadata for agent registration."""
    name: str
    description: str = ""
    category: AgentCategory = AgentCategory.DELIVERY
    agent_type: AgentType = AgentType.CODER
    phase: AgentPhase = AgentPhase.DEVELOPMENT
    capabilities: List[str] = field(default_factory=list)
    tools_required: List[str] = field(default_factory=list)
    mcp_servers: List[MCPServer] = field(default_factory=list)
    quality_gates: List[QualityGate] = field(default_factory=list)
    artifact_contracts: List[ArtifactContract] = field(default_factory=list)
    hooks_pre: Optional[str] = None
    hooks_post: Optional[str] = None
    version: str = "1.0.0"
    author: str = "claude-code"
    enabled: bool = True
    # New in v2.0: Contracts and memory (from agent-creator)
    input_contract: Optional[InputContract] = None
    output_contract: Optional[OutputContract] = None
    memory_namespace: Optional[str] = None  # e.g., "agents/{category}/{name}"
    expertise_file: Optional[str] = None  # Path to domain expertise file


# Registry for agent classes
_agent_registry: Dict[str, Type["AgentBase"]] = {}


def agent_metadata(
    name: str,
    description: str = "",
    category: AgentCategory = AgentCategory.DELIVERY,
    agent_type: AgentType = AgentType.CODER,
    phase: AgentPhase = AgentPhase.DEVELOPMENT,
    capabilities: Optional[List[str]] = None,
    tools_required: Optional[List[str]] = None,
    mcp_servers: Optional[List[MCPServer]] = None,
    quality_gates: Optional[List[QualityGate]] = None,
    artifact_contracts: Optional[List[ArtifactContract]] = None,
    hooks_pre: Optional[str] = None,
    hooks_post: Optional[str] = None,
    version: str = "1.0.0",
    author: str = "claude-code",
    enabled: bool = True,
    # New in v2.0: Contracts and memory (from agent-creator)
    input_contract: Optional[InputContract] = None,
    output_contract: Optional[OutputContract] = None,
    memory_namespace: Optional[str] = None,
    expertise_file: Optional[str] = None,
):
    """
    Decorator to register agent metadata.

    Example:
        @agent_metadata(
            name="code-reviewer",
            category=AgentCategory.QUALITY,
            capabilities=["code-review", "security-analysis"],
            mcp_servers=[MCPServer("memory-mcp", required=True)],
            input_contract=InputContract(required={"code": str}),
            memory_namespace="agents/quality/code-reviewer",
        )
        class CodeReviewerAgent(AgentBase):
            ...
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Auto-generate memory namespace if not provided
        ns = memory_namespace or f"agents/{category.value}/{name}"

        metadata = AgentMetadata(
            name=name,
            description=description or cls.__doc__ or "",
            category=category,
            agent_type=agent_type,
            phase=phase,
            capabilities=capabilities or [],
            tools_required=tools_required or [],
            mcp_servers=mcp_servers or [MCPServer("memory-mcp", required=True)],
            quality_gates=quality_gates or [],
            artifact_contracts=artifact_contracts or [],
            hooks_pre=hooks_pre,
            hooks_post=hooks_post,
            version=version,
            author=author,
            enabled=enabled,
            input_contract=input_contract,
            output_contract=output_contract,
            memory_namespace=ns,
            expertise_file=expertise_file,
        )
        cls._metadata = metadata
        _agent_registry[name] = cls
        return cls
    return decorator


def get_agent(name: str) -> Optional[Type["AgentBase"]]:
    """Get a registered agent class by name."""
    return _agent_registry.get(name)


def list_agents() -> List[str]:
    """List all registered agent names."""
    return list(_agent_registry.keys())


def list_agents_by_category(category: AgentCategory) -> List[str]:
    """List agents in a specific category."""
    return [
        name for name, cls in _agent_registry.items()
        if cls._metadata.category == category
    ]


class AgentBase(ABC):
    """
    Abstract base class for Context Cascade agents.

    Agents are the execution units spawned by skills. They:
    - Receive structured tasks
    - Execute domain-specific logic
    - Return structured results with artifacts
    - Integrate with Memory MCP for persistence
    - Support quality gates and hooks

    Example:
        @agent_metadata(
            name="bug-fixer",
            category=AgentCategory.DELIVERY,
            capabilities=["debugging", "code-fix"],
        )
        class BugFixerAgent(AgentBase):
            async def execute(self, task: AgentTask) -> AgentResult:
                # Debug and fix the bug
                fix = await self.diagnose_and_fix(task.description)
                return AgentResult(
                    success=True,
                    output={"fix": fix},
                    artifacts=[{"type": "patch", "content": fix}],
                )
    """

    _metadata: AgentMetadata = None

    def __init__(self):
        if self._metadata is None:
            raise TypeError(
                f"{self.__class__.__name__} must be decorated with @agent_metadata"
            )
        self._id = str(uuid.uuid4())[:8]
        self._status = AgentStatus.PENDING

    @property
    def metadata(self) -> AgentMetadata:
        """Get agent metadata."""
        return self._metadata

    @property
    def name(self) -> str:
        """Get agent name."""
        return self._metadata.name

    @property
    def agent_id(self) -> str:
        """Get unique agent instance ID."""
        return f"{self._metadata.name}:{self._id}"

    @property
    def status(self) -> AgentStatus:
        """Get current status."""
        return self._status

    def create_memory_tag(self, project: str, why: str, content: Any) -> MemoryTag:
        """Create a memory tag for this agent.

        Args:
            project: Project name (required by TaggedEntry)
            why: Reason category (from WhyCategory or custom string)
            content: The actual data to store (required by TaggedEntry)

        Returns:
            MemoryTag (TaggedEntry) ready for Memory MCP write
        """
        return MemoryTag(
            who=self.agent_id,
            project=project,
            why=why,
            content=content,
        )

    def check_confidence(self, confidence: float) -> ConfidenceLevel:
        """Check confidence level tier (from agent-creator uncertainty handling).

        Args:
            confidence: Confidence score 0.0-1.0

        Returns:
            ConfidenceLevel tier (HIGH, MEDIUM, or LOW)

        Behavior by tier:
            - HIGH (>=0.8): Proceed with execution, document assumptions
            - MEDIUM (0.5-0.8): Present options, ask user to confirm
            - LOW (<0.5): Do NOT proceed, ask clarifying questions
        """
        if confidence >= ConfidenceLevel.HIGH.value:
            return ConfidenceLevel.HIGH
        elif confidence >= ConfidenceLevel.MEDIUM.value:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    async def load_expertise(self, task: AgentTask) -> Optional[Dict[str, Any]]:
        """Phase 0: Load domain expertise before execution (from agent-creator).

        Override to implement expertise loading from:
        - File system (expertise_file in metadata)
        - Memory MCP query
        - External knowledge base

        Args:
            task: The current task context

        Returns:
            Expertise dictionary or None if no expertise available
        """
        # Default: check if task has expertise or load from metadata path
        if task.expertise:
            return task.expertise

        if self._metadata.expertise_file:
            # Placeholder: In production, load from file
            logger.debug(f"Would load expertise from: {self._metadata.expertise_file}")
            return None

        return None

    def validate_input_contract(self, task: AgentTask) -> tuple[bool, List[str]]:
        """Validate task args against input contract (from agent-creator).

        Args:
            task: The task to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        if self._metadata.input_contract is None:
            return True, []  # No contract = always valid

        return self._metadata.input_contract.validate(task.args)

    def get_memory_namespace(self, suffix: str = "") -> str:
        """Get the memory namespace for this agent with optional suffix.

        Args:
            suffix: Optional suffix to append (e.g., "/{timestamp}")

        Returns:
            Full memory namespace string
        """
        base = self._metadata.memory_namespace or f"agents/{self._metadata.category.value}/{self.name}"
        if suffix:
            return f"{base}/{suffix}"
        return base

    async def initialize(self, task: AgentTask) -> bool:
        """
        Optional initialization. Override to perform setup.

        Called before execute(). Use for:
        - Loading configuration
        - Validating MCP servers are available
        - Setting up resources
        """
        return True

    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult:
        """
        Main execution. MUST be implemented by subclasses.

        This is where the agent's core logic lives.
        """
        pass

    async def cleanup(self, task: AgentTask, result: AgentResult):
        """
        Optional cleanup. Override to perform teardown.

        Called after execute(), even on failure. Use for:
        - Releasing resources
        - Logging to Memory MCP
        - Triggering post-hooks
        """
        pass

    async def validate_quality_gates(self, result: AgentResult) -> List[str]:
        """
        Validate result against quality gates.

        Returns list of failed gate names.
        """
        failures = []
        for gate in self._metadata.quality_gates:
            if gate.required:
                # Placeholder for actual gate validation
                # In production, this would run the gate script
                pass
        return failures

    async def run(self, task: AgentTask) -> AgentResult:
        """
        Execute the full agent lifecycle.

        Lifecycle (from agent-creator):
        0. Phase 0: Load expertise
        1. Validate input contract
        2. Check confidence level
        3. Run pre-hooks
        4. Initialize
        5. Execute
        6. Validate quality gates
        7. Run post-hooks
        8. Cleanup
        """
        start_time = datetime.utcnow()
        self._status = AgentStatus.RUNNING
        result = AgentResult(success=False, status=AgentStatus.FAILED)

        try:
            # Phase 0: Load expertise (from agent-creator)
            expertise = await self.load_expertise(task)
            if expertise:
                task.expertise = expertise
                logger.debug(f"Loaded expertise with {len(expertise)} entries")

            # Validate input contract (from agent-creator)
            contract_valid, contract_errors = self.validate_input_contract(task)
            if not contract_valid:
                result = AgentResult(
                    success=False,
                    error=f"Input contract validation failed: {'; '.join(contract_errors)}",
                    status=AgentStatus.FAILED,
                )
                return result

            # Check confidence level (from agent-creator)
            confidence_level = self.check_confidence(task.confidence)
            if confidence_level == ConfidenceLevel.LOW:
                # LOW confidence: require clarification before proceeding
                result = AgentResult(
                    success=False,
                    error=f"Confidence too low ({task.confidence:.2f}). Need clarification. Assumptions: {task.assumptions}",
                    status=AgentStatus.FAILED,
                    metadata={"confidence_level": "LOW", "assumptions": task.assumptions},
                )
                return result
            elif confidence_level == ConfidenceLevel.MEDIUM:
                # MEDIUM confidence: proceed but flag for review
                logger.warning(
                    f"Medium confidence ({task.confidence:.2f}). Proceeding with assumptions: {task.assumptions}"
                )

            # Pre-hooks (would run external script)
            if self._metadata.hooks_pre:
                logger.debug(f"Would run pre-hook: {self._metadata.hooks_pre}")

            # Initialize
            init_ok = await self.initialize(task)
            if not init_ok:
                result = AgentResult(
                    success=False,
                    error="Initialization failed",
                    status=AgentStatus.FAILED,
                )
                return result

            # Execute with optional timeout
            if task.timeout:
                try:
                    result = await asyncio.wait_for(
                        self.execute(task),
                        timeout=task.timeout,
                    )
                except asyncio.TimeoutError:
                    result = AgentResult(
                        success=False,
                        error=f"Execution timed out after {task.timeout}s",
                        status=AgentStatus.TIMEOUT,
                    )
            else:
                result = await self.execute(task)

            # Validate quality gates
            if result.success:
                failures = await self.validate_quality_gates(result)
                if failures:
                    result.metadata["quality_gate_failures"] = failures
                    logger.warning(f"Quality gates failed: {failures}")

            # Post-hooks
            if self._metadata.hooks_post:
                logger.debug(f"Would run post-hook: {self._metadata.hooks_post}")

        except Exception as e:
            logger.exception(f"Agent {self.name} failed")
            result = AgentResult(
                success=False,
                error=str(e),
                status=AgentStatus.FAILED,
            )

        finally:
            # Cleanup
            try:
                await self.cleanup(task, result)
            except Exception as e:
                logger.exception(f"Agent {self.name} cleanup failed")

            # Calculate duration
            end_time = datetime.utcnow()
            result.duration_ms = (end_time - start_time).total_seconds() * 1000

            # Update status
            if result.success:
                self._status = AgentStatus.SUCCESS
            else:
                self._status = result.status

        return result

    def to_yaml_frontmatter(self) -> str:
        """Generate YAML frontmatter for this agent."""
        meta = self._metadata
        lines = [
            "---",
            f"name: {meta.name}",
            f"type: {meta.agent_type.value}",
            f"phase: {meta.phase.value}",
            f"category: {meta.category.value}",
            f"description: {meta.description}",
            f"capabilities: {meta.capabilities}",
            f"tools_required: {meta.tools_required}",
            "mcp_servers:",
            "  required:",
        ]
        for mcp in meta.mcp_servers:
            if mcp.required:
                lines.append(f"    - {mcp.name}")
        lines.append("  optional:")
        for mcp in meta.mcp_servers:
            if not mcp.required:
                lines.append(f"    - {mcp.name}")
        lines.append("---")
        return "\n".join(lines)


class CompositeAgent(AgentBase):
    """
    An agent that coordinates multiple sub-agents.

    Useful for complex tasks requiring multiple specializations.
    """

    def __init__(self):
        super().__init__()
        self._sub_agents: List[AgentBase] = []

    def add_agent(self, agent: AgentBase):
        """Add a sub-agent."""
        self._sub_agents.append(agent)

    async def execute(self, task: AgentTask) -> AgentResult:
        """Execute all sub-agents and aggregate results."""
        outputs = []
        all_artifacts = []

        for agent in self._sub_agents:
            # Create sub-task with parent reference
            sub_task = AgentTask(
                description=task.description,
                instructions=task.instructions,
                args=task.args,
                context=task.context,
                parent_agent=self.agent_id,
                session_id=task.session_id,
                memory_tag=task.memory_tag,
            )

            result = await agent.run(sub_task)
            outputs.append({
                "agent": agent.name,
                "success": result.success,
                "output": result.output,
            })
            all_artifacts.extend(result.artifacts)

            if not result.success:
                return AgentResult(
                    success=False,
                    error=f"Sub-agent {agent.name} failed: {result.error}",
                    output=outputs,
                    artifacts=all_artifacts,
                )

        return AgentResult(
            success=True,
            output=outputs,
            artifacts=all_artifacts,
        )
