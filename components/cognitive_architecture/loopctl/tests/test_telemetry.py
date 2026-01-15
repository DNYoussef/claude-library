"""
Tests for FrozenHarness Telemetry Integration.
"""

from __future__ import annotations

from pathlib import Path
import importlib
import sys
import types
import pytest


MODULE_PATH = 'components.cognitive_architecture.loopctl.telemetry'
EXPORTS = ['TelemetryPacket', 'GradeEvent', 'ConvergenceEvent', 'HarnessTelemetry']


def _library_root() -> Path:
    root = Path(__file__).resolve()
    while root != root.parent:
        if (root / 'catalog.json').exists() and (root / 'components').exists():
            return root
        root = root.parent
    raise RuntimeError('Library root not found')


def _ensure_library_package() -> None:
    root = _library_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    if 'library' not in sys.modules:
        library = types.ModuleType('library')
        library.__path__ = [str(root)]
        sys.modules['library'] = library


def _import_module():
    _ensure_library_package()
    try:
        return importlib.import_module(MODULE_PATH)
    except ModuleNotFoundError as exc:
        if exc.name and exc.name in MODULE_PATH:
            raise
        pytest.skip(f'Missing dependency: {exc.name}')
    except ImportError as exc:
        pytest.skip(f'Import error: {exc}')


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


def test_telemetry_packet_creation():
    """Test TelemetryPacket dataclass."""
    from datetime import datetime
    module = _import_module()

    packet = module.TelemetryPacket(
        timestamp=datetime.now(),
        period_seconds=300.0,
        grades_issued=10,
        veto_rate=0.05,
        override_rate=0.0,
        avg_grade=0.85,
    )

    assert packet.grades_issued == 10
    assert packet.veto_rate == 0.05
    assert packet.avg_grade == 0.85


def test_telemetry_packet_to_dict():
    """Test TelemetryPacket serialization."""
    from datetime import datetime
    module = _import_module()

    packet = module.TelemetryPacket(
        timestamp=datetime.now(),
        period_seconds=300.0,
        grades_issued=5,
        harness_version="1.0.0",
        harness_hash="test_hash",
        evaluation_mode="heuristic",
    )

    data = packet.to_dict()
    assert data["grades_issued"] == 5
    assert data["harness_version"] == "1.0.0"
    assert data["harness_hash"] == "test_hash"
    assert "timestamp" in data


def test_telemetry_packet_prometheus_format():
    """Test Prometheus exposition format."""
    from datetime import datetime
    module = _import_module()

    packet = module.TelemetryPacket(
        timestamp=datetime.now(),
        period_seconds=300.0,
        grades_issued=10,
        veto_rate=0.05,
        avg_grade=0.85,
        grade_distribution={"0.8-1.0": 8, "0.6-0.8": 2},
        harness_version="1.0.0",
        harness_hash="abc123",
        evaluation_mode="heuristic",
    )

    prometheus = packet.to_prometheus_format()
    assert "frozen_harness_grades_issued_total 10" in prometheus
    assert "frozen_harness_veto_rate 0.05" in prometheus
    assert "frozen_harness_avg_grade 0.85" in prometheus
    assert 'frozen_harness_info{version="1.0.0"' in prometheus


def test_harness_telemetry_init():
    """Test HarnessTelemetry initialization."""
    module = _import_module()

    telemetry = module.HarnessTelemetry()
    assert telemetry is not None


def test_harness_telemetry_record_grade():
    """Test recording grade events."""
    module = _import_module()

    telemetry = module.HarnessTelemetry()
    telemetry.record_grade(0.85, 100.0, "/path/to/artifact")
    telemetry.record_grade(0.92, 120.0, "/path/to/artifact2")

    packet = telemetry.collect()
    assert packet.grades_issued == 2
    assert packet.avg_grade == pytest.approx(0.885, rel=0.01)


def test_harness_telemetry_record_convergence():
    """Test recording convergence events."""
    module = _import_module()

    telemetry = module.HarnessTelemetry()
    telemetry.record_convergence(5, 0.95, True)
    telemetry.record_convergence(3, 0.90, True)
    telemetry.record_convergence(7, 0.88, True)

    packet = telemetry.collect()
    assert packet.convergence_iterations == pytest.approx(5.0, rel=0.01)


def test_harness_telemetry_grade_distribution():
    """Test grade distribution bucketing."""
    module = _import_module()

    telemetry = module.HarnessTelemetry()

    # Add grades in different buckets
    telemetry.record_grade(0.15, 100.0)  # 0.0-0.2
    telemetry.record_grade(0.35, 100.0)  # 0.2-0.4
    telemetry.record_grade(0.55, 100.0)  # 0.4-0.6
    telemetry.record_grade(0.75, 100.0)  # 0.6-0.8
    telemetry.record_grade(0.95, 100.0)  # 0.8-1.0
    telemetry.record_grade(0.85, 100.0)  # 0.8-1.0

    packet = telemetry.collect()
    dist = packet.grade_distribution

    assert dist["0.0-0.2"] == 1
    assert dist["0.2-0.4"] == 1
    assert dist["0.4-0.6"] == 1
    assert dist["0.6-0.8"] == 1
    assert dist["0.8-1.0"] == 2


def test_harness_telemetry_with_authority():
    """Test telemetry with DecisionAuthority integration."""
    module = _import_module()
    auth_module = importlib.import_module(
        'components.cognitive_architecture.loopctl.authority'
    )

    authority = auth_module.DecisionAuthority()

    # Make some decisions
    authority.make_decision(
        auth_module.AuthorityLevel.LOOP1, "execute", "task_parameters"
    )
    result = authority.make_decision(
        auth_module.AuthorityLevel.LOOP3, "propose", "learning_rate"
    )
    # Veto one
    authority.veto(result.decision.id, auth_module.AuthorityLevel.HARNESS, "test")

    telemetry = module.HarnessTelemetry(authority=authority)
    packet = telemetry.collect()

    assert packet.decision_count == 2
    assert packet.veto_rate == 0.5  # 1 veto / 2 decisions


def test_harness_telemetry_with_harness():
    """Test telemetry with FrozenHarness integration."""
    module = _import_module()
    core_module = importlib.import_module(
        'components.cognitive_architecture.loopctl.core'
    )

    harness = core_module.FrozenHarness(
        harness_version="1.0.0",
        use_cli_evaluator=False
    )

    telemetry = module.HarnessTelemetry(harness=harness)
    packet = telemetry.collect()

    assert packet.harness_version == "1.0.0"
    assert packet.harness_hash.startswith("frozen_eval_harness_v1.0.0_")
    assert packet.evaluation_mode == "heuristic"


def test_harness_telemetry_export_to_file():
    """Test exporting telemetry to JSON file."""
    import tempfile
    module = _import_module()

    telemetry = module.HarnessTelemetry()
    telemetry.record_grade(0.85, 100.0)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "telemetry.json"
        exported = telemetry.export_to_file(output_path)

        assert exported.exists()

        import json
        with open(exported) as f:
            data = json.load(f)

        assert data["grades_issued"] == 1
        assert "timestamp" in data


def test_harness_telemetry_export_prometheus():
    """Test exporting telemetry in Prometheus format."""
    import tempfile
    module = _import_module()

    telemetry = module.HarnessTelemetry()
    telemetry.record_grade(0.90, 100.0)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metrics"
        exported = telemetry.export_prometheus(output_path)

        assert exported.exists()

        content = exported.read_text()
        assert "frozen_harness_grades_issued_total" in content


def test_harness_telemetry_clear():
    """Test clearing telemetry events."""
    module = _import_module()

    telemetry = module.HarnessTelemetry()
    telemetry.record_grade(0.85, 100.0)
    telemetry.record_grade(0.90, 100.0)

    packet_before = telemetry.collect()
    assert packet_before.grades_issued == 2

    telemetry.clear()

    packet_after = telemetry.collect()
    assert packet_after.grades_issued == 0


def test_harness_telemetry_summary():
    """Test getting telemetry summary."""
    module = _import_module()

    telemetry = module.HarnessTelemetry()
    telemetry.record_grade(0.85, 100.0)
    telemetry.record_grade(0.90, 100.0)

    summary = telemetry.get_summary()
    assert summary["grades_issued"] == 2
    assert "avg_grade" in summary
    assert "veto_rate" in summary


def test_harness_telemetry_export_callback():
    """Test export callback registration."""
    module = _import_module()

    telemetry = module.HarnessTelemetry()

    # Track callback invocations
    callback_packets = []

    def test_callback(packet):
        callback_packets.append(packet)

    telemetry.register_export_callback(test_callback)
    telemetry.record_grade(0.85, 100.0)

    # Trigger collection
    telemetry.collect()

    assert len(callback_packets) == 1
    assert callback_packets[0].grades_issued == 1
