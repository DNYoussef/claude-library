# Script Base Class

Abstract base class for Context Cascade automation scripts.

## Features

- CLI argument parsing
- Cron scheduling support
- Structured logging
- Timeout handling

## Exports

| Export | Description |
|--------|-------------|
| `ScriptBase` | Abstract base class for all scripts |
| `ScriptArgs` | Arguments container for script execution |
| `ScriptArg` | Single argument specification |
| `ScriptResult` | Result of script execution |
| `ScriptMetadata` | Script metadata (name, schedule, etc.) |
| `ScriptCategory` | Enum for script categories |
| `LogLevel` | Logging levels (DEBUG, INFO, etc.) |
| `script_metadata` | Decorator for script metadata |
| `get_script` | Get script by name |
| `list_scripts` | List all registered scripts |

## Usage

```python
from library.components.cognitive.script_base import (
    ScriptBase,
    script_metadata,
    ScriptArgs,
    ScriptResult,
)

@script_metadata(
    name="cleanup-temp",
    schedule="0 3 * * 0",  # Weekly on Sunday at 3am
)
class CleanupTempScript(ScriptBase):
    async def run(self, args: ScriptArgs) -> ScriptResult:
        # Cleanup logic
        return ScriptResult(success=True)
```

## Related

- `scheduling/task_scheduler` - Task scheduler component
- `observability/audit_logging` - Audit logging component
