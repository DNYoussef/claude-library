# Circuit Breakers Library Component

Production-ready circuit breaker implementations for trading systems and financial applications.

## Overview

This library provides comprehensive circuit breaker protection for trading systems:

- **Generic Circuit Breaker**: Standard CLOSED/OPEN/HALF_OPEN state machine for any protected operation
- **Trading Circuit Breakers**: 6 specialized breakers for financial P&L protection

## Features

- Thread-safe state management
- Event callbacks for monitoring and alerting
- Decimal precision for financial calculations
- Configurable thresholds and timeouts
- Exponential backoff recovery
- Comprehensive metrics and status reporting

## Installation

Copy this component to your project or add to your library path:

```python
import sys
sys.path.insert(0, r"C:\Users\17175\.claude\library\components\trading")

from circuit_breakers import CircuitBreaker, TradingCircuitBreakers
```

## Quick Start

### Basic Circuit Breaker (API Protection)

```python
from circuit_breakers import CircuitBreaker, CircuitType, CircuitBreakerConfig

# Create a circuit breaker for broker API calls
config = CircuitBreakerConfig(
    failure_threshold=5,        # Trip after 5 failures
    open_timeout_seconds=60,    # Stay open for 60 seconds
    success_threshold=3         # Need 3 successes to recover
)
breaker = CircuitBreaker("broker_api", CircuitType.CONNECTION_FAILURE, config)

# Protect an async function
try:
    result = await breaker.call(broker.get_positions)
except CircuitOpenException:
    # Circuit is open, use fallback or wait
    logger.warning("Broker API circuit open, using cached data")
    result = get_cached_positions()

# Register callbacks for monitoring
breaker.register_trip_callback(lambda name, type: alert_ops_team(name))
breaker.register_recovery_callback(lambda name, type: log_recovery(name))
```

### Trading Circuit Breakers (P&L Protection)

```python
from decimal import Decimal
from circuit_breakers import TradingCircuitBreakers, TradingBreakerConfig

# Configure thresholds
config = TradingBreakerConfig(
    # Daily Loss Breaker
    daily_loss_limit_pct=Decimal("-2.0"),   # -2% triggers halt
    daily_loss_warning_pct=Decimal("-1.5"), # -1.5% warning

    # Max Drawdown Kill Switch
    max_drawdown_pct=Decimal("-10.0"),      # -10% kill switch
    drawdown_warning_pct=Decimal("-7.0"),   # -7% warning

    # Position Concentration
    max_position_pct=Decimal("20.0"),       # 20% max single position

    # Rate Limiting
    max_orders_per_minute=10,
    max_orders_per_hour=100
)

# Initialize with portfolio provider
breakers = TradingCircuitBreakers(portfolio_manager, config)

# Start background monitoring
await breakers.start_monitoring()

# Check before trading
if breakers.can_trade():
    # Record the order for rate limiting
    if await breakers.record_order():
        # Check position concentration
        if await breakers.check_position_concentration("SPY", proposed_value):
            execute_order(order)
        else:
            log("Position concentration limit exceeded")
    else:
        log("Rate limit exceeded")
else:
    reasons = breakers.get_blocking_reasons()
    log(f"Trading blocked: {reasons}")

# Register callbacks
breakers.register_trip_callback(on_breaker_trip)
breakers.register_warning_callback(on_warning)
```

## The 6 Trading Circuit Breaker Types

| Type | Default Threshold | Purpose |
|------|------------------|---------|
| **Daily Loss** | -2% | Halt trading when daily P&L drops below limit |
| **Max Drawdown** | -10% | Kill switch for excessive drawdown (requires manual reset) |
| **Position Concentration** | 20% | Prevent over-concentration in single positions |
| **Volatility** | 3 std dev | Halt during extreme market volatility |
| **Rate Limit** | 10/min, 100/hr | Prevent excessive order frequency |
| **Connection** | 3 failures | Detect and handle API/broker failures |

## Circuit Breaker States

```
    CLOSED (Normal)
        |
        | (failures exceed threshold)
        v
      OPEN (Blocking)
        |
        | (timeout expires)
        v
    HALF_OPEN (Testing)
        |
        +---> CLOSED (successes >= threshold)
        |
        +---> OPEN (any failure)
```

## Configuration Reference

### CircuitBreakerConfig

```python
@dataclass
class CircuitBreakerConfig:
    # Failure thresholds
    failure_threshold: int = 5              # Failures to trip
    failure_rate_threshold: float = 0.5     # Rate (0.0-1.0) to trip
    success_threshold: int = 3              # Successes to recover

    # Time windows
    failure_window_seconds: int = 60        # Failure counting window
    open_timeout_seconds: int = 60          # Time in open state
    half_open_timeout_seconds: int = 30     # Testing duration

    # Recovery behavior
    exponential_backoff: bool = True        # Use exponential backoff
    max_backoff_seconds: int = 300          # Max backoff (5 minutes)
    backoff_multiplier: float = 2.0         # Backoff multiplier

    # Trading thresholds (Decimal for precision)
    daily_loss_limit_pct: Decimal = Decimal("-2.0")
    max_drawdown_pct: Decimal = Decimal("-10.0")
    position_limit: Decimal = Decimal("0.20")
```

### TradingBreakerConfig

```python
@dataclass
class TradingBreakerConfig:
    # Daily Loss
    daily_loss_limit_pct: Decimal = Decimal("-2.0")
    daily_loss_warning_pct: Decimal = Decimal("-1.5")

    # Max Drawdown
    max_drawdown_pct: Decimal = Decimal("-10.0")
    drawdown_warning_pct: Decimal = Decimal("-7.0")

    # Position Concentration
    max_position_pct: Decimal = Decimal("20.0")
    position_warning_pct: Decimal = Decimal("15.0")

    # Volatility
    volatility_std_threshold: Decimal = Decimal("3.0")
    volatility_lookback_days: int = 20

    # Rate Limiting
    max_orders_per_minute: int = 10
    max_orders_per_hour: int = 100

    # Connection
    connection_failure_threshold: int = 3
    connection_timeout_seconds: int = 30

    # Monitoring
    check_interval_seconds: float = 1.0
    cooldown_seconds: int = 300

    # Recovery
    auto_recovery: bool = False
    require_manual_reset: bool = True  # For kill switch
```

## Portfolio Provider Protocol

Implement this protocol to integrate with your portfolio system:

```python
from circuit_breakers import PortfolioProvider
from decimal import Decimal

class MyPortfolioManager(PortfolioProvider):
    async def get_total_value(self) -> Decimal:
        return self.total_portfolio_value

    async def get_daily_pnl(self) -> Decimal:
        return self.today_pnl

    async def get_daily_pnl_pct(self) -> Decimal:
        return (self.today_pnl / self.starting_value) * 100

    async def get_max_drawdown(self) -> Decimal:
        return self.calculate_drawdown_from_peak()

    async def get_position_concentration(self, symbol: str) -> Decimal:
        position_value = self.positions.get(symbol, Decimal("0"))
        return (position_value / self.total_portfolio_value) * 100
```

## API Reference

### CircuitBreaker

| Method | Description |
|--------|-------------|
| `call(func, *args, **kwargs)` | Execute protected function |
| `register_trip_callback(cb)` | Register callback for trips |
| `register_recovery_callback(cb)` | Register callback for recovery |
| `force_open()` | Manually trip the breaker |
| `force_close()` | Manually reset the breaker |
| `reset()` | Reset to initial state |
| `get_status()` | Get current status dict |
| `is_open` | Property: check if open |
| `is_closed` | Property: check if closed |

### TradingCircuitBreakers

| Method | Description |
|--------|-------------|
| `start_monitoring()` | Start background threshold checks |
| `stop_monitoring()` | Stop monitoring |
| `can_trade()` | Check if trading allowed |
| `get_blocking_reasons()` | Get list of blocking reasons |
| `record_order()` | Record order for rate limiting |
| `check_position_concentration(symbol, value)` | Check concentration limit |
| `record_connection_failure(error)` | Record API failure |
| `record_connection_success()` | Record API success |
| `reset_kill_switch(auth_key)` | Reset the kill switch |
| `reset_breaker(name)` | Reset specific breaker |
| `reset_all()` | Reset all breakers |
| `get_status()` | Get comprehensive status |

## Source

Extracted from: `D:\Projects\trader-ai`

Original files:
- `src/safety/circuit_breakers/circuit_breaker.py`
- `src/safety/kill_switch_system.py`
- `src/safety/core/safety_manager.py`

## Version

- **Version**: 1.0.0
- **Author**: David Youssef
- **License**: MIT
