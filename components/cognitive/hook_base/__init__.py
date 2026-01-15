"""
Hook Base Class Component

Abstract base class for Context Cascade hooks.

Features:
- Lifecycle event interception
- State persistence
- Compliance tracking
- Pattern retention

Events:
- UserPromptSubmit: Before processing user message
- PreToolUse: Before a tool is invoked
- PostToolUse: After a tool completes
- PreCompact: Before context compaction
- Stop: When session ends

Example:
    from library.components.cognitive.hook_base import (
        HookBase,
        hook_metadata,
        HookContext,
        HookResult,
        HookEvent,
    )

    @hook_metadata(
        name="skill-reminder",
        event=HookEvent.PRE_TOOL_USE,
        matcher="Skill",
    )
    class SkillReminderHook(HookBase):
        async def execute(self, context: HookContext) -> HookResult:
            return HookResult(message="Remember: Skill -> Task -> TodoWrite")
"""

from .base import (
    HookBase,
    CompositeHook,
    HookContext,
    HookResult,
    HookMetadata,
    HookState,
    HookEvent,
    HookExitCode,
    hook_metadata,
    get_hook,
    list_hooks,
    list_hooks_by_event,
)

__all__ = [
    "HookBase",
    "CompositeHook",
    "HookContext",
    "HookResult",
    "HookMetadata",
    "HookState",
    "HookEvent",
    "HookExitCode",
    "hook_metadata",
    "get_hook",
    "list_hooks",
    "list_hooks_by_event",
]
