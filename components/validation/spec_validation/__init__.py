"""
Spec Validation Component.

A generalized validation framework for specification documents.

Quick Start:
    from spec_validation import SpecValidator, ValidationResult

    validator = SpecValidator("/path/to/specs")
    if validator.is_valid():
        print("All validations passed!")
    else:
        for result in validator.validate_all():
            print(result)

Classes:
    - ValidationResult: Result of a validation check
    - ValidationSchema: Configurable schema for validation rules
    - BaseValidator: Abstract base class for custom validators
    - SpecValidator: Main orchestrator for all validations

Individual Validators:
    - PrereqsValidator: Validates prerequisites exist
    - JSONFileValidator: Generic JSON file validator
    - ContextValidator: Validates context.json
    - MarkdownDocumentValidator: Validates markdown documents
    - SpecDocumentValidator: Validates spec.md
    - ImplementationPlanValidator: Validates implementation_plan.json

Default Schemas:
    - DEFAULT_CONTEXT_SCHEMA
    - DEFAULT_REQUIREMENTS_SCHEMA
    - DEFAULT_IMPLEMENTATION_PLAN_SCHEMA
    - DEFAULT_PHASE_SCHEMA
    - DEFAULT_SUBTASK_SCHEMA
    - DEFAULT_VERIFICATION_SCHEMA
    - DEFAULT_SPEC_REQUIRED_SECTIONS
    - DEFAULT_SPEC_RECOMMENDED_SECTIONS

Utility Functions:
    - validate_spec_directory: Quick validation of a spec directory
    - create_validator_from_config: Create validator from config dict
"""

from .spec_validation import (
    # Core classes
    ValidationResult,
    ValidationSchema,
    BaseValidator,
    SpecValidator,
    # Individual validators
    PrereqsValidator,
    JSONFileValidator,
    ContextValidator,
    MarkdownDocumentValidator,
    SpecDocumentValidator,
    ImplementationPlanValidator,
    # Default schemas
    DEFAULT_CONTEXT_SCHEMA,
    DEFAULT_REQUIREMENTS_SCHEMA,
    DEFAULT_IMPLEMENTATION_PLAN_SCHEMA,
    DEFAULT_PHASE_SCHEMA,
    DEFAULT_SUBTASK_SCHEMA,
    DEFAULT_VERIFICATION_SCHEMA,
    DEFAULT_SPEC_REQUIRED_SECTIONS,
    DEFAULT_SPEC_RECOMMENDED_SECTIONS,
    # Utility functions
    validate_spec_directory,
    create_validator_from_config,
    # Type definitions
    Validatable,
    ValidatorFactory,
)

__version__ = "1.0.0"
__all__ = [
    # Core classes
    "ValidationResult",
    "ValidationSchema",
    "BaseValidator",
    "SpecValidator",
    # Individual validators
    "PrereqsValidator",
    "JSONFileValidator",
    "ContextValidator",
    "MarkdownDocumentValidator",
    "SpecDocumentValidator",
    "ImplementationPlanValidator",
    # Default schemas
    "DEFAULT_CONTEXT_SCHEMA",
    "DEFAULT_REQUIREMENTS_SCHEMA",
    "DEFAULT_IMPLEMENTATION_PLAN_SCHEMA",
    "DEFAULT_PHASE_SCHEMA",
    "DEFAULT_SUBTASK_SCHEMA",
    "DEFAULT_VERIFICATION_SCHEMA",
    "DEFAULT_SPEC_REQUIRED_SECTIONS",
    "DEFAULT_SPEC_RECOMMENDED_SECTIONS",
    # Utility functions
    "validate_spec_directory",
    "create_validator_from_config",
    # Type definitions
    "Validatable",
    "ValidatorFactory",
]
