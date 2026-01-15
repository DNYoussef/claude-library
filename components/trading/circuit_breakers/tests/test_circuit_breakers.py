"""
Tests for Circuit Breakers Library Component.

Run with: pytest tests/test_circuit_breakers.py -v
"""

import asyncio
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitBreakerConfig,
    CircuitState,
    CircuitType,
    CircuitOpenException,
)

from trading_breakers import (
    TradingCircuitBreakers,
    TradingBreakerConfig,
    PortfolioProvider,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def basic_config():
    """Basic circuit breaker configuration for testing."""
    return CircuitBreakerConfig(
        failure_threshold=3,
        failure_rate_threshold=0.5,
        success_threshold=2,
        failure_window_seconds=60,
        open_timeout_seconds=1,  # Short timeout for testing
        exponential_backoff=False
    )


@pytest.fixture
def circuit_breaker(basic_config):
    """Create a basic circuit breaker for testing."""
    return CircuitBreaker("test_breaker", CircuitType.CONNECTION_FAILURE, basic_config)


@pytest.fixture
def mock_portfolio():
    """Create a mock portfolio provider."""
    portfolio = AsyncMock(spec=PortfolioProvider)
    portfolio.get_total_value.return_value = Decimal("100000")
    portfolio.get_daily_pnl.return_value = Decimal("0")
    portfolio.get_daily_pnl_pct.return_value = Decimal("0")
    portfolio.get_max_drawdown.return_value = Decimal("0")
    portfolio.get_position_concentration.return_value = Decimal("5")
    return portfolio


@pytest.fixture
def trading_config():
    """Trading circuit breaker configuration for testing."""
    return TradingBreakerConfig(
        daily_loss_limit_pct=Decimal("-2.0"),
        max_drawdown_pct=Decimal("-10.0"),
        max_position_pct=Decimal("20.0"),
        max_orders_per_minute=5,
        max_orders_per_hour=50,
        check_interval_seconds=0.1,  # Fast checks for testing
        cooldown_seconds=1
    )


# =============================================================================
# Basic Circuit Breaker Tests
# =============================================================================

class TestCircuitBreaker:
    """Tests for the base CircuitBreaker class."""

    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self, circuit_breaker):
        """Circuit breaker should start in CLOSED state."""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.is_closed
        assert not circuit_breaker.is_open

    @pytest.mark.asyncio
    async def test_successful_call_stays_closed(self, circuit_breaker):
        """Successful calls should keep circuit closed."""
        async def success_func():
            return "success"

        result = await circuit_breaker.call(success_func)

        assert result == "success"
        assert circuit_breaker.is_closed
        assert circuit_breaker.metrics.successful_requests == 1
        assert circuit_breaker.metrics.failed_requests == 0

    @pytest.mark.asyncio
    async def test_failure_increments_counter(self, circuit_breaker):
        """Failures should increment the failure counter."""
        async def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)

        assert circuit_breaker.metrics.failed_requests == 1
        assert circuit_breaker.is_closed  # Not enough failures to trip

    @pytest.mark.asyncio
    async def test_trips_after_threshold(self, circuit_breaker):
        """Circuit should trip after reaching failure threshold."""
        async def failing_func():
            raise ValueError("Test error")

        # Fail 3 times (threshold)
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.is_open
        assert circuit_breaker.metrics.circuit_trips == 1

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self, circuit_breaker):
        """Open circuit should reject new calls."""
        # Trip the circuit
        await circuit_breaker.force_open()

        async def success_func():
            return "success"

        with pytest.raises(CircuitOpenException) as exc_info:
            await circuit_breaker.call(success_func)

        assert "test_breaker" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self, circuit_breaker):
        """Circuit should transition to half-open after timeout."""
        await circuit_breaker.force_open()
        assert circuit_breaker.is_open

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Next call should be allowed (half-open)
        async def success_func():
            return "success"

        result = await circuit_breaker.call(success_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_recovery_after_successes(self, circuit_breaker):
        """Circuit should recover after enough successes in half-open."""
        # Trip and wait for half-open
        await circuit_breaker.force_open()
        await asyncio.sleep(1.1)

        async def success_func():
            return "success"

        # First success
        await circuit_breaker.call(success_func)
        # Second success (threshold is 2)
        await circuit_breaker.call(success_func)

        assert circuit_breaker.is_closed
        assert circuit_breaker.metrics.last_recovery_time is not None

    @pytest.mark.asyncio
    async def test_force_open_trips_circuit(self, circuit_breaker):
        """force_open should immediately trip the circuit."""
        assert circuit_breaker.is_closed

        await circuit_breaker.force_open()

        assert circuit_breaker.is_open

    @pytest.mark.asyncio
    async def test_force_close_recovers_circuit(self, circuit_breaker):
        """force_close should immediately recover the circuit."""
        await circuit_breaker.force_open()
        assert circuit_breaker.is_open

        await circuit_breaker.force_close()

        assert circuit_breaker.is_closed

    @pytest.mark.asyncio
    async def test_reset_clears_state(self, circuit_breaker):
        """reset should clear all state and metrics."""
        # Generate some state
        async def failing_func():
            raise ValueError("Test")

        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.metrics.failed_requests == 3

        # Reset
        circuit_breaker.reset()

        assert circuit_breaker.is_closed
        assert circuit_breaker.metrics.failed_requests == 0
        assert circuit_breaker.metrics.total_requests == 0

    @pytest.mark.asyncio
    async def test_trip_callback_called(self, circuit_breaker):
        """Trip callback should be called when circuit trips."""
        callback_called = []

        def trip_callback(name, circuit_type):
            callback_called.append((name, circuit_type))

        circuit_breaker.register_trip_callback(trip_callback)

        # Trip the circuit
        async def failing_func():
            raise ValueError("Test")

        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert len(callback_called) == 1
        assert callback_called[0][0] == "test_breaker"
        assert callback_called[0][1] == CircuitType.CONNECTION_FAILURE

    @pytest.mark.asyncio
    async def test_recovery_callback_called(self, circuit_breaker):
        """Recovery callback should be called when circuit recovers."""
        recovery_called = []

        def recovery_callback(name, circuit_type):
            recovery_called.append((name, circuit_type))

        circuit_breaker.register_recovery_callback(recovery_callback)

        # Trip and recover
        await circuit_breaker.force_open()
        await asyncio.sleep(1.1)

        async def success_func():
            return "success"

        # Recover with 2 successes
        await circuit_breaker.call(success_func)
        await circuit_breaker.call(success_func)

        assert len(recovery_called) == 1

    @pytest.mark.asyncio
    async def test_get_status_returns_dict(self, circuit_breaker):
        """get_status should return a comprehensive status dict."""
        status = circuit_breaker.get_status()

        assert 'name' in status
        assert 'state' in status
        assert 'total_requests' in status
        assert 'failure_rate' in status
        assert status['name'] == "test_breaker"
        assert status['state'] == "closed"

    @pytest.mark.asyncio
    async def test_sync_function_support(self, circuit_breaker):
        """Circuit breaker should support sync functions."""
        def sync_func():
            return "sync_result"

        result = await circuit_breaker.call(sync_func)
        assert result == "sync_result"


# =============================================================================
# Circuit Breaker Manager Tests
# =============================================================================

class TestCircuitBreakerManager:
    """Tests for CircuitBreakerManager."""

    def test_create_circuit_breaker(self):
        """Should create and register a circuit breaker."""
        manager = CircuitBreakerManager()

        breaker = manager.create_circuit_breaker(
            "test",
            CircuitType.CONNECTION_FAILURE
        )

        assert breaker.name == "test"
        assert manager.get_circuit_breaker("test") is breaker

    def test_duplicate_name_raises_error(self):
        """Should raise error for duplicate breaker names."""
        manager = CircuitBreakerManager()
        manager.create_circuit_breaker("test", CircuitType.CONNECTION_FAILURE)

        with pytest.raises(ValueError):
            manager.create_circuit_breaker("test", CircuitType.RATE_LIMIT)

    def test_get_system_status(self):
        """Should return system-wide status."""
        manager = CircuitBreakerManager()
        manager.create_circuit_breaker("breaker1", CircuitType.CONNECTION_FAILURE)
        manager.create_circuit_breaker("breaker2", CircuitType.RATE_LIMIT)

        status = manager.get_system_status()

        assert status['total_circuit_breakers'] == 2
        assert status['closed_breakers'] == 2
        assert status['open_breakers'] == 0
        assert 'breaker1' in status['circuit_breakers']
        assert 'breaker2' in status['circuit_breakers']

    @pytest.mark.asyncio
    async def test_any_open(self):
        """Should detect when any breaker is open."""
        manager = CircuitBreakerManager()
        breaker1 = manager.create_circuit_breaker("breaker1", CircuitType.CONNECTION_FAILURE)
        manager.create_circuit_breaker("breaker2", CircuitType.RATE_LIMIT)

        assert not manager.any_open()

        await breaker1.force_open()

        assert manager.any_open()

    def test_get_open_breakers(self):
        """Should return list of open breaker names."""
        manager = CircuitBreakerManager()
        manager.create_circuit_breaker("breaker1", CircuitType.CONNECTION_FAILURE)
        manager.create_circuit_breaker("breaker2", CircuitType.RATE_LIMIT)

        assert manager.get_open_breakers() == []

    def test_reset_all(self):
        """Should reset all breakers."""
        manager = CircuitBreakerManager()
        breaker1 = manager.create_circuit_breaker("breaker1", CircuitType.CONNECTION_FAILURE)
        breaker2 = manager.create_circuit_breaker("breaker2", CircuitType.RATE_LIMIT)

        # Modify state
        breaker1.metrics.failed_requests = 10
        breaker2.metrics.failed_requests = 5

        manager.reset_all()

        assert breaker1.metrics.failed_requests == 0
        assert breaker2.metrics.failed_requests == 0


# =============================================================================
# Trading Circuit Breaker Tests
# =============================================================================

class TestTradingCircuitBreakers:
    """Tests for TradingCircuitBreakers."""

    @pytest.mark.asyncio
    async def test_initial_state_allows_trading(self, mock_portfolio, trading_config):
        """Should allow trading in initial state."""
        breakers = TradingCircuitBreakers(mock_portfolio, trading_config)

        assert breakers.can_trade()
        assert not breakers.kill_switch_active

    @pytest.mark.asyncio
    async def test_daily_loss_trips_breaker(self, mock_portfolio, trading_config):
        """Should trip when daily loss exceeds threshold."""
        mock_portfolio.get_daily_pnl_pct.return_value = Decimal("-2.5")

        breakers = TradingCircuitBreakers(mock_portfolio, trading_config)
        await breakers.start_monitoring()

        # Wait for monitoring to detect the breach
        await asyncio.sleep(0.2)

        assert not breakers.can_trade()
        reasons = breakers.get_blocking_reasons()
        assert any("daily_loss" in r for r in reasons)

        await breakers.stop_monitoring()

    @pytest.mark.asyncio
    async def test_drawdown_activates_kill_switch(self, mock_portfolio, trading_config):
        """Should activate kill switch on excessive drawdown."""
        mock_portfolio.get_max_drawdown.return_value = Decimal("-12.0")

        breakers = TradingCircuitBreakers(mock_portfolio, trading_config)
        await breakers.start_monitoring()

        await asyncio.sleep(0.2)

        assert breakers.kill_switch_active
        assert not breakers.can_trade()

        await breakers.stop_monitoring()

    @pytest.mark.asyncio
    async def test_kill_switch_requires_manual_reset(self, mock_portfolio, trading_config):
        """Kill switch should require manual reset."""
        mock_portfolio.get_max_drawdown.return_value = Decimal("-12.0")

        breakers = TradingCircuitBreakers(mock_portfolio, trading_config)
        await breakers.start_monitoring()
        await asyncio.sleep(0.2)

        assert breakers.kill_switch_active

        # Fix the drawdown
        mock_portfolio.get_max_drawdown.return_value = Decimal("-5.0")
        await asyncio.sleep(0.2)

        # Should still be active (requires manual reset)
        assert breakers.kill_switch_active

        # Manual reset
        breakers.reset_kill_switch("test_auth")
        assert not breakers.kill_switch_active

        await breakers.stop_monitoring()

    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_portfolio, trading_config):
        """Should enforce rate limits."""
        breakers = TradingCircuitBreakers(mock_portfolio, trading_config)

        # Record orders up to limit
        for _ in range(5):
            result = await breakers.record_order()
            assert result

        # Next order should be rejected
        result = await breakers.record_order()
        assert not result

    @pytest.mark.asyncio
    async def test_position_concentration_check(self, mock_portfolio, trading_config):
        """Should enforce position concentration limits."""
        breakers = TradingCircuitBreakers(mock_portfolio, trading_config)

        # 15% concentration - should be allowed
        result = await breakers.check_position_concentration("SPY", Decimal("15000"))
        assert result

        # 25% concentration - should be rejected
        result = await breakers.check_position_concentration("SPY", Decimal("25000"))
        assert not result

    @pytest.mark.asyncio
    async def test_connection_failure_tracking(self, mock_portfolio, trading_config):
        """Should track connection failures."""
        breakers = TradingCircuitBreakers(mock_portfolio, trading_config)

        # Record failures
        for _ in range(3):
            await breakers.record_connection_failure("Connection timeout")

        # Connection breaker should be open
        status = breakers.manager.get_circuit_breaker("connection").get_status()
        assert status['state'] == 'open'

    @pytest.mark.asyncio
    async def test_trip_callback(self, mock_portfolio, trading_config):
        """Should call trip callbacks when breakers trip."""
        breakers = TradingCircuitBreakers(mock_portfolio, trading_config)

        trip_events = []

        def on_trip(name, reason):
            trip_events.append((name, reason))

        breakers.register_trip_callback(on_trip)

        # Trip via connection failures
        for _ in range(3):
            await breakers.record_connection_failure("Test error")

        assert len(trip_events) >= 1

    @pytest.mark.asyncio
    async def test_warning_callback(self, mock_portfolio, trading_config):
        """Should call warning callbacks at warning thresholds."""
        # Set P&L at warning level but not limit
        mock_portfolio.get_daily_pnl_pct.return_value = Decimal("-1.7")

        breakers = TradingCircuitBreakers(mock_portfolio, trading_config)

        warning_events = []

        def on_warning(name, message):
            warning_events.append((name, message))

        breakers.register_warning_callback(on_warning)

        await breakers.start_monitoring()
        await asyncio.sleep(0.2)

        # Should have warning but still allow trading
        assert breakers.can_trade()
        assert len(warning_events) >= 1

        await breakers.stop_monitoring()

    @pytest.mark.asyncio
    async def test_reset_breaker(self, mock_portfolio, trading_config):
        """Should reset individual breakers."""
        breakers = TradingCircuitBreakers(mock_portfolio, trading_config)

        # Trip connection breaker
        for _ in range(3):
            await breakers.record_connection_failure("Test")

        # Reset it
        result = breakers.reset_breaker("connection")
        assert result

        # Should be able to record success now
        await breakers.record_connection_success()

    @pytest.mark.asyncio
    async def test_get_status(self, mock_portfolio, trading_config):
        """Should return comprehensive status."""
        breakers = TradingCircuitBreakers(mock_portfolio, trading_config)

        status = breakers.get_status()

        assert status.can_trade
        assert isinstance(status.blocking_breakers, list)
        assert isinstance(status.warning_breakers, list)
        assert 'details' in status.__dict__

    @pytest.mark.asyncio
    async def test_get_blocking_reasons(self, mock_portfolio, trading_config):
        """Should list all blocking reasons."""
        breakers = TradingCircuitBreakers(mock_portfolio, trading_config)

        # Initially empty
        reasons = breakers.get_blocking_reasons()
        assert len(reasons) == 0

        # Trip a breaker
        for _ in range(3):
            await breakers.record_connection_failure("Test")

        reasons = breakers.get_blocking_reasons()
        assert len(reasons) >= 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for circuit breakers."""

    @pytest.mark.asyncio
    async def test_full_trading_workflow(self, mock_portfolio):
        """Test complete trading workflow with circuit breakers."""
        config = TradingBreakerConfig(
            daily_loss_limit_pct=Decimal("-5.0"),
            max_drawdown_pct=Decimal("-15.0"),
            max_orders_per_minute=10,
            check_interval_seconds=0.1
        )

        breakers = TradingCircuitBreakers(mock_portfolio, config)
        await breakers.start_monitoring()

        # Simulate normal trading
        assert breakers.can_trade()

        for _ in range(5):
            assert await breakers.record_order()
            await asyncio.sleep(0.01)

        # Simulate loss event
        mock_portfolio.get_daily_pnl_pct.return_value = Decimal("-6.0")
        await asyncio.sleep(0.2)

        assert not breakers.can_trade()

        # Reset and resume
        breakers.reset_breaker("daily_loss")
        mock_portfolio.get_daily_pnl_pct.return_value = Decimal("-1.0")

        assert breakers.can_trade()

        await breakers.stop_monitoring()

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff behavior."""
        config = CircuitBreakerConfig(
            failure_threshold=1,
            open_timeout_seconds=1,
            exponential_backoff=True,
            backoff_multiplier=2.0,
            max_backoff_seconds=10
        )

        breaker = CircuitBreaker("backoff_test", CircuitType.CONNECTION_FAILURE, config)

        async def failing():
            raise ValueError("Test")

        # First trip
        with pytest.raises(ValueError):
            await breaker.call(failing)

        assert breaker.current_backoff == 1  # Initial backoff

        # Recover
        await asyncio.sleep(1.1)
        async def success():
            return True
        await breaker.call(success)
        await breaker.call(success)

        # Second trip should use initial backoff after recovery
        with pytest.raises(ValueError):
            await breaker.call(failing)

        assert breaker.current_backoff == 1  # Backoff resets on recovery


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
