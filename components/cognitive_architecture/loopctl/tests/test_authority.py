"""
Tests for Decision Authority Model.
"""

from __future__ import annotations

from components.testing.pytest_fixtures.import_helper import import_component_module

from pathlib import Path
import importlib
import sys
import types
import pytest


MODULE_PATH = 'components.cognitive_architecture.loopctl.authority'
EXPORTS = ['AuthorityLevel', 'DecisionAction', 'Decision', 'DecisionResult', 'DecisionAuthority']


def _import_module():
    return import_component_module(MODULE_PATH)

def test_module_imports():
    """Test that module can be imported."""
    _import_module()


def test_exports_present():
    """Test that all expected exports are present."""
    module = _import_module()
    if not EXPORTS:
        return
    missing = [name for name in EXPORTS if not hasattr(module, name)]
    assert not missing, f"Missing exports: {missing}"


def test_authority_levels_hierarchy():
    """Test authority level ordering."""
    module = _import_module()
    AL = module.AuthorityLevel

    # Higher number = higher authority
    assert AL.HARNESS > AL.HUMAN > AL.LOOP3 > AL.LOOP1
    assert AL.HARNESS.value == 4
    assert AL.HUMAN.value == 3
    assert AL.LOOP3.value == 2
    assert AL.LOOP1.value == 1


def test_decision_authority_init():
    """Test DecisionAuthority initialization."""
    module = _import_module()
    authority = module.DecisionAuthority()

    # Should have default ownership
    assert authority.get_owner("harness_weights") == module.AuthorityLevel.HARNESS
    assert authority.get_owner("learning_rate") == module.AuthorityLevel.LOOP3
    assert authority.get_owner("unknown_target") is None


def test_can_modify_hierarchy():
    """Test that lower authority cannot modify higher authority targets."""
    module = _import_module()
    AL = module.AuthorityLevel
    authority = module.DecisionAuthority()

    # HARNESS can modify anything
    assert authority.can_modify("harness_weights", AL.HARNESS) is True
    assert authority.can_modify("learning_rate", AL.HARNESS) is True

    # LOOP1 cannot modify HARNESS targets
    assert authority.can_modify("harness_weights", AL.LOOP1) is False
    assert authority.can_modify("harness_weights", AL.LOOP3) is False
    assert authority.can_modify("harness_weights", AL.HUMAN) is False

    # LOOP1 can modify its own targets
    assert authority.can_modify("execution_context", AL.LOOP1) is True

    # Unowned targets can be modified by anyone
    assert authority.can_modify("unowned_target", AL.LOOP1) is True


def test_make_decision_allowed():
    """Test making a decision at appropriate authority level."""
    module = _import_module()
    AL = module.AuthorityLevel
    authority = module.DecisionAuthority()

    # LOOP3 can modify its own targets
    result = authority.make_decision(
        level=AL.LOOP3,
        action="modify",
        target="learning_rate",
        reason="Optimization suggests change"
    )

    assert result.allowed is True
    assert result.decision is not None
    assert result.decision.authority_level == AL.LOOP3
    assert result.decision.action == "modify"
    assert result.decision.target == "learning_rate"
    assert result.decision.effective is True


def test_make_decision_blocked():
    """Test that lower authority is blocked from modifying higher targets."""
    module = _import_module()
    AL = module.AuthorityLevel
    authority = module.DecisionAuthority()

    # LOOP1 cannot modify HARNESS targets
    result = authority.make_decision(
        level=AL.LOOP1,
        action="modify",
        target="harness_weights",
        reason="Trying to change weights"
    )

    assert result.allowed is False
    assert result.decision is None
    assert result.blocking_authority == AL.HARNESS
    assert "cannot modify" in result.blocked_reason


def test_veto_decision():
    """Test vetoing a decision from lower authority."""
    module = _import_module()
    AL = module.AuthorityLevel
    authority = module.DecisionAuthority()

    # LOOP3 makes a decision
    result = authority.make_decision(
        level=AL.LOOP3,
        action="propose",
        target="learning_rate",
        reason="Suggest new rate"
    )
    assert result.allowed is True
    decision_id = result.decision.id

    # HARNESS vetoes it
    veto_result = authority.veto(
        decision_id=decision_id,
        vetoing_level=AL.HARNESS,
        reason="Quality threshold not met"
    )

    assert veto_result.allowed is True
    assert veto_result.decision.is_vetoed is True
    assert veto_result.decision.vetoed_by == AL.HARNESS
    assert veto_result.decision.effective is False


def test_veto_requires_reason():
    """Test that veto requires explanation."""
    module = _import_module()
    AL = module.AuthorityLevel
    authority = module.DecisionAuthority()

    # Make a decision
    result = authority.make_decision(
        level=AL.LOOP1,
        action="execute",
        target="task_parameters"
    )
    decision_id = result.decision.id

    # Try to veto without reason
    veto_result = authority.veto(
        decision_id=decision_id,
        vetoing_level=AL.HARNESS,
        reason=""  # Empty reason
    )

    assert veto_result.allowed is False
    assert "requires explanation" in veto_result.blocked_reason


def test_veto_authority_check():
    """Test that lower authority cannot veto higher authority decisions."""
    module = _import_module()
    AL = module.AuthorityLevel
    authority = module.DecisionAuthority()

    # HARNESS makes a decision
    result = authority.make_decision(
        level=AL.HARNESS,
        action="veto",
        target="harness_weights",
        reason="Quality check"
    )
    decision_id = result.decision.id

    # LOOP3 tries to veto HARNESS decision - blocked
    veto_result = authority.veto(
        decision_id=decision_id,
        vetoing_level=AL.LOOP3,
        reason="Disagree with veto"
    )

    assert veto_result.allowed is False
    assert veto_result.blocking_authority == AL.HARNESS


def test_human_override():
    """Test human override functionality."""
    module = _import_module()
    AL = module.AuthorityLevel
    authority = module.DecisionAuthority()

    # Make a decision
    result = authority.make_decision(
        level=AL.LOOP3,
        action="propose",
        target="meta_loop_config"
    )
    decision_id = result.decision.id

    # HUMAN overrides
    override_result = authority.override(
        decision_id=decision_id,
        overriding_level=AL.HUMAN,
        reason="User preference"
    )

    assert override_result.allowed is True
    assert override_result.decision.is_overridden is True
    assert override_result.decision.overridden_by == AL.HUMAN


def test_only_human_can_override():
    """Test that only HUMAN authority can issue overrides."""
    module = _import_module()
    AL = module.AuthorityLevel
    authority = module.DecisionAuthority()

    # Make a decision
    result = authority.make_decision(
        level=AL.LOOP1,
        action="execute",
        target="runtime_config"
    )
    decision_id = result.decision.id

    # HARNESS tries to override - blocked
    override_result = authority.override(
        decision_id=decision_id,
        overriding_level=AL.HARNESS,
        reason="Override attempt"
    )

    assert override_result.allowed is False
    assert "Only HUMAN" in override_result.blocked_reason


def test_get_statistics():
    """Test decision statistics gathering."""
    module = _import_module()
    AL = module.AuthorityLevel
    authority = module.DecisionAuthority()

    # Make several decisions
    authority.make_decision(AL.LOOP1, "execute", "task_parameters")
    loop3_result = authority.make_decision(AL.LOOP3, "propose", "learning_rate")
    authority.make_decision(AL.HARNESS, "approve", "harness_weights")

    # Veto the LOOP3 decision (HARNESS can veto lower authority)
    authority.veto(loop3_result.decision.id, AL.HARNESS, "Test veto")

    stats = authority.get_statistics()
    assert stats["total_decisions"] == 3
    assert stats["effective_decisions"] == 2  # One was vetoed
    assert stats["by_level"]["HARNESS"]["total"] == 1
    assert stats["by_level"]["LOOP3"]["total"] == 1
    assert stats["by_level"]["LOOP1"]["total"] == 1


def test_decision_to_dict():
    """Test decision serialization."""
    module = _import_module()
    AL = module.AuthorityLevel
    authority = module.DecisionAuthority()

    result = authority.make_decision(
        level=AL.LOOP3,
        action="propose",
        target="optimization_parameters",
        reason="Test decision",
        metadata={"test_key": "test_value"}
    )

    decision_dict = result.decision.to_dict()
    assert decision_dict["authority_level"] == "LOOP3"
    assert decision_dict["action"] == "propose"
    assert decision_dict["target"] == "optimization_parameters"
    assert decision_dict["reason"] == "Test decision"
    assert decision_dict["metadata"]["test_key"] == "test_value"
    assert decision_dict["effective"] is True


def test_persist_and_clear():
    """Test persisting decisions to file and clearing."""
    import tempfile
    module = _import_module()
    AL = module.AuthorityLevel
    authority = module.DecisionAuthority()

    # Make decisions
    authority.make_decision(AL.LOOP1, "execute", "task_parameters")
    authority.make_decision(AL.LOOP3, "propose", "learning_rate")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "decisions.json"
        persisted_path = authority.persist(output_path)

        assert persisted_path.exists()

        # Read and verify
        import json
        with open(persisted_path) as f:
            data = json.load(f)

        assert len(data["decisions"]) == 2
        assert "statistics" in data

    # Clear
    count = authority.clear()
    assert count == 2
    assert authority.get_statistics()["total_decisions"] == 0
