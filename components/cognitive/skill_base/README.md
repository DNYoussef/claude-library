# Skill Base Class Component

Abstract base class for Context Cascade skills with lifecycle management and registry.

## Features

- Abstract lifecycle methods (setup, validate, execute, teardown)
- Metadata registry with decorator
- Hook system for cross-cutting concerns
- Async-first design
- Composite skill pattern for orchestration

## Usage

### Basic Skill

```python
from library.components.cognitive.skill_base import (
    SkillBase,
    skill_metadata,
    SkillContext,
    SkillResult,
    SkillCategory,
)

@skill_metadata(
    name="fix-bug",
    version="1.0.0",
    category=SkillCategory.DEVELOPMENT,
    triggers=["fix", "debug", "bug"],
    description="Diagnose and fix software bugs",
)
class FixBugSkill(SkillBase):
    async def execute(self, context: SkillContext) -> SkillResult:
        # Skill logic here
        bug_description = context.request
        fix = await self.diagnose_and_fix(bug_description)

        return SkillResult(
            success=True,
            output={"fix": fix},
            chain_to="tester",  # Optionally chain to another skill
        )

    async def diagnose_and_fix(self, description: str) -> str:
        # Implementation
        return "Fixed the bug"
```

### With Lifecycle Hooks

```python
@skill_metadata(name="deploy", category=SkillCategory.OPERATIONS)
class DeploySkill(SkillBase):
    async def setup(self, context: SkillContext) -> SkillResult:
        # Load configuration, check prerequisites
        self.config = await self.load_config()
        return SkillResult(success=True)

    async def validate(self, context: SkillContext) -> SkillResult:
        # Validate inputs and permissions
        if not context.args.get("environment"):
            return SkillResult(
                success=False,
                error="Environment is required",
            )
        return SkillResult(success=True)

    async def execute(self, context: SkillContext) -> SkillResult:
        # Main deployment logic
        env = context.args["environment"]
        await self.deploy_to(env)
        return SkillResult(success=True, output={"deployed_to": env})

    async def teardown(self, context: SkillContext, result: SkillResult) -> SkillResult:
        # Cleanup, logging
        await self.log_deployment(result)
        return result
```

### Composite Skills

```python
from library.components.cognitive.skill_base import CompositeSkill

@skill_metadata(name="full-workflow", category=SkillCategory.ORCHESTRATION)
class FullWorkflowSkill(CompositeSkill):
    def __init__(self):
        super().__init__()
        self.add_skill(AnalyzerSkill())
        self.add_skill(PlannerSkill())
        self.add_skill(ExecutorSkill())

# Usage
skill = FullWorkflowSkill()
result = await skill.run(context)
# Each sub-skill executes in sequence
```

### Registry Functions

```python
from library.components.cognitive.skill_base import get_skill, list_skills

# List all registered skills
skill_names = list_skills()
print(skill_names)  # ["fix-bug", "deploy", "full-workflow"]

# Get a skill class by name
SkillClass = get_skill("fix-bug")
skill = SkillClass()
result = await skill.run(context)
```

### Adding Hooks

```python
from library.components.cognitive.skill_base import SkillPhase

skill = FixBugSkill()

# Register a hook for the execute phase
def log_execution(skill, context):
    print(f"Executing skill: {skill.name}")

skill.register_hook(SkillPhase.EXECUTE, log_execution)
```

## API Reference

### SkillBase

Abstract base class that all skills must inherit from.

**Abstract Methods:**
- `execute(context: SkillContext) -> SkillResult` - Main execution logic

**Optional Override Methods:**
- `setup(context) -> SkillResult` - Initialization before execution
- `validate(context) -> SkillResult` - Input validation
- `teardown(context, result) -> SkillResult` - Cleanup after execution

**Properties:**
- `metadata: SkillMetadata` - Skill metadata
- `name: str` - Skill name

**Methods:**
- `run(context) -> SkillResult` - Execute full lifecycle
- `register_hook(phase, callback)` - Add phase hook

### SkillContext

```python
@dataclass
class SkillContext:
    request: str                    # User request
    args: Dict[str, Any]           # Arguments
    user_id: Optional[str]         # User identifier
    session_id: Optional[str]      # Session identifier
    project: Optional[str]         # Project name
    parent_skill: Optional[str]    # Calling skill
    memory: Dict[str, Any]         # Shared memory
    metadata: Dict[str, Any]       # Additional metadata
```

### SkillResult

```python
@dataclass
class SkillResult:
    success: bool                   # Success flag
    output: Any                     # Output data
    error: Optional[str]           # Error message
    duration_ms: Optional[float]   # Execution time
    phase: SkillPhase              # Current phase
    metadata: Dict[str, Any]       # Additional metadata
    chain_to: Optional[str]        # Next skill to invoke
```

### skill_metadata Decorator

```python
@skill_metadata(
    name="my-skill",                    # Required: Unique skill name
    version="1.0.0",                    # Version string
    category=SkillCategory.DEVELOPMENT, # Category for routing
    description="Description",          # Human-readable description
    triggers=["keyword1", "keyword2"],  # Trigger keywords
    dependencies=["other-skill"],       # Required skills
    chain_from=["source-skill"],        # Skills that chain to this
    chain_to=["target-skill"],          # Skills this chains to
    enabled=True,                       # Enable/disable
    author="claude-code",               # Author
)
class MySkill(SkillBase):
    ...
```

## Sources

- [pluginlib](https://github.com/Rockhopper-Technologies/pluginlib) - Plugin framework
- [decorated-plugins](https://kaleidoescape.github.io/decorated-plugins/) - Decorator pattern
- [python-patterns](https://github.com/faif/python-patterns) - Design patterns
