# Spec Validation Component

A generalized validation framework for specification documents including JSON schemas, markdown documents, and implementation plans.

## Installation

Copy the `spec-validation` directory to your project or add it to your Python path:

```python
import sys
sys.path.append("/path/to/spec-validation")
```

## Quick Start

```python
from spec_validation import SpecValidator, ValidationResult

# Basic usage with defaults
validator = SpecValidator("/path/to/specs")
results = validator.validate_all()

for result in results:
    print(result)

# Check if all validations pass
if validator.is_valid():
    print("All validations passed!")
```

## Features

- **Configurable Schemas**: Define custom validation rules for JSON files
- **Markdown Validation**: Check for required/recommended sections in markdown
- **Extensible Architecture**: Add custom validators via dependency injection
- **Detailed Results**: Get errors, warnings, and suggested fixes
- **Type Hints**: Full type annotations throughout

## Core Classes

### ValidationResult

Represents the result of a validation check.

```python
@dataclass
class ValidationResult:
    valid: bool           # Whether validation passed
    checkpoint: str       # Name of the validation checkpoint
    errors: List[str]     # List of error messages
    warnings: List[str]   # List of warning messages
    fixes: List[str]      # List of suggested fixes
    metadata: Dict        # Additional metadata
```

**Methods:**
- `to_dict()` - Convert to dictionary
- `from_dict(data)` - Create from dictionary
- `merge(other)` - Merge two results

### ValidationSchema

Configuration for validation rules.

```python
@dataclass
class ValidationSchema:
    required_fields: List[str]                    # Must be present
    optional_fields: List[str]                    # May be present
    allowed_values: Dict[str, List[str]]          # Field -> allowed values
    nested_schemas: Dict[str, ValidationSchema]   # Nested validation
    custom_validators: Dict[str, Callable]        # Custom validation functions
    required_fields_either: List[List[str]]       # At least one from each group
```

**Example:**
```python
from spec_validation import ValidationSchema

my_schema = ValidationSchema(
    required_fields=["name", "version"],
    optional_fields=["description", "author"],
    allowed_values={
        "type": ["feature", "bugfix", "refactor"],
    },
    required_fields_either=[["id", "uuid"]],  # Need at least one
)
```

### SpecValidator

Main orchestrator for all validations.

```python
validator = SpecValidator(
    spec_dir="/path/to/specs",
    context_schema=my_context_schema,           # Custom context.json schema
    implementation_plan_schema=my_plan_schema,  # Custom plan schema
    spec_required_sections=["Overview", "API"], # Custom required sections
    spec_recommended_sections=["Examples"],     # Custom recommended sections
    additional_validators={"custom": MyValidator},
    validator_configs={"prereqs": {"required_files": ["config.json"]}},
)
```

**Methods:**
- `validate_all()` - Run all validations
- `validate_prereqs()` - Check prerequisites
- `validate_context()` - Validate context.json
- `validate_spec_document()` - Validate spec.md
- `validate_implementation_plan()` - Validate implementation_plan.json
- `validate_checkpoint(name)` - Validate specific checkpoint
- `is_valid()` - Check if all pass
- `get_summary()` - Get summary dict
- `add_validator(name, validator)` - Add custom validator
- `remove_validator(name)` - Remove validator

## Individual Validators

### PrereqsValidator

Checks that the spec directory and required files exist.

```python
from spec_validation import PrereqsValidator

validator = PrereqsValidator(
    spec_dir="/path/to/specs",
    required_files=["config.json", "schema.json"],
    optional_files=["README.md"],
)
result = validator.validate()
```

### JSONFileValidator

Generic validator for any JSON file.

```python
from spec_validation import JSONFileValidator, ValidationSchema

schema = ValidationSchema(required_fields=["name", "type"])
validator = JSONFileValidator(
    spec_dir="/path/to/specs",
    filename="config.json",
    schema=schema,
    checkpoint_name="config",
    not_found_fix="Run init to generate config.json",
)
result = validator.validate()
```

### ContextValidator

Validates `context.json` with configurable schema.

```python
from spec_validation import ContextValidator

validator = ContextValidator(spec_dir="/path/to/specs")
# Or with custom schema:
validator = ContextValidator(spec_dir="/path/to/specs", schema=my_schema)
```

### MarkdownDocumentValidator

Validates markdown files for required sections.

```python
from spec_validation import MarkdownDocumentValidator

validator = MarkdownDocumentValidator(
    spec_dir="/path/to/specs",
    filename="design.md",
    checkpoint_name="design_doc",
    required_sections=["Overview", "Architecture"],
    recommended_sections=["Examples", "FAQ"],
    min_length=1000,
)
result = validator.validate()
```

### SpecDocumentValidator

Specialized validator for `spec.md`.

```python
from spec_validation import SpecDocumentValidator

validator = SpecDocumentValidator(
    spec_dir="/path/to/specs",
    required_sections=["Overview", "API"],  # Override defaults
)
```

### ImplementationPlanValidator

Deep validation of `implementation_plan.json` including phases and subtasks.

```python
from spec_validation import ImplementationPlanValidator

validator = ImplementationPlanValidator(spec_dir="/path/to/specs")
```

## Creating Custom Validators

Extend `BaseValidator` to create custom validators:

```python
from spec_validation import BaseValidator, ValidationResult

class SecurityValidator(BaseValidator):
    """Validates security requirements."""

    def __init__(self, spec_dir, security_level="standard"):
        super().__init__(spec_dir)
        self.security_level = security_level

    def validate(self) -> ValidationResult:
        errors = []
        warnings = []
        fixes = []

        # Custom validation logic
        security_file = self.spec_dir / "security.json"
        if not security_file.exists():
            if self.security_level == "strict":
                errors.append("security.json required for strict mode")
            else:
                warnings.append("security.json not found")

        return self._create_result(
            "security",
            errors=errors,
            warnings=warnings,
            fixes=fixes,
        )

# Use with SpecValidator
validator = SpecValidator(
    spec_dir="/path/to/specs",
    additional_validators={"security": SecurityValidator},
    validator_configs={"security": {"security_level": "strict"}},
)
```

## Default Schemas

The module provides several default schemas:

| Schema | Description |
|--------|-------------|
| `DEFAULT_CONTEXT_SCHEMA` | context.json validation |
| `DEFAULT_REQUIREMENTS_SCHEMA` | requirements.json validation |
| `DEFAULT_IMPLEMENTATION_PLAN_SCHEMA` | Full plan validation |
| `DEFAULT_PHASE_SCHEMA` | Phase structure validation |
| `DEFAULT_SUBTASK_SCHEMA` | Subtask structure validation |
| `DEFAULT_VERIFICATION_SCHEMA` | Verification step validation |
| `DEFAULT_SPEC_REQUIRED_SECTIONS` | Required spec.md sections |
| `DEFAULT_SPEC_RECOMMENDED_SECTIONS` | Recommended spec.md sections |

## Utility Functions

### validate_spec_directory

Quick validation without creating a validator instance:

```python
from spec_validation import validate_spec_directory

summary = validate_spec_directory("/path/to/specs")
print(f"Valid: {summary['all_valid']}")
print(f"Errors: {summary['total_errors']}")
```

### create_validator_from_config

Create a validator from a configuration dictionary:

```python
from spec_validation import create_validator_from_config

config = {
    "context_schema": {
        "required_fields": ["task_description", "author"],
    },
    "spec_required_sections": ["Overview", "API Reference"],
}

validator = create_validator_from_config("/path/to/specs", config)
```

## Expected Directory Structure

```
specs/
  context.json          # Discovery context
  requirements.json     # Original requirements (optional)
  spec.md               # Specification document
  implementation_plan.json  # Implementation phases
```

## API Reference

### ValidationResult Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `__str__()` | `str` | Human-readable format |
| `to_dict()` | `Dict` | Dictionary representation |
| `from_dict(data)` | `ValidationResult` | Create from dict |
| `merge(other)` | `ValidationResult` | Combine two results |

### SpecValidator Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `validate_all()` | `List[ValidationResult]` | Run all validators |
| `validate_prereqs()` | `ValidationResult` | Check prerequisites |
| `validate_context()` | `ValidationResult` | Validate context.json |
| `validate_spec_document()` | `ValidationResult` | Validate spec.md |
| `validate_implementation_plan()` | `ValidationResult` | Validate plan |
| `validate_checkpoint(name)` | `ValidationResult` | Validate by name |
| `is_valid()` | `bool` | All validations pass? |
| `get_summary()` | `Dict` | Full summary |
| `add_validator(name, v)` | `None` | Add custom validator |
| `remove_validator(name)` | `bool` | Remove validator |

## Version History

- **1.0.0** - Initial extraction from Life-OS Dashboard
  - Generalized schemas with ValidationSchema class
  - Injectable validators
  - Full type hints
  - Comprehensive documentation

## License

MIT License - Use freely in any project.
