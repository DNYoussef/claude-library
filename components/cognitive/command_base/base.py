"""
Command Base Class Component

Abstract base class for Context Cascade slash commands.

Commands are the CLI interface layer that:
- Parse user input from slash commands
- Route to appropriate skills
- Handle argument parsing and validation
- Provide help and usage information

References:
- Context Cascade commands structure
- Typer CLI patterns

Example:
    from library.components.cognitive.command_base import CommandBase, command_metadata

    @command_metadata(
        name="fix-bug",
        aliases=["fb", "debug"],
        description="Fix a bug in the codebase",
    )
    class FixBugCommand(CommandBase):
        async def execute(self, args: CommandArgs) -> CommandResult:
            # Invoke the fix-bug skill
            return CommandResult(
                success=True,
                skill_to_invoke="fix-bug",
                args={"description": args.positional[0]},
            )
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="CommandBase")


class CommandCategory(Enum):
    """Command categories."""
    DELIVERY = "delivery"
    QUALITY = "quality"
    RESEARCH = "research"
    ORCHESTRATION = "orchestration"
    OPERATIONS = "operations"
    FOUNDRY = "foundry"
    TOOLING = "tooling"


@dataclass
class CommandArg:
    """Command argument specification."""
    name: str
    type: str = "string"  # string, int, float, bool, file, choice
    required: bool = False
    default: Any = None
    help: str = ""
    choices: Optional[List[str]] = None


@dataclass
class CommandArgs:
    """Parsed command arguments."""
    positional: List[str] = field(default_factory=list)
    named: Dict[str, Any] = field(default_factory=dict)
    flags: List[str] = field(default_factory=list)
    raw: str = ""


@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    skill_to_invoke: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None
    error: Optional[str] = None


@dataclass
class CommandMetadata:
    """Metadata for command registration."""
    name: str
    description: str = ""
    category: CommandCategory = CommandCategory.DELIVERY
    aliases: List[str] = field(default_factory=list)
    args: List[CommandArg] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    skill_binding: Optional[str] = None  # Skill to invoke by default
    hidden: bool = False
    version: str = "1.0.0"


# Registry for command classes
_command_registry: Dict[str, Type["CommandBase"]] = {}
_alias_registry: Dict[str, str] = {}  # alias -> command name


def command_metadata(
    name: str,
    description: str = "",
    category: CommandCategory = CommandCategory.DELIVERY,
    aliases: Optional[List[str]] = None,
    args: Optional[List[CommandArg]] = None,
    examples: Optional[List[str]] = None,
    skill_binding: Optional[str] = None,
    hidden: bool = False,
    version: str = "1.0.0",
):
    """
    Decorator to register command metadata.

    Example:
        @command_metadata(
            name="fix-bug",
            aliases=["fb", "debug"],
            description="Fix a bug in the codebase",
            skill_binding="fix-bug",
            args=[CommandArg("description", required=True, help="Bug description")],
        )
        class FixBugCommand(CommandBase):
            ...
    """
    def decorator(cls: Type[T]) -> Type[T]:
        metadata = CommandMetadata(
            name=name,
            description=description or cls.__doc__ or "",
            category=category,
            aliases=aliases or [],
            args=args or [],
            examples=examples or [],
            skill_binding=skill_binding,
            hidden=hidden,
            version=version,
        )
        cls._metadata = metadata
        _command_registry[name] = cls

        # Register aliases
        for alias in metadata.aliases:
            _alias_registry[alias] = name

        return cls
    return decorator


def get_command(name: str) -> Optional[Type["CommandBase"]]:
    """Get a registered command class by name or alias."""
    # Check if it's an alias
    if name in _alias_registry:
        name = _alias_registry[name]
    return _command_registry.get(name)


def list_commands() -> List[str]:
    """List all registered command names."""
    return list(_command_registry.keys())


def list_commands_by_category(category: CommandCategory) -> List[str]:
    """List commands in a specific category."""
    return [
        name for name, cls in _command_registry.items()
        if cls._metadata.category == category
    ]


class CommandBase(ABC):
    """
    Abstract base class for Context Cascade commands.

    Commands are the CLI interface that:
    - Parse /command user input
    - Route to appropriate skills
    - Handle argument validation
    - Provide help and usage

    Example:
        @command_metadata(
            name="build-feature",
            aliases=["bf", "feature"],
            skill_binding="build-feature",
        )
        class BuildFeatureCommand(CommandBase):
            async def execute(self, args: CommandArgs) -> CommandResult:
                return CommandResult(
                    success=True,
                    skill_to_invoke="build-feature",
                    args={"feature": args.positional[0]},
                )
    """

    _metadata: CommandMetadata = None

    def __init__(self):
        if self._metadata is None:
            raise TypeError(
                f"{self.__class__.__name__} must be decorated with @command_metadata"
            )

    @property
    def metadata(self) -> CommandMetadata:
        """Get command metadata."""
        return self._metadata

    @property
    def name(self) -> str:
        """Get command name."""
        return self._metadata.name

    def parse_args(self, raw_input: str) -> CommandArgs:
        """
        Parse raw command input into structured args.

        Supports:
        - Positional args: /cmd arg1 arg2
        - Named args: /cmd --name value
        - Flags: /cmd --verbose
        - Quoted strings: /cmd "multi word arg"
        """
        args = CommandArgs(raw=raw_input)

        # Remove command name
        parts = raw_input.strip().split(maxsplit=1)
        if len(parts) < 2:
            return args

        input_str = parts[1]

        # Parse with regex to handle quotes
        pattern = r'--(\w+)(?:=("[^"]*"|\S+))?|"([^"]*)"|(\S+)'
        matches = re.findall(pattern, input_str)

        i = 0
        while i < len(matches):
            match = matches[i]
            if match[0]:  # Named arg or flag
                name = match[0]
                value = match[1].strip('"') if match[1] else None
                if value is None:
                    # Check if next item is the value
                    if i + 1 < len(matches) and not matches[i + 1][0]:
                        value = matches[i + 1][2] or matches[i + 1][3]
                        i += 1
                    else:
                        # It's a flag
                        args.flags.append(name)
                        i += 1
                        continue
                args.named[name] = value
            elif match[2]:  # Quoted string
                args.positional.append(match[2])
            elif match[3]:  # Regular word
                args.positional.append(match[3])
            i += 1

        return args

    def validate_args(self, args: CommandArgs) -> List[str]:
        """
        Validate parsed args against metadata.

        Returns list of validation errors.
        """
        errors = []
        required_positional = [
            arg for arg in self._metadata.args
            if arg.required and arg.name not in ["--" + n for n in args.named]
        ]

        for i, spec in enumerate(required_positional):
            if i >= len(args.positional):
                errors.append(f"Missing required argument: {spec.name}")

        for name, value in args.named.items():
            spec = next(
                (a for a in self._metadata.args if a.name == name),
                None
            )
            if spec and spec.choices and value not in spec.choices:
                errors.append(
                    f"Invalid value for {name}: must be one of {spec.choices}"
                )

        return errors

    @abstractmethod
    async def execute(self, args: CommandArgs) -> CommandResult:
        """
        Execute the command. MUST be implemented by subclasses.

        Typically routes to a skill with parsed arguments.
        """
        pass

    async def run(self, raw_input: str) -> CommandResult:
        """
        Execute the full command lifecycle.

        1. Parse arguments
        2. Validate arguments
        3. Execute command
        """
        args = self.parse_args(raw_input)
        errors = self.validate_args(args)

        if errors:
            return CommandResult(
                success=False,
                error="; ".join(errors),
            )

        return await self.execute(args)

    def get_help(self) -> str:
        """Generate help text for this command."""
        lines = [
            f"/{self.name} - {self._metadata.description}",
            "",
        ]

        if self._metadata.aliases:
            lines.append(f"Aliases: {', '.join('/' + a for a in self._metadata.aliases)}")
            lines.append("")

        if self._metadata.args:
            lines.append("Arguments:")
            for arg in self._metadata.args:
                req = "(required)" if arg.required else "(optional)"
                lines.append(f"  {arg.name} {req}: {arg.help}")
            lines.append("")

        if self._metadata.examples:
            lines.append("Examples:")
            for ex in self._metadata.examples:
                lines.append(f"  {ex}")
            lines.append("")

        if self._metadata.skill_binding:
            lines.append(f"Invokes skill: {self._metadata.skill_binding}")

        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Generate markdown documentation for this command."""
        return f"""---
name: {self.name}
category: {self._metadata.category.value}
aliases: {self._metadata.aliases}
skill_binding: {self._metadata.skill_binding or 'none'}
---

# /{self.name}

{self._metadata.description}

## Usage

```
/{self.name} [arguments]
```

{self.get_help()}
"""
