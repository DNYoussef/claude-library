"""
Command Base Class Component

Abstract base class for Context Cascade slash commands.

Features:
- Argument parsing and validation
- Skill binding and routing
- Help generation
- Alias support

Example:
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
"""

from .base import (
    CommandBase,
    CommandArgs,
    CommandArg,
    CommandResult,
    CommandMetadata,
    CommandCategory,
    command_metadata,
    get_command,
    list_commands,
    list_commands_by_category,
)

__all__ = [
    "CommandBase",
    "CommandArgs",
    "CommandArg",
    "CommandResult",
    "CommandMetadata",
    "CommandCategory",
    "command_metadata",
    "get_command",
    "list_commands",
    "list_commands_by_category",
]
