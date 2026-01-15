"""
Script Base Class Component

Abstract base class for Context Cascade automation scripts.

Scripts are standalone automation units that:
- Run independently or as part of pipelines
- Support CLI invocation with arguments
- Provide structured logging and output
- Integrate with cron scheduling

References:
- Typer CLI patterns
- Python script best practices

Example:
    from library.components.cognitive.script_base import ScriptBase, script_metadata

    @script_metadata(
        name="backup-memory",
        schedule="0 2 * * *",  # Daily at 2am
    )
    class BackupMemoryScript(ScriptBase):
        async def run(self, args: ScriptArgs) -> ScriptResult:
            # Backup memory MCP data
            await self.backup_to_cloud()
            return ScriptResult(success=True, message="Backup complete")
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypeVar
from enum import Enum
from datetime import datetime
import asyncio
import logging
import sys
import os

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="ScriptBase")


class ScriptCategory(Enum):
    """Script categories."""
    MAINTENANCE = "maintenance"
    AUTOMATION = "automation"
    ANALYSIS = "analysis"
    DEPLOYMENT = "deployment"
    BACKUP = "backup"
    MONITORING = "monitoring"


class LogLevel(Enum):
    """Script logging levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ScriptArg:
    """Script argument specification."""
    name: str
    type: str = "string"  # string, int, float, bool, file, path
    required: bool = False
    default: Any = None
    help: str = ""
    env_var: Optional[str] = None  # Environment variable fallback


@dataclass
class ScriptArgs:
    """Parsed script arguments."""
    positional: List[str] = field(default_factory=list)
    named: Dict[str, Any] = field(default_factory=dict)
    flags: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class ScriptResult:
    """Result of script execution."""
    success: bool
    message: Optional[str] = None
    output: Any = None
    error: Optional[str] = None
    exit_code: int = 0
    duration_ms: Optional[float] = None
    artifacts: List[str] = field(default_factory=list)  # Output file paths
    logs: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ScriptMetadata:
    """Metadata for script registration."""
    name: str
    description: str = ""
    category: ScriptCategory = ScriptCategory.AUTOMATION
    args: List[ScriptArg] = field(default_factory=list)
    schedule: Optional[str] = None  # Cron expression
    timeout: Optional[float] = None  # seconds
    requires: List[str] = field(default_factory=list)  # Required tools/deps
    version: str = "1.0.0"
    author: str = "claude-code"


# Registry for script classes
_script_registry: Dict[str, Type["ScriptBase"]] = {}


def script_metadata(
    name: str,
    description: str = "",
    category: ScriptCategory = ScriptCategory.AUTOMATION,
    args: Optional[List[ScriptArg]] = None,
    schedule: Optional[str] = None,
    timeout: Optional[float] = None,
    requires: Optional[List[str]] = None,
    version: str = "1.0.0",
    author: str = "claude-code",
):
    """
    Decorator to register script metadata.

    Example:
        @script_metadata(
            name="cleanup-temp",
            category=ScriptCategory.MAINTENANCE,
            schedule="0 3 * * 0",  # Weekly Sunday 3am
            args=[ScriptArg("days", type="int", default=7)],
        )
        class CleanupTempScript(ScriptBase):
            ...
    """
    def decorator(cls: Type[T]) -> Type[T]:
        metadata = ScriptMetadata(
            name=name,
            description=description or cls.__doc__ or "",
            category=category,
            args=args or [],
            schedule=schedule,
            timeout=timeout,
            requires=requires or [],
            version=version,
            author=author,
        )
        cls._metadata = metadata
        _script_registry[name] = cls
        return cls
    return decorator


def get_script(name: str) -> Optional[Type["ScriptBase"]]:
    """Get a registered script class by name."""
    return _script_registry.get(name)


def list_scripts() -> List[str]:
    """List all registered script names."""
    return list(_script_registry.keys())


class ScriptBase(ABC):
    """
    Abstract base class for Context Cascade scripts.

    Scripts are standalone automation units:
    - CLI-invocable with structured arguments
    - Support cron scheduling
    - Provide structured logging
    - Return structured results

    Example:
        @script_metadata(
            name="generate-report",
            args=[
                ScriptArg("output", required=True, help="Output path"),
                ScriptArg("format", default="json", help="Output format"),
            ],
        )
        class GenerateReportScript(ScriptBase):
            async def run(self, args: ScriptArgs) -> ScriptResult:
                output_path = args.named.get("output")
                format = args.named.get("format", "json")

                report = await self.generate_report(format)
                await self.save_report(report, output_path)

                return ScriptResult(
                    success=True,
                    message=f"Report saved to {output_path}",
                    artifacts=[output_path],
                )
    """

    _metadata: ScriptMetadata = None

    def __init__(self):
        if self._metadata is None:
            raise TypeError(
                f"{self.__class__.__name__} must be decorated with @script_metadata"
            )
        self._logs: List[Dict[str, Any]] = []

    @property
    def metadata(self) -> ScriptMetadata:
        """Get script metadata."""
        return self._metadata

    @property
    def name(self) -> str:
        """Get script name."""
        return self._metadata.name

    def log(self, level: LogLevel, message: str, **kwargs):
        """Add a structured log entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.value,
            "message": message,
            **kwargs,
        }
        self._logs.append(entry)
        getattr(logger, level.value)(f"[{self.name}] {message}")

    def log_info(self, message: str, **kwargs):
        """Log at INFO level."""
        self.log(LogLevel.INFO, message, **kwargs)

    def log_error(self, message: str, **kwargs):
        """Log at ERROR level."""
        self.log(LogLevel.ERROR, message, **kwargs)

    def log_warning(self, message: str, **kwargs):
        """Log at WARNING level."""
        self.log(LogLevel.WARNING, message, **kwargs)

    def log_debug(self, message: str, **kwargs):
        """Log at DEBUG level."""
        self.log(LogLevel.DEBUG, message, **kwargs)

    def parse_args(self, argv: Optional[List[str]] = None) -> ScriptArgs:
        """Parse command line arguments."""
        argv = argv or sys.argv[1:]
        args = ScriptArgs()

        # Get environment variables for args with env_var
        for arg_spec in self._metadata.args:
            if arg_spec.env_var and arg_spec.env_var in os.environ:
                args.env[arg_spec.name] = os.environ[arg_spec.env_var]

        i = 0
        while i < len(argv):
            arg = argv[i]

            if arg.startswith("--"):
                name = arg[2:]
                if "=" in name:
                    name, value = name.split("=", 1)
                    args.named[name] = value
                elif i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                    args.named[name] = argv[i + 1]
                    i += 1
                else:
                    args.flags.append(name)
            elif arg.startswith("-"):
                args.flags.append(arg[1:])
            else:
                args.positional.append(arg)

            i += 1

        # Apply defaults and env vars
        for arg_spec in self._metadata.args:
            if arg_spec.name not in args.named:
                if arg_spec.name in args.env:
                    args.named[arg_spec.name] = args.env[arg_spec.name]
                elif arg_spec.default is not None:
                    args.named[arg_spec.name] = arg_spec.default

        return args

    def validate_args(self, args: ScriptArgs) -> List[str]:
        """Validate parsed args. Returns list of errors."""
        errors = []

        for arg_spec in self._metadata.args:
            if arg_spec.required:
                if arg_spec.name not in args.named and arg_spec.name not in args.env:
                    errors.append(f"Missing required argument: --{arg_spec.name}")

        return errors

    @abstractmethod
    async def run(self, args: ScriptArgs) -> ScriptResult:
        """
        Execute the script. MUST be implemented by subclasses.

        Returns ScriptResult with success status, output, and artifacts.
        """
        pass

    async def execute(self, argv: Optional[List[str]] = None) -> ScriptResult:
        """
        Execute the full script lifecycle.

        1. Parse arguments
        2. Validate arguments
        3. Run script
        4. Return result with logs
        """
        start_time = datetime.utcnow()
        self._logs = []

        try:
            args = self.parse_args(argv)
            errors = self.validate_args(args)

            if errors:
                return ScriptResult(
                    success=False,
                    error="; ".join(errors),
                    exit_code=1,
                    logs=self._logs,
                )

            self.log_info(f"Starting script: {self.name}")

            if self._metadata.timeout:
                result = await asyncio.wait_for(
                    self.run(args),
                    timeout=self._metadata.timeout,
                )
            else:
                result = await self.run(args)

            result.logs = self._logs

        except asyncio.TimeoutError:
            result = ScriptResult(
                success=False,
                error=f"Script timed out after {self._metadata.timeout}s",
                exit_code=124,  # Standard timeout exit code
                logs=self._logs,
            )
        except Exception as e:
            self.log_error(f"Script failed: {e}")
            result = ScriptResult(
                success=False,
                error=str(e),
                exit_code=1,
                logs=self._logs,
            )

        # Calculate duration
        end_time = datetime.utcnow()
        result.duration_ms = (end_time - start_time).total_seconds() * 1000

        self.log_info(
            f"Script completed: success={result.success}, "
            f"duration={result.duration_ms:.0f}ms"
        )

        return result

    def get_help(self) -> str:
        """Generate help text."""
        lines = [
            f"{self.name} - {self._metadata.description}",
            "",
            "Usage:",
            f"  python -m {self.__module__} [OPTIONS]",
            "",
        ]

        if self._metadata.args:
            lines.append("Options:")
            for arg in self._metadata.args:
                req = "(required)" if arg.required else f"(default: {arg.default})"
                env = f" [env: {arg.env_var}]" if arg.env_var else ""
                lines.append(f"  --{arg.name} {req}{env}")
                if arg.help:
                    lines.append(f"      {arg.help}")

        if self._metadata.schedule:
            lines.extend(["", f"Schedule: {self._metadata.schedule}"])

        return "\n".join(lines)

    def to_crontab(self) -> Optional[str]:
        """Generate crontab entry for this script."""
        if not self._metadata.schedule:
            return None

        return f"{self._metadata.schedule} python -m {self.__module__}"
