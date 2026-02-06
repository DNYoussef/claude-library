"""
Runtime Dependency Manager

Utilities for checking and managing component dependencies at runtime.

Features:
- Check if component dependencies are installed
- Get missing dependencies for a component
- Install missing dependencies (optional)
- Domain-based dependency groups

Usage:
    from library.components.utilities.dependency_manager import (
        check_dependencies,
        get_missing_dependencies,
        DependencyChecker,
    )

    # Quick check
    ok, missing = check_dependencies(['fastapi', 'pydantic'])
    if not ok:
        print(f"Missing: {missing}")

    # Full checker
    checker = DependencyChecker()
    result = checker.check_component('api/fastapi_router')
"""

from .dependency_manager import (
    DependencyChecker,
    DependencyResult,
    DomainDependencies,
    check_dependencies,
    get_missing_dependencies,
    get_domain_dependencies,
    check_domain,
)

__all__ = [
    "DependencyChecker",
    "DependencyResult",
    "DomainDependencies",
    "check_dependencies",
    "get_missing_dependencies",
    "get_domain_dependencies",
    "check_domain",
]
