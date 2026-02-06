from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.memory.memory_mcp_client'
EXPORTS = ['AgentCategory', 'CacheLayer', 'CircuitBreaker', 'CircuitBreakerConfig', 'CircuitBreakerError', 'CircuitBreakerState', 'CircuitBreakerStatus', 'FallbackStorage', 'HealthStatus', 'INTENT_DESCRIPTIONS', 'InMemoryCache', 'InMemoryFallback', 'Intent', 'MCPTransport', 'MemoryMCPClient', 'MemoryMCPConfig', 'MemoryStorePayload', 'MemoryTags', 'MockMCPTransport', 'ProjectTag', 'StoreResult', 'TaggingConfig', 'TaggingProtocol', 'TaskHistoryResult', 'WhenTag', 'WhoTag', 'WhyTag', '__author__', '__source__', '__version__', 'create_backend_tagger', 'create_custom_tagger', 'create_frontend_tagger', 'create_memory_mcp_client', 'create_testing_tagger']


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
