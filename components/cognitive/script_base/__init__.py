"""
Script Base Class Component

Abstract base class for Context Cascade automation scripts.

Features:
- CLI argument parsing
- Cron scheduling support
- Structured logging
- Timeout handling

Example:
    from library.components.cognitive.script_base import (
        ScriptBase,
        script_metadata,
        ScriptArgs,
        ScriptResult,
    )

    @script_metadata(
        name="cleanup-temp",
        schedule="0 3 * * 0",  # Weekly
    )
    class CleanupTempScript(ScriptBase):
        async def run(self, args: ScriptArgs) -> ScriptResult:
            # Cleanup logic
            return ScriptResult(success=True)
"""

from .base import (
    ScriptBase,
    ScriptArgs,
    ScriptArg,
    ScriptResult,
    ScriptMetadata,
    ScriptCategory,
    LogLevel,
    script_metadata,
    get_script,
    list_scripts,
)

__all__ = [
    "ScriptBase",
    "ScriptArgs",
    "ScriptArg",
    "ScriptResult",
    "ScriptMetadata",
    "ScriptCategory",
    "LogLevel",
    "script_metadata",
    "get_script",
    "list_scripts",
]
