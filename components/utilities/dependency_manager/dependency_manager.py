"""
Runtime Dependency Manager

Utilities for checking component dependencies at runtime.
Works with the catalog.json to verify that required dependencies are installed.

Example:
    >>> checker = DependencyChecker()
    >>> result = checker.check_component('api/fastapi_router')
    >>> if not result.ok:
    ...     print(f"Missing: {result.missing}")
"""

from dataclasses import dataclass, field
from importlib.metadata import distributions, PackageNotFoundError
from importlib.util import find_spec
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import json


# Domain to pyproject.toml optional-dependency mapping
DOMAIN_GROUPS: Dict[str, str] = {
    "api": "api",
    "database": "database",
    "caching": "cache",
    "cache": "cache",
    "http": "http",
    "auth": "auth",
    "authentication": "auth",
    "observability": "observability",
    "memory": "memory",
    "content": "content",
    "pipelines": "content",
    "analysis": "analysis",
    "scheduling": "scheduling",
    "realtime": "realtime",
    "payments": "payments",
    "banking": "payments",
    "testing": "testing",
    "utilities": "yaml",
}

# Package name normalization (pypi name -> import name)
PACKAGE_ALIASES: Dict[str, str] = {
    "python-jose": "jose",
    "plaid-python": "plaid",
    "pyyaml": "yaml",
    "pillow": "PIL",
    "scikit-learn": "sklearn",
    "opencv-python": "cv2",
}


@dataclass
class DomainDependencies:
    """Dependencies for a domain"""
    domain: str
    packages: List[str]
    optional_group: str


@dataclass
class DependencyResult:
    """Result of dependency check"""
    component_id: str
    ok: bool
    installed: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    optional: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.ok


def _normalize_package_name(name: str) -> str:
    """Normalize package name for import checking"""
    # Remove version specifiers
    base_name = name.split(">=")[0].split("==")[0].split("<")[0].strip()
    # Check aliases
    return PACKAGE_ALIASES.get(base_name.lower(), base_name.lower().replace("-", "_"))


def _is_installed(package: str) -> bool:
    """Check if a package is installed"""
    import_name = _normalize_package_name(package)
    try:
        return find_spec(import_name) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def check_dependencies(packages: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if packages are installed.

    Args:
        packages: List of package names to check

    Returns:
        Tuple of (all_ok, missing_packages)

    Example:
        >>> ok, missing = check_dependencies(['fastapi', 'pydantic'])
        >>> if not ok:
        ...     print(f"Please install: {' '.join(missing)}")
    """
    missing = [p for p in packages if not _is_installed(p)]
    return len(missing) == 0, missing


def get_missing_dependencies(packages: List[str]) -> List[str]:
    """
    Get list of missing packages.

    Args:
        packages: List of package names to check

    Returns:
        List of packages that are not installed
    """
    return [p for p in packages if not _is_installed(p)]


def get_domain_dependencies(domain: str) -> DomainDependencies:
    """
    Get dependencies for a domain.

    Args:
        domain: Domain name (e.g., 'api', 'database', 'memory')

    Returns:
        DomainDependencies with package list and optional group name
    """
    # Map to optional-dependency group
    group = DOMAIN_GROUPS.get(domain.lower(), domain.lower())

    # Read from pyproject.toml if available
    pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"
    packages: List[str] = []

    if pyproject_path.exists():
        try:
            import tomllib
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            opt_deps = data.get("project", {}).get("optional-dependencies", {})
            packages = opt_deps.get(group, [])
        except ImportError:
            # Python < 3.11, try toml
            try:
                import toml
                data = toml.load(pyproject_path)
                opt_deps = data.get("project", {}).get("optional-dependencies", {})
                packages = opt_deps.get(group, [])
            except ImportError:
                pass

    return DomainDependencies(
        domain=domain,
        packages=packages,
        optional_group=group,
    )


def check_domain(domain: str) -> Tuple[bool, List[str]]:
    """
    Check if all dependencies for a domain are installed.

    Args:
        domain: Domain name

    Returns:
        Tuple of (all_ok, missing_packages)
    """
    deps = get_domain_dependencies(domain)
    return check_dependencies(deps.packages)


class DependencyChecker:
    """
    Full dependency checker with catalog support.

    Example:
        >>> checker = DependencyChecker()
        >>> result = checker.check_component('api/fastapi_router')
        >>> if not result:
        ...     print(f"Install: pip install {' '.join(result.missing)}")
    """

    def __init__(self, catalog_path: Optional[Path] = None):
        """
        Initialize checker.

        Args:
            catalog_path: Path to catalog.json. If None, uses default location.
        """
        if catalog_path is None:
            catalog_path = Path(__file__).parent.parent.parent.parent / "catalog.json"
        self._catalog_path = catalog_path
        self._catalog: Optional[Dict] = None

    @property
    def catalog(self) -> Dict:
        """Load catalog on first access"""
        if self._catalog is None:
            if self._catalog_path.exists():
                with open(self._catalog_path, "r", encoding="utf-8") as f:
                    self._catalog = json.load(f)
            else:
                self._catalog = {"components": []}
        return self._catalog

    def find_component(self, component_id: str) -> Optional[Dict]:
        """
        Find component by ID or location.

        Args:
            component_id: Component ID or partial location path

        Returns:
            Component dict or None if not found
        """
        for comp in self.catalog.get("components", []):
            if comp.get("id") == component_id:
                return comp
            if component_id in comp.get("location", ""):
                return comp
        return None

    def check_component(self, component_id: str) -> DependencyResult:
        """
        Check dependencies for a specific component.

        Args:
            component_id: Component ID or location pattern

        Returns:
            DependencyResult with installed/missing packages
        """
        comp = self.find_component(component_id)
        if comp is None:
            return DependencyResult(
                component_id=component_id,
                ok=True,
                missing=[],
                installed=[],
                optional=[f"Component '{component_id}' not found in catalog"],
            )

        deps = comp.get("dependencies", [])
        if not deps:
            return DependencyResult(
                component_id=comp.get("id", component_id),
                ok=True,
                installed=[],
                missing=[],
            )

        installed = []
        missing = []

        for dep in deps:
            if _is_installed(dep):
                installed.append(dep)
            else:
                missing.append(dep)

        return DependencyResult(
            component_id=comp.get("id", component_id),
            ok=len(missing) == 0,
            installed=installed,
            missing=missing,
        )

    def check_domain(self, domain: str) -> DependencyResult:
        """
        Check all components in a domain.

        Args:
            domain: Domain name

        Returns:
            DependencyResult with aggregated results
        """
        all_installed: Set[str] = set()
        all_missing: Set[str] = set()

        for comp in self.catalog.get("components", []):
            if comp.get("domain") == domain:
                result = self.check_component(comp.get("id"))
                all_installed.update(result.installed)
                all_missing.update(result.missing)

        return DependencyResult(
            component_id=f"domain:{domain}",
            ok=len(all_missing) == 0,
            installed=sorted(all_installed),
            missing=sorted(all_missing),
        )

    def get_install_command(self, result: DependencyResult) -> str:
        """
        Get pip install command for missing dependencies.

        Args:
            result: DependencyResult from check

        Returns:
            pip install command string
        """
        if not result.missing:
            return ""
        return f"pip install {' '.join(result.missing)}"


# Module-level convenience functions
_checker: Optional[DependencyChecker] = None


def _get_checker() -> DependencyChecker:
    """Get or create module-level checker"""
    global _checker
    if _checker is None:
        _checker = DependencyChecker()
    return _checker


def check_component(component_id: str) -> DependencyResult:
    """
    Check dependencies for a component.

    Args:
        component_id: Component ID or location pattern

    Returns:
        DependencyResult
    """
    return _get_checker().check_component(component_id)
