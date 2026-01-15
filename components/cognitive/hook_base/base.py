"""
Hook Base Class Component

Abstract base class for Context Cascade hooks.

Hooks are lifecycle interceptors that:
- Run at specific Claude Code events
- Inject context and reminders
- Track state and compliance
- Enable recursive improvement

References:
- Claude Code hooks documentation
- Context Cascade hooks/enforcement/

Events:
- UserPromptSubmit: Before processing user message
- PreToolUse: Before a tool is invoked
- PostToolUse: After a tool completes
- PreCompact: Before context compaction
- Stop: When session ends

Example:
    from library.components.cognitive.hook_base import HookBase, hook_metadata

    @hook_metadata(
        name="skill-enforcement",
        event=HookEvent.PRE_TOOL_USE,
        matcher="Skill",
    )
    class SkillEnforcementHook(HookBase):
        async def execute(self, context: HookContext) -> HookResult:
            # Validate skill usage
            return HookResult(message="Remember: Skill -> Task -> TodoWrite")
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar
from enum import Enum
from datetime import datetime
import json
import logging
import os

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="HookBase")


class HookEvent(Enum):
    """Claude Code hook events."""
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    PRE_COMPACT = "PreCompact"
    STOP = "Stop"


class HookExitCode(Enum):
    """Hook exit codes."""
    SUCCESS = 0           # Continue normally
    MODIFY_INPUT = 0      # For input modification (same as success)
    BLOCK = 2             # Block the action
    ERROR = 1             # Hook error (logged but continues)


@dataclass
class HookContext:
    """Context passed to hook execution."""
    event: HookEvent
    session_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Any] = None
    user_message: Optional[str] = None
    compact_reason: Optional[str] = None  # "manual" or "auto"
    state_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HookResult:
    """Result of hook execution."""
    exit_code: HookExitCode = HookExitCode.SUCCESS
    message: Optional[str] = None  # Message to display
    modified_input: Optional[Dict[str, Any]] = None  # For input modification
    state_updates: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class HookState:
    """Persistent hook state across a session."""
    session_id: str
    started_at: datetime
    skill_invocations: List[Dict[str, Any]] = field(default_factory=list)
    agent_spawns: List[Dict[str, Any]] = field(default_factory=list)
    violations: List[Dict[str, Any]] = field(default_factory=list)
    todos_created: bool = False
    current_phase: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "skill_invocations": self.skill_invocations,
            "agent_spawns": self.agent_spawns,
            "violations": self.violations,
            "todos_created": self.todos_created,
            "current_phase": self.current_phase,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HookState":
        return cls(
            session_id=data["session_id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            skill_invocations=data.get("skill_invocations", []),
            agent_spawns=data.get("agent_spawns", []),
            violations=data.get("violations", []),
            todos_created=data.get("todos_created", False),
            current_phase=data.get("current_phase"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class HookMetadata:
    """Metadata for hook registration."""
    name: str
    description: str = ""
    event: HookEvent = HookEvent.USER_PROMPT_SUBMIT
    matcher: Optional[str] = None  # Tool name pattern for tool events
    priority: int = 100  # Lower = runs first
    enabled: bool = True
    version: str = "1.0.0"


# Registry for hook classes
_hook_registry: Dict[str, Type["HookBase"]] = {}


def hook_metadata(
    name: str,
    description: str = "",
    event: HookEvent = HookEvent.USER_PROMPT_SUBMIT,
    matcher: Optional[str] = None,
    priority: int = 100,
    enabled: bool = True,
    version: str = "1.0.0",
):
    """
    Decorator to register hook metadata.

    Example:
        @hook_metadata(
            name="skill-tracker",
            event=HookEvent.POST_TOOL_USE,
            matcher="Skill",
            priority=50,
        )
        class SkillTrackerHook(HookBase):
            ...
    """
    def decorator(cls: Type[T]) -> Type[T]:
        metadata = HookMetadata(
            name=name,
            description=description or cls.__doc__ or "",
            event=event,
            matcher=matcher,
            priority=priority,
            enabled=enabled,
            version=version,
        )
        cls._metadata = metadata
        _hook_registry[name] = cls
        return cls
    return decorator


def get_hook(name: str) -> Optional[Type["HookBase"]]:
    """Get a registered hook class by name."""
    return _hook_registry.get(name)


def list_hooks() -> List[str]:
    """List all registered hook names."""
    return list(_hook_registry.keys())


def list_hooks_by_event(event: HookEvent) -> List[str]:
    """List hooks for a specific event."""
    return [
        name for name, cls in _hook_registry.items()
        if cls._metadata.event == event
    ]


class HookBase(ABC):
    """
    Abstract base class for Context Cascade hooks.

    Hooks intercept Claude Code lifecycle events to:
    - Inject reminders and context
    - Track skill/agent usage
    - Detect compliance violations
    - Enable pattern retention

    Example:
        @hook_metadata(
            name="todowrite-reminder",
            event=HookEvent.POST_TOOL_USE,
            matcher="Task",
        )
        class TodoWriteReminderHook(HookBase):
            async def execute(self, context: HookContext) -> HookResult:
                # Remind user to call TodoWrite after Task
                return HookResult(
                    message="Remember: After Task(), call TodoWrite() to track progress."
                )
    """

    _metadata: HookMetadata = None

    def __init__(self, state_path: Optional[str] = None):
        if self._metadata is None:
            raise TypeError(
                f"{self.__class__.__name__} must be decorated with @hook_metadata"
            )
        self._state_path = state_path or os.path.expanduser(
            "~/.claude/runtime/hook-state.json"
        )
        self._state: Optional[HookState] = None

    @property
    def metadata(self) -> HookMetadata:
        """Get hook metadata."""
        return self._metadata

    @property
    def name(self) -> str:
        """Get hook name."""
        return self._metadata.name

    def load_state(self) -> Optional[HookState]:
        """Load state from disk."""
        try:
            with open(self._state_path, "r") as f:
                data = json.load(f)
            self._state = HookState.from_dict(data)
            return self._state
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.warning(f"Failed to load hook state: {e}")
            return None

    def save_state(self, state: HookState):
        """Save state to disk."""
        try:
            os.makedirs(os.path.dirname(self._state_path), exist_ok=True)
            with open(self._state_path, "w") as f:
                json.dump(state.to_dict(), f, indent=2)
            self._state = state
        except Exception as e:
            logger.warning(f"Failed to save hook state: {e}")

    def init_state(self, session_id: str) -> HookState:
        """Initialize a new state for a session."""
        state = HookState(
            session_id=session_id,
            started_at=datetime.utcnow(),
        )
        self.save_state(state)
        return state

    def log_skill(self, skill_name: str, params: Optional[Dict] = None):
        """Log a skill invocation to state."""
        state = self.load_state()
        if state:
            state.skill_invocations.append({
                "skill": skill_name,
                "params": params or {},
                "timestamp": datetime.utcnow().isoformat(),
            })
            self.save_state(state)

    def log_agent(self, agent_type: str, task_desc: str):
        """Log an agent spawn to state."""
        state = self.load_state()
        if state:
            state.agent_spawns.append({
                "agent": agent_type,
                "task": task_desc,
                "timestamp": datetime.utcnow().isoformat(),
            })
            self.save_state(state)

    def log_violation(self, violation_type: str, details: str):
        """Log a compliance violation."""
        state = self.load_state()
        if state:
            state.violations.append({
                "type": violation_type,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
            })
            self.save_state(state)

    @abstractmethod
    async def execute(self, context: HookContext) -> HookResult:
        """
        Execute the hook. MUST be implemented by subclasses.

        Return HookResult with:
        - message: Text to display to user/Claude
        - exit_code: SUCCESS, BLOCK, or ERROR
        - state_updates: Updates to persist
        """
        pass

    async def run(self, context: HookContext) -> HookResult:
        """Execute the hook with error handling."""
        try:
            context.state_path = self._state_path
            result = await self.execute(context)

            # Apply state updates
            if result.state_updates:
                state = self.load_state()
                if state:
                    state.metadata.update(result.state_updates)
                    self.save_state(state)

            return result

        except Exception as e:
            logger.exception(f"Hook {self.name} failed")
            return HookResult(
                exit_code=HookExitCode.ERROR,
                error=str(e),
            )

    def to_settings_json(self) -> Dict[str, Any]:
        """Generate settings.json hook configuration."""
        config = {
            "type": "command",
            "command": f"python -m library.components.cognitive.hook_base.runner {self.name}",
        }

        entry = {"hooks": [config]}

        if self._metadata.matcher:
            entry["matcher"] = self._metadata.matcher

        return {self._metadata.event.value: [entry]}


class CompositeHook(HookBase):
    """
    A hook that runs multiple sub-hooks in sequence.

    Useful for combining related hook logic.
    """

    def __init__(self, state_path: Optional[str] = None):
        super().__init__(state_path)
        self._sub_hooks: List[HookBase] = []

    def add_hook(self, hook: HookBase):
        """Add a sub-hook."""
        self._sub_hooks.append(hook)

    async def execute(self, context: HookContext) -> HookResult:
        """Execute all sub-hooks."""
        messages = []
        all_updates = {}

        for hook in sorted(self._sub_hooks, key=lambda h: h.metadata.priority):
            result = await hook.run(context)

            if result.message:
                messages.append(result.message)
            all_updates.update(result.state_updates)

            if result.exit_code == HookExitCode.BLOCK:
                return HookResult(
                    exit_code=HookExitCode.BLOCK,
                    message="\n".join(messages),
                    state_updates=all_updates,
                )

        return HookResult(
            exit_code=HookExitCode.SUCCESS,
            message="\n".join(messages) if messages else None,
            state_updates=all_updates,
        )
