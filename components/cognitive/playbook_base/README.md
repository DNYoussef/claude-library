# Playbook Base Class

Abstract base class for Context Cascade playbooks.

## Features

- Multi-phase orchestration
- Checkpoint and recovery
- Skill and agent coordination
- Error handling with retries

## Exports

| Export | Description |
|--------|-------------|
| `PlaybookBase` | Abstract base class for all playbooks |
| `PlaybookContext` | Execution context for playbook phases |
| `PlaybookResult` | Result of playbook execution |
| `PlaybookMetadata` | Playbook metadata (name, phases, etc.) |
| `PlaybookCategory` | Enum for playbook categories |
| `PhaseSpec` | Phase specification with skills and options |
| `PhaseResult` | Result of a single phase |
| `PhaseStatus` | Enum for phase status (pending, running, done) |
| `playbook_metadata` | Decorator for playbook metadata |
| `get_playbook` | Get playbook by name |
| `list_playbooks` | List all registered playbooks |

## Usage

```python
from library.components.cognitive.playbook_base import (
    PlaybookBase,
    playbook_metadata,
    PlaybookContext,
    PlaybookResult,
    PhaseSpec,
)

@playbook_metadata(
    name="feature-dev",
    phases=[
        PhaseSpec("analyze", skills=["analyzer"]),
        PhaseSpec("implement", skills=["code"], checkpoint=True),
    ],
)
class FeatureDevPlaybook(PlaybookBase):
    async def run_phase(self, phase, context) -> PhaseResult:
        # Phase logic
        pass
```

## Related

- `cognitive/skill_base` - Skill base class
- `cognitive/agent_base` - Agent base class
