"""
Comprehensive tests for the Gate System component.

Tests gate validation, progression tracking, violation management, and custom configuration.

Run tests with:
    cd ~/.claude/library/components/trading/gate-system
    python -m pytest tests/ -v

Or run directly:
    python tests/test_gate_system.py
"""
import pytest
from decimal import Decimal
from pathlib import Path
import sys

# Add parent directory to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Direct imports from gate_manager module
from gate_manager import (
    GateManager, GateLevel, GateConfig, create_default_gate_configs
)


class TestGateConfig:
    """Test GateConfig validation and creation."""

    def test_valid_gate_config(self):
        """Test creating a valid gate config."""
        config = GateConfig(
            level=GateLevel.G0,
            capital_min=200.0,
            capital_max=499.99,
            allowed_assets={'SPY', 'QQQ'},
            cash_floor_pct=0.50,
            options_enabled=False
        )
        assert config.level == GateLevel.G0
        assert config.capital_min == Decimal("200.0")
        assert config.max_position_pct == Decimal("0.20")  # Default

    def test_invalid_capital_range(self):
        """Test that invalid capital range raises error."""
        with pytest.raises(ValueError, match="Invalid capital range"):
            GateConfig(
                level=GateLevel.G0,
                capital_min=500.0,
                capital_max=200.0,  # Invalid: max < min
                allowed_assets={'SPY'},
                cash_floor_pct=0.50,
                options_enabled=False
            )

    def test_invalid_cash_floor(self):
        """Test that invalid cash floor raises error."""
        with pytest.raises(ValueError, match="Invalid cash floor"):
            GateConfig(
                level=GateLevel.G0,
                capital_min=200.0,
                capital_max=500.0,
                allowed_assets={'SPY'},
                cash_floor_pct=1.5,  # Invalid: > 1.0
                options_enabled=False
            )

    def test_invalid_theta_pct(self):
        """Test that invalid theta percentage raises error."""
        with pytest.raises(ValueError, match="Invalid theta"):
            GateConfig(
                level=GateLevel.G0,
                capital_min=200.0,
                capital_max=500.0,
                allowed_assets={'SPY'},
                cash_floor_pct=0.50,
                options_enabled=True,
                max_theta_pct=2.0  # Invalid: > 1.0
            )


class TestDefaultConfigs:
    """Test default gate configurations."""

    def test_create_default_configs(self):
        """Test default config creation."""
        configs = create_default_gate_configs()

        assert GateLevel.G0 in configs
        assert GateLevel.G3 in configs
        assert GateLevel.G12 in configs

    def test_g0_config(self):
        """Test G0 default config."""
        configs = create_default_gate_configs()
        g0 = configs[GateLevel.G0]

        assert g0.capital_min == Decimal("200")
        assert g0.capital_max == Decimal("499.99")
        assert g0.cash_floor_pct == 0.50
        assert g0.options_enabled is False
        assert 'ULTY' in g0.allowed_assets

    def test_g3_enables_options(self):
        """Test that G3 enables options."""
        configs = create_default_gate_configs()
        g3 = configs[GateLevel.G3]

        assert g3.options_enabled is True
        assert g3.max_theta_pct == Decimal("0.005")

    def test_higher_gates_have_wildcard(self):
        """Test that higher gates allow all assets."""
        configs = create_default_gate_configs()

        for gate in [GateLevel.G4, GateLevel.G5, GateLevel.G12]:
            assert '*' in configs[gate].allowed_assets


class TestGateManager:
    """Test GateManager core functionality."""

    @pytest.fixture
    def manager(self):
        """Create a fresh GateManager for each test."""
        return GateManager()

    @pytest.fixture
    def manager_with_state(self, tmp_path):
        """Create a GateManager with state persistence."""
        return GateManager(data_dir=str(tmp_path / "gates"))

    def test_initialization(self, manager):
        """Test manager initializes correctly."""
        assert manager.current_gate == GateLevel.G0
        assert manager.current_capital == Decimal("0")
        assert len(manager.violation_history) == 0

    def test_update_capital_same_gate(self, manager):
        """Test updating capital within same gate."""
        manager.update_capital(300.0)
        assert manager.current_capital == Decimal("300.0")
        assert manager.current_gate == GateLevel.G0

    def test_update_capital_gate_change(self, manager):
        """Test updating capital triggers gate change."""
        result = manager.update_capital(600.0)
        assert result is True
        assert manager.current_gate == GateLevel.G1

    def test_get_current_config(self, manager):
        """Test getting current gate config."""
        config = manager.get_current_config()
        assert config.level == GateLevel.G0

        manager.update_capital(600.0)
        config = manager.get_current_config()
        assert config.level == GateLevel.G1

    def test_get_all_gates(self, manager):
        """Test getting all gate summaries."""
        gates = manager.get_all_gates()
        assert len(gates) > 0
        assert gates[0]['level'] == 'G0'


class TestTradeValidation:
    """Test trade validation functionality."""

    @pytest.fixture
    def manager_g1(self):
        """Create manager at G1 level."""
        manager = GateManager()
        manager.update_capital(600.0)
        return manager

    def test_valid_trade(self, manager_g1):
        """Test a valid trade passes validation."""
        result = manager_g1.validate_trade(
            trade_details={
                'symbol': 'IAU',
                'side': 'BUY',
                'quantity': 5,  # Smaller quantity to stay within limits
                'price': 40.0,  # $200 trade
                'trade_type': 'STOCK'
            },
            current_portfolio={
                'cash': 7000.0,  # 70% cash - above 60% floor requirement
                'total_value': 10000.0,
                'positions': {}
            }
        )
        assert result.is_valid is True
        assert len(result.violations) == 0

    def test_asset_not_allowed(self, manager_g1):
        """Test asset not allowed at current gate."""
        result = manager_g1.validate_trade(
            trade_details={
                'symbol': 'TSLA',  # Not in G1 allowed list
                'side': 'BUY',
                'quantity': 1,
                'price': 200.0,
                'trade_type': 'STOCK'
            },
            current_portfolio={
                'cash': 5000.0,
                'total_value': 10000.0,
                'positions': {}
            }
        )
        assert result.is_valid is False
        assert any(v['type'] == 'asset_not_allowed' for v in result.violations)

    def test_cash_floor_violation(self, manager_g1):
        """Test cash floor violation detection."""
        result = manager_g1.validate_trade(
            trade_details={
                'symbol': 'IAU',
                'side': 'BUY',
                'quantity': 100,
                'price': 40.0,  # $4000 trade
                'trade_type': 'STOCK'
            },
            current_portfolio={
                'cash': 5000.0,
                'total_value': 10000.0,  # Need 60% = $6000 cash floor
                'positions': {}
            }
        )
        assert result.is_valid is False
        assert any(v['type'] == 'cash_floor_violation' for v in result.violations)

    def test_position_size_exceeded(self, manager_g1):
        """Test position size limit violation."""
        result = manager_g1.validate_trade(
            trade_details={
                'symbol': 'IAU',
                'side': 'BUY',
                'quantity': 100,
                'price': 30.0,  # $3000 trade = 30% of portfolio
                'trade_type': 'STOCK'
            },
            current_portfolio={
                'cash': 9000.0,
                'total_value': 10000.0,
                'positions': {}
            }
        )
        assert result.is_valid is False
        assert any(v['type'] == 'position_size_exceeded' for v in result.violations)

    def test_options_not_allowed(self, manager_g1):
        """Test options not allowed at G1."""
        result = manager_g1.validate_trade(
            trade_details={
                'symbol': 'SPY',
                'side': 'BUY',
                'quantity': 1,
                'price': 5.0,
                'trade_type': 'OPTION'
            },
            current_portfolio={
                'cash': 9000.0,
                'total_value': 10000.0,
                'positions': {}
            }
        )
        assert result.is_valid is False
        assert any(v['type'] == 'options_not_allowed' for v in result.violations)

    def test_warnings_for_approaching_limits(self, manager_g1):
        """Test warnings are generated when approaching limits."""
        result = manager_g1.validate_trade(
            trade_details={
                'symbol': 'IAU',
                'side': 'BUY',
                'quantity': 5,
                'price': 40.0,
                'trade_type': 'STOCK',
                'kelly_percentage': 0.18  # Near 22% limit triggers Kelly warning
            },
            current_portfolio={
                'cash': 2500.0,  # 25% cash (below 60% floor triggers warning at 70% utilization)
                'total_value': 10000.0,
                'positions': {}
            }
        )
        # Either cash utilization warning or Kelly warning should be present
        # Note: trade may still be valid if it's a small trade
        assert len(result.warnings) > 0 or not result.is_valid


class TestOptionsValidation:
    """Test options-specific validation at G3+."""

    @pytest.fixture
    def manager_g3(self):
        """Create manager at G3 level (options enabled)."""
        manager = GateManager()
        manager.update_capital(3000.0)
        return manager

    def test_options_allowed_at_g3(self, manager_g3):
        """Test options are allowed at G3."""
        result = manager_g3.validate_trade(
            trade_details={
                'symbol': 'SPY',
                'side': 'BUY',
                'quantity': 1,
                'price': 5.0,
                'trade_type': 'OPTION',
                'theta': 0.01
            },
            current_portfolio={
                'cash': 9000.0,
                'total_value': 10000.0,
                'positions': {},
                'total_theta': 0
            }
        )
        # Should not have options_not_allowed violation
        assert not any(v['type'] == 'options_not_allowed' for v in result.violations)

    def test_theta_limit_exceeded(self, manager_g3):
        """Test theta limit violation."""
        result = manager_g3.validate_trade(
            trade_details={
                'symbol': 'SPY',
                'side': 'BUY',
                'quantity': 100,  # Large quantity
                'price': 5.0,
                'trade_type': 'OPTION',
                'theta': 1.0  # High theta per contract
            },
            current_portfolio={
                'cash': 9000.0,
                'total_value': 10000.0,
                'positions': {},
                'total_theta': 0
            }
        )
        assert result.is_valid is False
        assert any(v['type'] == 'theta_limit_exceeded' for v in result.violations)


class TestGraduation:
    """Test graduation and downgrade logic."""

    @pytest.fixture
    def compliant_manager(self):
        """Create a manager at G0 with compliant history ready for graduation."""
        manager = GateManager()
        # Start at G0 level (capital below $500)
        manager.current_capital = Decimal("450.0")
        manager.current_gate = GateLevel.G0
        # Set metrics that meet graduation criteria for G0->G1
        manager.graduation_metrics.consecutive_compliant_days = 20  # >= 14 required
        manager.graduation_metrics.performance_score = 0.7  # >= 0.6 required
        manager.graduation_metrics.total_violations_30d = 0  # <= 2 required
        return manager

    def test_graduation_check_graduate(self, compliant_manager):
        """Test graduation check returns GRADUATE when criteria met."""
        # Set capital to meet next gate minimum ($500)
        compliant_manager.current_capital = Decimal("550.0")
        decision = compliant_manager.check_graduation({
            'sharpe_ratio_30d': 1.5,
            'max_drawdown_30d': 0.05,
            'avg_cash_utilization_30d': 0.45
        })
        assert decision == 'GRADUATE'

    def test_graduation_check_hold(self):
        """Test graduation check returns HOLD when criteria not met."""
        manager = GateManager()
        manager.update_capital(450.0)
        manager.graduation_metrics.consecutive_compliant_days = 5  # Not enough

        decision = manager.check_graduation({
            'sharpe_ratio_30d': 1.5,
            'max_drawdown_30d': 0.05,
            'avg_cash_utilization_30d': 0.45
        })
        assert decision == 'HOLD'

    def test_graduation_check_downgrade(self):
        """Test graduation check returns DOWNGRADE on poor performance."""
        manager = GateManager()
        manager.update_capital(600.0)
        manager.graduation_metrics.total_violations_30d = 10

        decision = manager.check_graduation({
            'sharpe_ratio_30d': -0.5,
            'max_drawdown_30d': 0.25,
            'avg_cash_utilization_30d': 0.80
        })
        assert decision == 'DOWNGRADE'

    def test_execute_graduation(self):
        """Test executing graduation."""
        manager = GateManager()
        manager.current_capital = Decimal("450.0")
        manager.current_gate = GateLevel.G0
        assert manager.current_gate == GateLevel.G0
        result = manager.execute_graduation()
        assert result is True
        assert manager.current_gate == GateLevel.G1

    def test_execute_downgrade(self):
        """Test executing downgrade."""
        manager = GateManager()
        manager.update_capital(600.0)
        assert manager.current_gate == GateLevel.G1

        result = manager.execute_downgrade()
        assert result is True
        assert manager.current_gate == GateLevel.G0

    def test_cannot_downgrade_from_g0(self):
        """Test cannot downgrade below G0."""
        manager = GateManager()
        result = manager.execute_downgrade()
        assert result is False
        assert manager.current_gate == GateLevel.G0


class TestViolations:
    """Test violation tracking and management."""

    @pytest.fixture
    def manager_with_violations(self):
        """Create manager with some violations."""
        manager = GateManager()
        manager.update_capital(600.0)

        # Trigger a violation
        manager.validate_trade(
            trade_details={
                'symbol': 'TSLA',
                'side': 'BUY',
                'quantity': 1,
                'price': 200.0,
                'trade_type': 'STOCK'
            },
            current_portfolio={
                'cash': 5000.0,
                'total_value': 10000.0,
                'positions': {}
            }
        )
        return manager

    def test_violation_recorded(self, manager_with_violations):
        """Test violations are recorded."""
        assert len(manager_with_violations.violation_history) > 0

    def test_get_violation_history(self, manager_with_violations):
        """Test getting violation history."""
        violations = manager_with_violations.get_violation_history(days=7)
        assert len(violations) > 0

    def test_resolve_violation(self, manager_with_violations):
        """Test resolving a violation."""
        result = manager_with_violations.resolve_violation(0, "Acknowledged")
        assert result is True
        assert manager_with_violations.violation_history[0].resolved is True

    def test_resolve_invalid_index(self, manager_with_violations):
        """Test resolving invalid violation index."""
        result = manager_with_violations.resolve_violation(999, "Invalid")
        assert result is False


class TestStatePersistence:
    """Test state persistence functionality."""

    def test_state_saved_and_loaded(self, tmp_path):
        """Test state is saved and loaded correctly."""
        data_dir = str(tmp_path / "gates")

        # Create and configure manager
        manager1 = GateManager(data_dir=data_dir)
        manager1.update_capital(600.0)
        manager1.graduation_metrics.consecutive_compliant_days = 10
        # Explicitly save state after updating metrics
        manager1._save_state()

        # Create new manager (should load state)
        manager2 = GateManager(data_dir=data_dir)
        assert manager2.current_gate == GateLevel.G1
        assert manager2.current_capital == Decimal("600.0")
        assert manager2.graduation_metrics.consecutive_compliant_days == 10


class TestCallbacks:
    """Test event callbacks."""

    def test_violation_callback(self):
        """Test violation callback is triggered."""
        violations_received = []

        def on_violation(violation):
            violations_received.append(violation)

        manager = GateManager(on_violation=on_violation)
        manager.update_capital(600.0)

        # Trigger violation
        manager.validate_trade(
            trade_details={
                'symbol': 'TSLA',
                'side': 'BUY',
                'quantity': 1,
                'price': 200.0,
                'trade_type': 'STOCK'
            },
            current_portfolio={
                'cash': 5000.0,
                'total_value': 10000.0,
                'positions': {}
            }
        )

        assert len(violations_received) > 0

    def test_graduation_callback(self):
        """Test graduation callback is triggered."""
        graduations = []

        def on_graduation(from_gate, to_gate):
            graduations.append((from_gate, to_gate))

        manager = GateManager(on_graduation=on_graduation)
        manager.update_capital(450.0)
        manager.graduation_metrics.consecutive_compliant_days = 20
        manager.graduation_metrics.performance_score = 0.7

        manager.execute_graduation()
        assert len(graduations) == 1
        assert graduations[0] == (GateLevel.G0, GateLevel.G1)


class TestCustomConfiguration:
    """Test custom gate configurations."""

    def test_custom_gate_configs(self):
        """Test using custom gate configurations."""
        custom_configs = {
            GateLevel.G0: GateConfig(
                level=GateLevel.G0,
                capital_min=100.0,
                capital_max=999.99,
                allowed_assets={'BTC', 'ETH'},
                cash_floor_pct=0.20,
                options_enabled=True,
                max_position_pct=0.50
            )
        }

        manager = GateManager(gate_configs=custom_configs)
        config = manager.get_current_config()

        assert config.capital_min == 100.0
        assert 'BTC' in config.allowed_assets
        assert config.options_enabled is True

    def test_custom_graduation_criteria(self):
        """Test using custom graduation criteria."""
        custom_criteria = {
            GateLevel.G0: {
                'min_compliant_days': 3,
                'max_violations_30d': 5,
                'min_performance_score': 0.3,
                'min_capital': 100.0
            }
        }

        manager = GateManager(graduation_criteria=custom_criteria)
        manager.update_capital(150.0)
        manager.graduation_metrics.consecutive_compliant_days = 5
        manager.graduation_metrics.performance_score = 0.5

        decision = manager.check_graduation({
            'sharpe_ratio_30d': 0.5,
            'max_drawdown_30d': 0.10
        })
        assert decision == 'GRADUATE'


class TestStatusReport:
    """Test status report generation."""

    def test_status_report_structure(self):
        """Test status report has correct structure."""
        manager = GateManager()
        manager.update_capital(600.0)
        report = manager.get_status_report()

        assert 'current_gate' in report
        assert 'current_capital' in report
        assert 'gate_config' in report
        assert 'graduation_metrics' in report
        assert 'recent_violations' in report

    def test_status_report_values(self):
        """Test status report has correct values."""
        manager = GateManager()
        manager.update_capital(600.0)
        report = manager.get_status_report()

        assert report['current_gate'] == 'G1'
        assert report['current_capital'] == "600.0"


class TestKellyValidation:
    """Test Kelly criterion integration."""

    def test_kelly_percentage_validation(self):
        """Test Kelly percentage is validated."""
        manager = GateManager()
        manager.update_capital(600.0)

        result = manager.validate_trade(
            trade_details={
                'symbol': 'IAU',
                'side': 'BUY',
                'quantity': 10,
                'price': 40.0,
                'trade_type': 'STOCK',
                'kelly_percentage': 0.30  # 30% Kelly exceeds 22% G1 limit
            },
            current_portfolio={
                'cash': 9000.0,
                'total_value': 10000.0,
                'positions': {}
            }
        )
        assert result.is_valid is False
        assert any(v['type'] == 'position_size_exceeded' for v in result.violations)

    def test_kelly_warning(self):
        """Test Kelly warning when approaching limit."""
        manager = GateManager()
        manager.update_capital(600.0)

        result = manager.validate_trade(
            trade_details={
                'symbol': 'IAU',
                'side': 'BUY',
                'quantity': 5,
                'price': 40.0,
                'trade_type': 'STOCK',
                'kelly_percentage': 0.18  # 18% approaching 22% limit
            },
            current_portfolio={
                'cash': 9000.0,
                'total_value': 10000.0,
                'positions': {}
            }
        )
        assert any('kelly' in w['message'].lower() for w in result.warnings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
