from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest

MODULE_PATH = 'components.cognitive_architecture.loopctl.core'
EXPORTS = ['FrozenHarness', 'GradeMetrics', 'check_emergency_stop']


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


def test_frozen_harness_init():
    """Test FrozenHarness initialization."""
    module = _import_module()
    harness = module.FrozenHarness(harness_version="1.0.0", use_cli_evaluator=False)
    assert harness.harness_version == "1.0.0"
    assert harness.current_hash.startswith("frozen_eval_harness_v1.0.0_")


def test_frozen_harness_integrity():
    """Test harness integrity verification."""
    module = _import_module()
    harness = module.FrozenHarness(use_cli_evaluator=False)
    expected = harness.current_hash
    assert harness.verify_integrity(expected) is True
    assert harness.verify_integrity("wrong_hash") is False
    assert harness.verify_integrity(None) is True


def test_frozen_harness_audit_log():
    """Test audit logging functionality."""
    import tempfile
    module = _import_module()
    with tempfile.TemporaryDirectory() as tmpdir:
        harness = module.FrozenHarness(
            loop_dir=Path(tmpdir),
            use_cli_evaluator=False,
            enable_audit_log=True
        )
        # Create test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Test content for grading")

        # Grade should add to audit log
        harness.grade(test_file)
        assert len(harness.audit_log) == 1

        entry = harness.audit_log[0]
        assert "timestamp" in entry
        assert entry["harness_hash"] == harness.current_hash
        assert "metrics" in entry

        # Persist audit log
        log_path = harness.persist_audit_log()
        assert log_path.exists()

        # Clear audit log
        count = harness.clear_audit_log()
        assert count == 1
        assert len(harness.audit_log) == 0
