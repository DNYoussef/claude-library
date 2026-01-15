"""
Agent Base Class Component

Abstract base class for Context Cascade agents.

Features:
- Agent lifecycle (initialize, execute, cleanup)
- Capability and tool requirements
- MCP server integration
- Memory tagging protocol
- Quality gates and artifact contracts

References:
- Context Cascade agents/README.md
- https://github.com/Rockhopper-Technologies/pluginlib

Example:
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
    )
    class CodeReviewerAgent(AgentBase):
        async def execute(self, task: AgentTask) -> AgentResult:
            return AgentResult(success=True, output={"review": "..."})
"""

from .base import (
    # Core classes
    AgentBase,
    CompositeAgent,
    AgentTask,
    AgentResult,
    AgentMetadata,
    AgentCategory,
    AgentType,
    AgentPhase,
    AgentStatus,
    MemoryTag,
    MCPServer,
    QualityGate,
    ArtifactContract,
    # New in v2.0: Contracts and metrics (from agent-creator/prompt-architect)
    ConfidenceLevel,
    InputContract,
    OutputContract,
    PerformanceMetrics,
    # Registry functions
    agent_metadata,
    get_agent,
    list_agents,
    list_agents_by_category,
)

__all__ = [
    # Core classes
    "AgentBase",
    "CompositeAgent",
    "AgentTask",
    "AgentResult",
    "AgentMetadata",
    "AgentCategory",
    "AgentType",
    "AgentPhase",
    "AgentStatus",
    "MemoryTag",
    "MCPServer",
    "QualityGate",
    "ArtifactContract",
    # New in v2.0: Contracts and metrics (from agent-creator/prompt-architect)
    "ConfidenceLevel",
    "InputContract",
    "OutputContract",
    "PerformanceMetrics",
    # Registry functions
    "agent_metadata",
    "get_agent",
    "list_agents",
    "list_agents_by_category",
]
