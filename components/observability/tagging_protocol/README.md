# Tagging Protocol Component

WHO/WHEN/PROJECT/WHY metadata tagging for memory and logging operations.

This is the **canonical** generic tagging protocol. For Memory MCP-specific
usage with dataclass-based config, see:
`components/memory/memory_mcp_client/tagging_protocol.py`

## Features

- WHO: Agent identity and capabilities
- WHEN: Timestamps (ISO, Unix, readable)
- PROJECT: Project and task context
- WHY: Intent categorization (12 intent types)
- Flat tags for logging systems
- Method chaining with `update_context()`

## Usage

```python
from tagging_protocol import (
    TaggingProtocol,
    Intent, AgentCategory,
    create_simple_tagger,
    create_tagger
)

# Quick setup
tagger = create_simple_tagger("my-agent", "my-project")
tags = tagger.generate_tags(Intent.IMPLEMENTATION)

# Full configuration (direct initialization)
tagger = TaggingProtocol(
    agent_id="backend-worker",
    agent_category=AgentCategory.BACKEND,
    capabilities=["api-dev", "database"],
    project_id="proj-123",
    project_name="Life OS Dashboard"
)

# Or use factory function
tagger = create_tagger(
    agent_id="backend-worker",
    agent_category=AgentCategory.BACKEND,
    capabilities=["api-dev", "database"],
    project_id="proj-123",
    project_name="Life OS Dashboard"
)

# Generate tags with task context
tags = tagger.generate_tags(
    intent=Intent.BUGFIX,
    task_id="TASK-456"
)

# Output:
# {
#   "who": {"agent_id": "backend-worker", "category": "backend", ...},
#   "when": {"iso": "2026-01-10T...", "unix": 1767..., "readable": "..."},
#   "project": {"id": "proj-123", "name": "Life OS Dashboard", "task_id": "TASK-456"},
#   "why": {"intent": "bugfix"}
# }

# Flat tags for logging
flat = tagger.generate_flat_tags(Intent.TESTING)
# {"who.agent_id": "backend-worker", "when.iso": "...", ...}
```

## Intent Types

| Intent | Description |
|--------|-------------|
| IMPLEMENTATION | New feature implementation |
| BUGFIX | Bug fixing |
| REFACTOR | Code refactoring |
| TESTING | Test writing/running |
| DOCUMENTATION | Doc updates |
| ANALYSIS | Code/data analysis |
| PLANNING | Planning activities |
| RESEARCH | Research tasks |

## Agent Categories

CORE_DEVELOPMENT, TESTING_VALIDATION, FRONTEND, BACKEND, DATABASE,
DOCUMENTATION, SWARM_COORDINATION, PERFORMANCE, SECURITY, RESEARCH
