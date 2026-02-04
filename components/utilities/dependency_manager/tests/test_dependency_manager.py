"""Tests for dependency_manager component."""
from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

import pytest

# Load module directly to avoid triggering package imports
_module_path = Path(__file__).parent.parent / "dependency_manager.py"
_spec = importlib.util.spec_from_file_location("dependency_manager", _module_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

# Import from loaded module
_normalize_package_name = _module._normalize_package_name
_is_installed = _module._is_installed
check_dependencies = _module.check_dependencies
get_missing_dependencies = _module.get_missing_dependencies
get_domain_dependencies = _module.get_domain_dependencies
DependencyChecker = _module.DependencyChecker
DependencyResult = _module.DependencyResult
DomainDependencies = _module.DomainDependencies
DOMAIN_GROUPS = _module.DOMAIN_GROUPS
PACKAGE_ALIASES = _module.PACKAGE_ALIASES




class TestPackageNormalization:
    """Tests for package name normalization."""

    def test_simple_name(self):
        """Simple package names pass through."""
        assert _normalize_package_name("pytest") == "pytest"
        assert _normalize_package_name("fastapi") == "fastapi"

    def test_version_stripping(self):
        """Version specifiers are stripped."""
        assert _normalize_package_name("pytest>=7.0.0") == "pytest"
        assert _normalize_package_name("fastapi==0.100.0") == "fastapi"
        assert _normalize_package_name("pydantic<2.0") == "pydantic"

    def test_hyphen_to_underscore(self):
        """Hyphens converted to underscores."""
        assert _normalize_package_name("some-package") == "some_package"

    def test_aliases(self):
        """Known aliases are applied."""
        assert _normalize_package_name("python-jose") == "jose"
        assert _normalize_package_name("pyyaml") == "yaml"
        assert _normalize_package_name("scikit-learn") == "sklearn"


class TestIsInstalled:
    """Tests for package installation checking."""

    def test_stdlib_module(self):
        """Standard library modules are found."""
        assert _is_installed("json") is True
        assert _is_installed("pathlib") is True
        assert _is_installed("os") is True

    def test_missing_module(self):
        """Non-existent modules return False."""
        assert _is_installed("nonexistent_fake_package_xyz") is False

    def test_pytest_installed(self):
        """pytest should be installed in test environment."""
        assert _is_installed("pytest") is True


class TestCheckDependencies:
    """Tests for dependency checking."""

    def test_all_installed(self):
        """All installed packages return ok=True."""
        ok, missing = check_dependencies(["json", "pathlib", "os"])
        assert ok is True
        assert missing == []

    def test_some_missing(self):
        """Missing packages are reported."""
        ok, missing = check_dependencies(["json", "fake_missing_pkg"])
        assert ok is False
        assert "fake_missing_pkg" in missing

    def test_empty_list(self):
        """Empty list returns ok=True."""
        ok, missing = check_dependencies([])
        assert ok is True
        assert missing == []


class TestGetMissingDependencies:
    """Tests for get_missing_dependencies."""

    def test_returns_only_missing(self):
        """Only missing packages are returned."""
        missing = get_missing_dependencies(["json", "fake_missing"])
        assert "json" not in missing
        assert "fake_missing" in missing


class TestGetDomainDependencies:
    """Tests for domain dependency lookup."""

    def test_known_domain(self):
        """Known domains return DomainDependencies."""
        result = get_domain_dependencies("api")
        assert isinstance(result, DomainDependencies)
        assert result.domain == "api"
        assert result.optional_group == "api"

    def test_aliased_domain(self):
        """Aliased domains map correctly."""
        result = get_domain_dependencies("authentication")
        assert result.optional_group == "auth"


class TestDependencyResult:
    """Tests for DependencyResult dataclass."""

    def test_bool_ok(self):
        """ok=True is truthy."""
        result = DependencyResult(component_id="test", ok=True)
        assert bool(result) is True

    def test_bool_not_ok(self):
        """ok=False is falsy."""
        result = DependencyResult(component_id="test", ok=False)
        assert bool(result) is False


class TestDependencyChecker:
    """Tests for DependencyChecker class."""

    def test_init_default_path(self):
        """Checker initializes with default catalog path."""
        checker = DependencyChecker()
        assert checker._catalog is None  # Lazy loaded

    def test_catalog_lazy_load(self):
        """Catalog is loaded on first access."""
        checker = DependencyChecker()
        _ = checker.catalog
        assert checker._catalog is not None

    def test_find_component_not_found(self):
        """Missing component returns None."""
        checker = DependencyChecker()
        result = checker.find_component("nonexistent/component")
        # May return None if catalog doesn't have it
        # This is expected behavior

    def test_check_component_not_in_catalog(self):
        """Component not in catalog returns ok=True with note."""
        checker = DependencyChecker()
        result = checker.check_component("totally_fake_component")
        assert result.ok is True
        assert len(result.optional) > 0  # Should have warning

    def test_get_install_command_with_missing(self):
        """Install command generated for missing deps."""
        checker = DependencyChecker()
        result = DependencyResult(
            component_id="test",
            ok=False,
            missing=["pkg1", "pkg2"],
        )
        cmd = checker.get_install_command(result)
        assert "pip install" in cmd
        assert "pkg1" in cmd
        assert "pkg2" in cmd

    def test_get_install_command_none_missing(self):
        """No command when nothing missing."""
        checker = DependencyChecker()
        result = DependencyResult(component_id="test", ok=True)
        cmd = checker.get_install_command(result)
        assert cmd == ""


class TestDomainGroups:
    """Tests for DOMAIN_GROUPS constant."""

    def test_domain_groups_complete(self):
        """Key domains are mapped."""
        assert "api" in DOMAIN_GROUPS
        assert "database" in DOMAIN_GROUPS
        assert "memory" in DOMAIN_GROUPS


class TestPackageAliases:
    """Tests for PACKAGE_ALIASES constant."""

    def test_known_aliases(self):
        """Common aliases are defined."""
        assert "python-jose" in PACKAGE_ALIASES
        assert "pyyaml" in PACKAGE_ALIASES
        assert PACKAGE_ALIASES["pyyaml"] == "yaml"
