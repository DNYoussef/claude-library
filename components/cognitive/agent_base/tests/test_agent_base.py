from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.cognitive.agent_base'
EXPORTS = ['AgentBase', 'AgentCategory', 'AgentMetadata', 'AgentPhase', 'AgentResult', 'AgentStatus', 'AgentTask', 'AgentType', 'ArtifactContract', 'CompositeAgent', 'ConfidenceLevel', 'InputContract', 'MCPServer', 'MemoryTag', 'OutputContract', 'PerformanceMetrics', 'QualityGate', 'agent_metadata', 'get_agent', 'list_agents', 'list_agents_by_category']


def _import_module():
    return import_component_module(MODULE_PATH)

def test_module_imports():
    _import_module()


def test_exports_present():
    module = _import_module()
    if not EXPORTS:
        return
    missing = [name for name in EXPORTS if not hasattr(module, name)]
    assert not missing, f"Missing exports: {missing}"
