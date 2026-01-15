#!/usr/bin/env python3
"""
Library Component Deployment Script

Deploys a library component to target projects.

Usage:
    python deploy_component.py pydantic-base D:\Projects\life-os-dashboard\backend
    python deploy_component.py metric-collector D:\Projects\trader-ai
"""

import sys
import shutil
import json
from pathlib import Path
from typing import List, Dict, Optional

# Component mapping: component-id -> source path relative to library
COMPONENT_MAP = {
    "pydantic-base": "components/api/pydantic_base",
    "metric-collector": "components/analysis/metric_collector",
    "fastapi-router": "components/api/fastapi_router",
    "circuit-breaker": "components/utilities/circuit_breaker",
    "health-monitor": "components/utilities/health_monitor",
    "audit-logging": "components/observability/audit_logging",
    "jwt-auth": "components/security/jwt_auth",
    "tagging-protocol": "components/observability/tagging_protocol",
    "memory-mcp-client": "components/memory/memory_mcp_client",
}

# Projects that need each component (from audit)
COMPONENT_TARGETS = {
    "pydantic-base": [
        "agentwise", "claude-dev-cli", "content-pipeline", "corporate-council",
        "fog-compute", "life-os-dashboard", "life-os-frontend", "memory-mcp",
        "meta-calculus", "nsbu-rpg-app", "portfolio", "slop-detector",
        "the-agent-maker", "trader-ai"
    ],
    "metric-collector": [
        "agentic-commerce-arc", "agentwise", "claude-dev-cli", "connascence",
        "content-pipeline", "corporate-council", "fog-compute", "life-os-dashboard",
        "life-os-frontend", "memory-mcp", "meta-calculus", "nsbu-rpg-app",
        "portfolio", "slop-detector", "the-agent-maker", "trader-ai"
    ],
}

# Project paths
PROJECT_PATHS = {
    "memory-mcp": r"D:\Projects\memory-mcp-triple-system",
    "connascence": r"D:\Projects\connascence",
    "claude-dev-cli": r"D:\Projects\claude-dev-cli",
    "trader-ai": r"D:\Projects\trader-ai",
    "slop-detector": r"D:\Projects\slop-detector",
    "the-agent-maker": r"D:\Projects\the-agent-maker",
    "corporate-council": r"D:\Projects\corporate-council",
    "content-pipeline": r"C:\Users\17175\scripts\content-pipeline",
    "meta-calculus": r"D:\Projects\meta-calculus",
    "fog-compute": r"D:\Projects\fog-compute",
    "life-os-dashboard": r"D:\Projects\life-os-dashboard\backend",
    "life-os-frontend": r"D:\Projects\life-os-frontend",
    "nsbu-rpg-app": r"D:\Projects\nsbu-rpg-app",
    "portfolio": r"D:\Projects\dnyoussef-portfolio",
    "agentwise": r"D:\Projects\agentwise",
    "agentic-commerce-arc": r"D:\Projects\agentic-commerce-arc",
}

LIBRARY_ROOT = Path(r"C:\Users\17175\.claude\library")


def get_component_path(component_id: str) -> Optional[Path]:
    """Get the source path for a component."""
    if component_id not in COMPONENT_MAP:
        print(f"Unknown component: {component_id}")
        return None
    return LIBRARY_ROOT / COMPONENT_MAP[component_id]


def deploy_to_project(component_id: str, project_path: Path) -> bool:
    """Deploy a component to a project."""
    source = get_component_path(component_id)
    if not source or not source.exists():
        print(f"Source not found: {source}")
        return False

    # Determine destination (prefer lib/library or src/lib)
    dest_options = [
        project_path / "lib" / "library" / component_id.replace("-", "_"),
        project_path / "src" / "lib" / component_id.replace("-", "_"),
        project_path / "app" / "lib" / component_id.replace("-", "_"),
    ]

    dest = None
    for opt in dest_options:
        if opt.parent.exists():
            dest = opt
            break

    if not dest:
        # Create lib/library folder
        dest = project_path / "lib" / "library" / component_id.replace("-", "_")
        dest.parent.mkdir(parents=True, exist_ok=True)

    # Copy component
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)

    print(f"Deployed {component_id} to {dest}")
    return True


def deploy_component_to_all(component_id: str) -> Dict[str, bool]:
    """Deploy a component to all target projects."""
    results = {}
    targets = COMPONENT_TARGETS.get(component_id, [])

    for project in targets:
        if project not in PROJECT_PATHS:
            print(f"Unknown project: {project}")
            results[project] = False
            continue

        project_path = Path(PROJECT_PATHS[project])
        if not project_path.exists():
            print(f"Project path not found: {project_path}")
            results[project] = False
            continue

        results[project] = deploy_to_project(component_id, project_path)

    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python deploy_component.py <component-id> [project-path]")
        print(f"Available components: {', '.join(COMPONENT_MAP.keys())}")
        sys.exit(1)

    component_id = sys.argv[1]

    if len(sys.argv) > 2:
        # Deploy to specific project
        project_path = Path(sys.argv[2])
        success = deploy_to_project(component_id, project_path)
        sys.exit(0 if success else 1)
    else:
        # Deploy to all target projects
        results = deploy_component_to_all(component_id)
        success_count = sum(1 for v in results.values() if v)
        print(f"\nDeployed to {success_count}/{len(results)} projects")
        sys.exit(0 if success_count == len(results) else 1)


if __name__ == "__main__":
    main()
