# Agent Base Class Component

Abstract base class for Context Cascade agents with lifecycle management and Memory MCP integration.

## Features

- Agent lifecycle (initialize, execute, cleanup)
- Capability and tool requirements
- MCP server integration
- Memory tagging protocol (WHO/WHEN/PROJECT/WHY)
- Quality gates and artifact contracts
- Composite agent pattern

## Usage

### Basic Agent

```python
from library.components.cognitive.agent_base import (
    AgentBase,
    agent_metadata,
    AgentTask,
    AgentResult,
    AgentCategory,
)

@agent_metadata(
    name="code-reviewer",
    category=AgentCategory.QUALITY,
    capabilities=["code-review", "security-analysis"],
    description="Reviews code for quality and security issues",
)
class CodeReviewerAgent(AgentBase):
    async def execute(self, task: AgentTask) -> AgentResult:
        review = await self.review_code(task.instructions)
        return AgentResult(
            success=True,
            output={"review": review},
            artifacts=[{"type": "review", "content": review}],
        )
```

### With Memory MCP Integration

```python
@agent_metadata(
    name="bug-fixer",
    category=AgentCategory.DELIVERY,
    mcp_servers=[MCPServer("memory-mcp", required=True)],
)
class BugFixerAgent(AgentBase):
    async def execute(self, task: AgentTask) -> AgentResult:
        # Create memory tag
        tag = self.create_memory_tag(
            project=task.context.get("project", "unknown"),
            why="bugfix",
        )

        fix = await self.diagnose_and_fix(task.description)

        return AgentResult(
            success=True,
            output={"fix": fix},
            memory_entries=[{
                **tag.to_dict(),
                "content": f"Fixed: {task.description}",
            }],
        )
```

### Composite Agents

```python
@agent_metadata(name="full-review", category=AgentCategory.QUALITY)
class FullReviewAgent(CompositeAgent):
    def __init__(self):
        super().__init__()
        self.add_agent(CodeReviewerAgent())
        self.add_agent(SecurityAuditorAgent())
        self.add_agent(PerformanceAnalyzerAgent())

# Usage
agent = FullReviewAgent()
result = await agent.run(task)
# All sub-agents execute and results are aggregated
```

## API Reference

### AgentBase

Abstract base class that all agents must inherit from.

**Abstract Methods:**
- `execute(task: AgentTask) -> AgentResult` - Main execution logic

**Optional Override Methods:**
- `initialize(task) -> bool` - Setup before execution
- `cleanup(task, result)` - Teardown after execution
- `validate_quality_gates(result) -> List[str]` - Quality validation

**Properties:**
- `metadata: AgentMetadata` - Agent metadata
- `name: str` - Agent name
- `agent_id: str` - Unique instance ID (name:uuid)
- `status: AgentStatus` - Current status

**Methods:**
- `run(task) -> AgentResult` - Execute full lifecycle
- `create_memory_tag(project, why) -> MemoryTag` - Create memory tag

### AgentTask

```python
@dataclass
class AgentTask:
    description: str              # Short task description
    instructions: str             # Detailed instructions
    args: Dict[str, Any]          # Additional arguments
    context: Dict[str, Any]       # Execution context
    parent_skill: Optional[str]   # Calling skill
    parent_agent: Optional[str]   # Calling agent (for composite)
    session_id: Optional[str]     # Session identifier
    timeout: Optional[float]      # Timeout in seconds
    memory_tag: Optional[MemoryTag]  # Memory tagging
```

### AgentResult

```python
@dataclass
class AgentResult:
    success: bool                  # Success flag
    output: Any                    # Output data
    error: Optional[str]           # Error message
    duration_ms: Optional[float]   # Execution time
    status: AgentStatus            # PENDING|RUNNING|SUCCESS|FAILED|TIMEOUT
    artifacts: List[Dict]          # Output artifacts
    metadata: Dict[str, Any]       # Additional metadata
    memory_entries: List[Dict]     # Memory MCP entries
```

### agent_metadata Decorator

```python
@agent_metadata(
    name="my-agent",                    # Required: Unique agent name
    description="Agent description",     # Human-readable description
    category=AgentCategory.DELIVERY,     # Category for organization
    agent_type=AgentType.CODER,         # Type by function
    phase=AgentPhase.DEVELOPMENT,       # Execution phase
    capabilities=["cap1", "cap2"],       # Agent capabilities
    tools_required=["tool1"],            # Required tools
    mcp_servers=[MCPServer("memory-mcp")],  # MCP requirements
    quality_gates=[QualityGate("tests", "test")],  # Quality gates
    hooks_pre="pre-hook.sh",             # Pre-execution hook
    hooks_post="post-hook.sh",           # Post-execution hook
)
class MyAgent(AgentBase):
    ...
```

## Memory Tagging Protocol

All memory writes should include WHO/WHEN/PROJECT/WHY:

```python
tag = agent.create_memory_tag(project="my-project", why="analysis")
# Returns MemoryTag with:
# - who: "agent-name:uuid"
# - when: datetime.utcnow()
# - project: "my-project"
# - why: "analysis"

# Use in memory entries:
result.memory_entries.append({
    **tag.to_dict(),
    "content": "Analysis findings...",
})
```

## Sources

- [Context Cascade agents/README.md](../../context-cascade/agents/README.md)
- [pluginlib](https://github.com/Rockhopper-Technologies/pluginlib)
