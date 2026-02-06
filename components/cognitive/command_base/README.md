# Command Base Class

Abstract base class for Context Cascade slash commands.

## Features

- Argument parsing and validation
- Skill binding and routing
- Help generation
- Alias support

## Exports

| Export | Description |
|--------|-------------|
| `CommandBase` | Abstract base class for all commands |
| `CommandArgs` | Arguments container for command execution |
| `CommandArg` | Single argument specification |
| `CommandResult` | Result of command execution |
| `CommandMetadata` | Command metadata (name, aliases, skill) |
| `CommandCategory` | Enum for command categories |
| `command_metadata` | Decorator for command metadata |
| `get_command` | Get command by name or alias |
| `list_commands` | List all registered commands |
| `list_commands_by_category` | List commands filtered by category |

## Usage

```python
from library.components.cognitive.command_base import (
    CommandBase,
    command_metadata,
    CommandArgs,
    CommandResult,
)

@command_metadata(
    name="fix-bug",
    aliases=["fb"],
    skill_binding="fix-bug",
)
class FixBugCommand(CommandBase):
    async def execute(self, args: CommandArgs) -> CommandResult:
        return CommandResult(
            success=True,
            skill_to_invoke="fix-bug",
        )
```

## Related

- `cognitive/skill_base` - Skill base class
- `cognitive/agent_base` - Agent base class
