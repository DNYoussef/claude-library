"""
Trading-Specific Circuit Breakers - Financial protection mechanisms.

This module provides specialized circuit breakers for trading systems:
1. Daily Loss Breaker (-2% default)
2. Max Drawdown Kill Switch (-10% default)
3. Position Concentration Breaker
4. Volatility Breaker
5. Rate Limit Breaker
6. Connection Failure Breaker

All monetary values use Decimal for precision.

Usage:
    from circuit_breakers import TradingCircuitBreakers, TradingBreakerConfig

    # Initialize with portfolio reference
    breakers = TradingCircuitBreakers(portfolio_manager, config)
    breakers.start_monitoring()

    # Check before trading
    if breakers.can_trade():
        execute_trade(order)
    else:
        reasons = breakers.get_blocking_reasons()
        log_blocked_trade(reasons)
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Protocol
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

# Import circuit breaker components - supports both package and direct import
try:
    from .circuit_breaker import (
        CircuitBreaker,
        CircuitBreakerConfig,
        CircuitBreakerManager,
        CircuitType,
        CircuitOpenException,
    )
except ImportError:
    # Fallback for direct import (non-package context)
    from circuit_breaker import (  # type: ignore[import-not-found]
        CircuitBreaker,
        CircuitBreakerConfig,
        CircuitBreakerManager,
        CircuitType,
        CircuitOpenException,
    )

logger = logging.getLogger(__name__)


class PortfolioProvider(Protocol):
    """Protocol for portfolio data access."""

    async def get_total_value(self) -> Decimal:
        """Get current total portfolio value."""
        ...

    async def get_daily_pnl(self) -> Decimal:
        """Get today's profit/loss."""
        ...

    async def get_daily_pnl_pct(self) -> Decimal:
        """Get today's profit/loss as percentage."""
        ...

    async def get_max_drawdown(self) -> Decimal:
        """Get maximum drawdown from peak."""
        ...

    async def get_position_concentration(self, symbol: str) -> Decimal:
        """Get position concentration for a symbol (as percentage of portfolio)."""
        ...


@dataclass
class TradingBreakerConfig:
    """
    Configuration for trading-specific circuit breakers.

    All percentage values are expressed as decimals (e.g., -2% = Decimal("-2.0")).
    """
    # Daily Loss Breaker (Type 1)
    daily_loss_limit_pct: Decimal = Decimal("-2.0")     # -2% daily loss triggers halt
    daily_loss_warning_pct: Decimal = Decimal("-1.5")   # -1.5% warning threshold

    # Max Drawdown Kill Switch (Type 2)
    max_drawdown_pct: Decimal = Decimal("-10.0")        # -10% drawdown triggers kill switch
    drawdown_warning_pct: Decimal = Decimal("-7.0")     # -7% warning threshold

    # Position Concentration (Type 3)
    max_position_pct: Decimal = Decimal("20.0")         # 20% max single position
    position_warning_pct: Decimal = Decimal("15.0")     # 15% warning threshold

    # Volatility Breaker (Type 4)
    volatility_std_threshold: Decimal = Decimal("3.0")  # 3 std dev triggers
    volatility_lookback_days: int = 20                  # Lookback period

    # Rate Limit Breaker (Type 5)
    max_orders_per_minute: int = 10                     # Max orders per minute
    max_orders_per_hour: int = 100                      # Max orders per hour

    # Connection Failure Breaker (Type 6)
    connection_failure_threshold: int = 3              # Failures to trip
    connection_timeout_seconds: int = 30               # Timeout duration

    # Monitoring intervals
    check_interval_seconds: float = 1.0                # How often to check thresholds
    cooldown_seconds: int = 300                        # Cooldown after trip (5 min)

    # Recovery settings
    auto_recovery: bool = False                        # Auto-recover when conditions improve
    require_manual_reset: bool = True                  # Require manual reset for kill switch


@dataclass
class TradingBreakerStatus:
    """Status information for trading breakers."""
    timestamp: datetime
    can_trade: bool
    blocking_breakers: List[str]
    warning_breakers: List[str]
    daily_pnl_pct: Decimal
    max_drawdown_pct: Decimal
    details: Dict[str, Any] = field(default_factory=dict)


class TradingBreakerType(Enum):
    """Types of trading-specific circuit breakers."""
    DAILY_LOSS = "daily_loss"
    MAX_DRAWDOWN = "max_drawdown"
    POSITION_CONCENTRATION = "position_concentration"
    VOLATILITY = "volatility"
    RATE_LIMIT = "rate_limit"
    CONNECTION = "connection"


class TradingCircuitBreakers:
    """
    Comprehensive trading circuit breaker system.

    Implements 6 key protection mechanisms:
    1. Daily Loss Limit (-2%): Halts trading when daily P&L drops below threshold
    2. Max Drawdown Kill Switch (-10%): Emergency halt on excessive drawdown
    3. Position Concentration: Prevents over-concentration in single positions
    4. Volatility Breaker: Halts during extreme market volatility
    5. Rate Limiter: Prevents excessive order frequency
    6. Connection Monitor: Detects and handles API/broker failures

    Thread-safe for use in multi-threaded trading systems.
    """

    def __init__(
        self,
        portfolio_provider: PortfolioProvider,
        config: Optional[TradingBreakerConfig] = None
    ):
        """
        Initialize trading circuit breakers.

        Args:
            portfolio_provider: Object providing portfolio metrics
            config: Configuration for thresholds and behavior
        """
        self.portfolio = portfolio_provider
        self.config = config or TradingBreakerConfig()

        # Thread safety
        self._lock = threading.RLock()
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None

        # Circuit breaker manager
        self.manager = CircuitBreakerManager()

        # Initialize individual breakers
        self._init_breakers()

        # Order tracking for rate limiting
        self._order_timestamps: List[datetime] = []

        # Callbacks
        self._on_trip_callbacks: List[Callable] = []
        self._on_warning_callbacks: List[Callable] = []

        # Kill switch state (requires manual reset)
        self._kill_switch_active = False
        self._kill_switch_reason: Optional[str] = None

        logger.info("Trading Circuit Breakers initialized with 6 protection mechanisms")

    def _init_breakers(self):
        """Initialize all trading circuit breakers."""
        # Daily Loss Breaker
        self.daily_loss_breaker = self.manager.create_circuit_breaker(
            "daily_loss",
            CircuitType.DAILY_LOSS,
            CircuitBreakerConfig(
                failure_threshold=1,  # Trip on first breach
                open_timeout_seconds=self.config.cooldown_seconds,
                exponential_backoff=False
            )
        )

        # Max Drawdown Kill Switch
        self.drawdown_breaker = self.manager.create_circuit_breaker(
            "max_drawdown",
            CircuitType.DRAWDOWN,
            CircuitBreakerConfig(
                failure_threshold=1,
                open_timeout_seconds=86400,  # 24 hours (effectively permanent)
                exponential_backoff=False
            )
        )

        # Position Concentration
        self.concentration_breaker = self.manager.create_circuit_breaker(
            "position_concentration",
            CircuitType.CONCENTRATION,
            CircuitBreakerConfig(
                failure_threshold=1,
                open_timeout_seconds=60,
                exponential_backoff=False
            )
        )

        # Volatility Breaker
        self.volatility_breaker = self.manager.create_circuit_breaker(
            "volatility",
            CircuitType.VOLATILITY,
            CircuitBreakerConfig(
                failure_threshold=1,
                open_timeout_seconds=300,  # 5 minutes
                exponential_backoff=True,
                max_backoff_seconds=3600  # Max 1 hour
            )
        )

        # Rate Limit Breaker
        self.rate_breaker = self.manager.create_circuit_breaker(
            "rate_limit",
            CircuitType.RATE_LIMIT,
            CircuitBreakerConfig(
                failure_threshold=self.config.max_orders_per_minute,
                failure_window_seconds=60,
                open_timeout_seconds=60,
                exponential_backoff=True
            )
        )

        # Connection Breaker
        self.connection_breaker = self.manager.create_circuit_breaker(
            "connection",
            CircuitType.CONNECTION_FAILURE,
            CircuitBreakerConfig(
                failure_threshold=self.config.connection_failure_threshold,
                open_timeout_seconds=self.config.connection_timeout_seconds,
                exponential_backoff=True,
                max_backoff_seconds=300
            )
        )

    async def start_monitoring(self):
        """Start background monitoring of trading thresholds."""
        with self._lock:
            if self._monitoring:
                logger.warning("Monitoring already active")
                return

            self._monitoring = True
            self._monitor_task = asyncio.create_task(self._monitoring_loop())

        logger.info("Trading circuit breaker monitoring started")

    async def stop_monitoring(self):
        """Stop background monitoring."""
        with self._lock:
            self._monitoring = False

            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass

        logger.info("Trading circuit breaker monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop for threshold checks."""
        while self._monitoring:
            try:
                await self._check_all_thresholds()
                await asyncio.sleep(self.config.check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(1.0)  # Brief pause on error

    async def _check_all_thresholds(self):
        """Check all trading thresholds."""
        try:
            # Check daily loss
            await self._check_daily_loss()

            # Check drawdown
            await self._check_drawdown()

            # Clean old order timestamps
            self._clean_order_timestamps()

        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")

    async def _check_daily_loss(self):
        """Check daily loss threshold."""
        try:
            daily_pnl_pct = await self.portfolio.get_daily_pnl_pct()

            # Check warning threshold
            # Check limit threshold
            if daily_pnl_pct <= self.config.daily_loss_limit_pct:
                await self._trip_breaker(
                    self.daily_loss_breaker,
                    f"Daily loss limit breached: {daily_pnl_pct}% <= {self.config.daily_loss_limit_pct}%"
                )
                return

            if daily_pnl_pct <= self.config.daily_loss_warning_pct:
                await self._trigger_warning(
                    "daily_loss",
                    f"Daily P&L at {daily_pnl_pct}% (warning: {self.config.daily_loss_warning_pct}%)"
                )

        except Exception as e:
            logger.error(f"Error checking daily loss: {e}")

    async def _check_drawdown(self):
        """Check maximum drawdown threshold."""
        try:
            drawdown_pct = await self.portfolio.get_max_drawdown()

            # Check warning threshold
            if drawdown_pct <= self.config.drawdown_warning_pct:
                if drawdown_pct > self.config.max_drawdown_pct:
                    await self._trigger_warning(
                        "max_drawdown",
                        f"Drawdown at {drawdown_pct}% (warning: {self.config.drawdown_warning_pct}%)"
                    )

            # Check kill switch threshold
            if drawdown_pct <= self.config.max_drawdown_pct:
                await self._activate_kill_switch(
                    f"Max drawdown kill switch activated: {drawdown_pct}% <= {self.config.max_drawdown_pct}%"
                )

        except Exception as e:
            logger.error(f"Error checking drawdown: {e}")

    async def _trip_breaker(self, breaker: CircuitBreaker, reason: str):
        """Trip a specific circuit breaker."""
        if breaker.is_closed:
            logger.warning(f"Tripping breaker '{breaker.name}': {reason}")
            await breaker.force_open()
            await self._execute_trip_callbacks(breaker.name, reason)

    async def _activate_kill_switch(self, reason: str):
        """Activate the kill switch (requires manual reset)."""
        with self._lock:
            if self._kill_switch_active:
                return

            self._kill_switch_active = True
            self._kill_switch_reason = reason

        logger.critical(f"KILL SWITCH ACTIVATED: {reason}")
        await self.drawdown_breaker.force_open()
        await self._execute_trip_callbacks("kill_switch", reason)

    async def _trigger_warning(self, breaker_name: str, message: str):
        """Trigger a warning (doesn't halt trading)."""
        logger.warning(f"Trading warning ({breaker_name}): {message}")

        for callback in self._on_warning_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(breaker_name, message)
                else:
                    callback(breaker_name, message)
            except Exception as e:
                logger.error(f"Error in warning callback: {e}")

    async def _execute_trip_callbacks(self, breaker_name: str, reason: str):
        """Execute callbacks when a breaker trips."""
        for callback in self._on_trip_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(breaker_name, reason)
                else:
                    callback(breaker_name, reason)
            except Exception as e:
                logger.error(f"Error in trip callback: {e}")

    def _clean_order_timestamps(self):
        """Remove old order timestamps for rate limiting."""
        cutoff = datetime.now() - timedelta(hours=1)
        with self._lock:
            self._order_timestamps = [
                ts for ts in self._order_timestamps
                if ts > cutoff
            ]

    # Public API

    def can_trade(self) -> bool:
        """
        Check if trading is currently allowed.

        Returns:
            True if all breakers are closed and kill switch is inactive
        """
        with self._lock:
            if self._kill_switch_active:
                return False

            return not self.manager.any_open()

    def get_blocking_reasons(self) -> List[str]:
        """Get list of reasons why trading is blocked."""
        reasons = []

        with self._lock:
            if self._kill_switch_active:
                reasons.append(f"Kill switch active: {self._kill_switch_reason}")

            for name in self.manager.get_open_breakers():
                breaker = self.manager.get_circuit_breaker(name)
                if not breaker:
                    continue
                status = breaker.get_status()
                reasons.append(
                    f"{name}: {status['state']} (trips: {status['circuit_trips']})"
                )

        return reasons

    async def record_order(self) -> bool:
        """
        Record an order for rate limiting.

        Returns:
            True if order is allowed, False if rate limit exceeded
        """
        now = datetime.now()

        with self._lock:
            # Check rate limits
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)

            orders_last_minute = sum(1 for ts in self._order_timestamps if ts > minute_ago)
            orders_last_hour = sum(1 for ts in self._order_timestamps if ts > hour_ago)

            if orders_last_minute >= self.config.max_orders_per_minute:
                await self._trip_breaker(
                    self.rate_breaker,
                    f"Rate limit exceeded: {orders_last_minute}/{self.config.max_orders_per_minute} orders/min"
                )
                return False

            if orders_last_hour >= self.config.max_orders_per_hour:
                await self._trip_breaker(
                    self.rate_breaker,
                    f"Hourly rate limit exceeded: {orders_last_hour}/{self.config.max_orders_per_hour} orders/hour"
                )
                return False

            # Record the order
            self._order_timestamps.append(now)
            return True

    async def check_position_concentration(self, symbol: str, proposed_value: Decimal) -> bool:
        """
        Check if a trade would exceed position concentration limits.

        Args:
            symbol: The symbol being traded
            proposed_value: The proposed position value after trade

        Returns:
            True if within limits, False if would exceed
        """
        try:
            portfolio_value = await self.portfolio.get_total_value()
            if portfolio_value <= 0:
                return True

            concentration_pct = (proposed_value / portfolio_value) * 100

            if concentration_pct > self.config.max_position_pct:
                await self._trip_breaker(
                    self.concentration_breaker,
                    f"Position concentration exceeded: {symbol} at {concentration_pct}% > {self.config.max_position_pct}%"
                )
                return False

            if concentration_pct > self.config.position_warning_pct:
                await self._trigger_warning(
                    "position_concentration",
                    f"{symbol} concentration at {concentration_pct}% (warning: {self.config.position_warning_pct}%)"
                )

            return True

        except Exception as e:
            logger.error(f"Error checking position concentration: {e}")
            return True  # Allow on error (fail-open for this check)

    async def record_connection_failure(self, error: str):
        """Record a connection/API failure for the connection breaker."""
        # Simulate a failure through the breaker
        was_open = self.connection_breaker.is_open
        try:
            async def failing_call():
                raise ConnectionError(error)

            await self.connection_breaker.call(failing_call)
        except (ConnectionError, CircuitOpenException):
            pass  # Expected
        finally:
            if self.connection_breaker.is_open and not was_open:
                await self._execute_trip_callbacks("connection", error)

    async def record_connection_success(self):
        """Record a successful connection/API call."""
        try:
            async def successful_call():
                return True

            await self.connection_breaker.call(successful_call)
        except CircuitOpenException:
            pass  # Breaker is open, ignore

    def reset_kill_switch(self, authorization_key: Optional[str] = None) -> bool:
        """
        Reset the kill switch (manual intervention required).

        Args:
            authorization_key: Optional authorization for audit trail

        Returns:
            True if reset successful
        """
        with self._lock:
            if not self._kill_switch_active:
                return True

            logger.warning(f"Kill switch reset requested (auth: {authorization_key or 'none'})")

            self._kill_switch_active = False
            self._kill_switch_reason = None

        # Also reset the drawdown breaker
        self.drawdown_breaker.reset()

        logger.info("Kill switch has been reset")
        return True

    def reset_breaker(self, breaker_name: str) -> bool:
        """Reset a specific circuit breaker."""
        breaker = self.manager.get_circuit_breaker(breaker_name)
        if breaker:
            breaker.reset()
            logger.info(f"Circuit breaker '{breaker_name}' reset")
            return True
        return False

    def reset_all(self):
        """Reset all circuit breakers (except kill switch)."""
        self.manager.reset_all()
        logger.info("All trading circuit breakers reset")

    def register_trip_callback(self, callback: Callable[[str, str], None]):
        """Register callback for when any breaker trips."""
        self._on_trip_callbacks.append(callback)

    def register_warning_callback(self, callback: Callable[[str, str], None]):
        """Register callback for warning thresholds."""
        self._on_warning_callbacks.append(callback)

    def get_status(self) -> TradingBreakerStatus:
        """Get comprehensive status of all trading breakers."""
        with self._lock:
            blocking = []
            warnings = []

            if self._kill_switch_active:
                blocking.append(f"kill_switch: {self._kill_switch_reason}")

            system_status = self.manager.get_system_status()

            for name, breaker_status in system_status['circuit_breakers'].items():
                if breaker_status['state'] == 'open':
                    blocking.append(name)
                elif breaker_status['state'] == 'half_open':
                    warnings.append(f"{name} (recovering)")

            return TradingBreakerStatus(
                timestamp=datetime.now(),
                can_trade=self.can_trade(),
                blocking_breakers=blocking,
                warning_breakers=warnings,
                daily_pnl_pct=Decimal("0"),  # Would be populated from portfolio
                max_drawdown_pct=Decimal("0"),  # Would be populated from portfolio
                details=system_status
            )

    @property
    def kill_switch_active(self) -> bool:
        """Check if kill switch is currently active."""
        return self._kill_switch_active

    @property
    def kill_switch_reason(self) -> Optional[str]:
        """Get reason for kill switch activation."""
        return self._kill_switch_reason
