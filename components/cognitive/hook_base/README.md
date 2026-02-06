# Hook Base Class

Abstract base class for Context Cascade hooks.

## Features

- Lifecycle event interception
- State persistence
- Compliance tracking
- Pattern retention

## Events

| Event | Trigger |
|-------|---------|
| `UserPromptSubmit` | Before processing user message |
| `PreToolUse` | Before a tool is invoked |
| `PostToolUse` | After a tool completes |
| `PreCompact` | Before context compaction |
| `Stop` | When session ends |

## Exports

| Export | Description |
|--------|-------------|
| `HookBase` | Abstract base class for all hooks |
| `CompositeHook` | Combine multiple hooks |
| `HookContext` | Context passed to hook execution |
| `HookResult` | Result of hook execution |
| `HookMetadata` | Hook metadata (name, event, matcher) |
| `HookState` | Persistent state for hooks |
| `HookEvent` | Enum for lifecycle events |
| `HookExitCode` | Exit codes (0=pass, 1=warn, 2=block) |
| `hook_metadata` | Decorator for hook metadata |
| `get_hook` | Get hook by name |
| `list_hooks` | List all registered hooks |
| `list_hooks_by_event` | List hooks filtered by event |

## Usage

```python
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
```

## Related

- `cognitive/skill_base` - Skill base class
- `cognitive/command_base` - Command base class
