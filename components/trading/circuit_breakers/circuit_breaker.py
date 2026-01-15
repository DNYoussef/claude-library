"""
Circuit Breaker Implementation - Generic protection triggers for financial systems.

This module implements various circuit breaker patterns to prevent system
failures from cascading and to provide automatic protection mechanisms.

Extracted from Trader AI and generalized for reuse across financial applications.

Key Features:
- Trading circuit breakers (loss limits, position limits)
- Connection circuit breakers (API failures, timeouts)
- Performance circuit breakers (latency, throughput)
- Adaptive thresholds based on market conditions
- Automatic recovery with exponential backoff
- Thread-safe state management
- Event callbacks for triggered breakers

Usage:
    from circuit_breakers import CircuitBreaker, CircuitType, CircuitBreakerConfig

    # Create a circuit breaker for API calls
    config = CircuitBreakerConfig(failure_threshold=5, open_timeout_seconds=60)
    breaker = CircuitBreaker("api_breaker", CircuitType.CONNECTION_FAILURE, config)

    # Use the breaker to protect a function
    result = await breaker.call(my_api_function, arg1, arg2)
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
import threading
from collections import deque

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states following the standard pattern."""
    CLOSED = "closed"        # Normal operation - requests flow through
    OPEN = "open"            # Circuit tripped - blocking all requests
    HALF_OPEN = "half_open"  # Testing recovery - limited requests allowed


class CircuitType(Enum):
    """Types of circuit breakers for different protection scenarios."""
    # Trading-specific breakers
    TRADING_LOSS = "trading_loss"              # P&L loss protection
    TRADING_POSITION = "trading_position"      # Position size protection
    DAILY_LOSS = "daily_loss"                  # Daily loss limit (-2% default)
    DRAWDOWN = "drawdown"                      # Max drawdown kill switch (10% default)
    VOLATILITY = "volatility"                  # Market volatility protection
    CONCENTRATION = "concentration"            # Position concentration limit

    # System breakers
    CONNECTION_FAILURE = "connection_failure"  # API/connection failures
    PERFORMANCE_LATENCY = "performance_latency"  # Response time protection
    RATE_LIMIT = "rate_limit"                  # Request rate protection
    MARKET_VOLATILITY = "market_volatility"    # Market condition protection


@dataclass
class CircuitBreakerConfig:
    """
    Configuration for circuit breaker behavior.

    All thresholds can be configured per-use-case. Defaults are conservative
    for production trading systems.
    """
    # Failure thresholds
    failure_threshold: int = 5              # Number of failures to trip
    failure_rate_threshold: float = 0.5     # Failure rate (0.0-1.0) to trip
    success_threshold: int = 3              # Consecutive successes to close

    # Time windows
    failure_window_seconds: int = 60        # Time window for failure counting
    open_timeout_seconds: int = 60          # How long to stay open
    half_open_timeout_seconds: int = 30     # How long to test in half-open

    # Adaptive behavior
    adaptive_threshold: bool = True         # Adjust thresholds based on conditions
    min_requests_for_rate: int = 10         # Minimum requests before rate calculation

    # Recovery behavior
    exponential_backoff: bool = True        # Use exponential backoff
    max_backoff_seconds: int = 300          # Maximum backoff time (5 minutes)
    backoff_multiplier: float = 2.0         # Backoff multiplication factor

    # Trading-specific thresholds (using Decimal for precision)
    daily_loss_limit_pct: Decimal = Decimal("-2.0")   # -2% daily loss limit
    max_drawdown_pct: Decimal = Decimal("-10.0")      # -10% max drawdown
    position_limit: Decimal = Decimal("0.20")         # 20% single position limit
    volatility_threshold: Decimal = Decimal("3.0")    # 3 std dev volatility trigger


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker performance monitoring."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_trips: int = 0
    time_in_open_state: float = 0.0
    time_in_half_open_state: float = 0.0
    average_response_time: float = 0.0
    last_failure_time: Optional[datetime] = None
    last_trip_time: Optional[datetime] = None
    last_recovery_time: Optional[datetime] = None


@dataclass
class RequestResult:
    """Result of a protected request with timing information."""
    success: bool
    response_time: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class CircuitOpenException(Exception):
    """Exception raised when circuit breaker is open and blocking requests."""

    def __init__(self, breaker_name: str, message: str = None):
        self.breaker_name = breaker_name
        self.message = message or f"Circuit breaker '{breaker_name}' is open"
        super().__init__(self.message)


class CircuitBreaker:
    """
    Circuit breaker implementation with adaptive behavior.

    Protects against cascading failures by monitoring success/failure rates
    and automatically blocking requests when thresholds are exceeded.

    Thread-safe for use in multi-threaded trading systems.

    Example:
        breaker = CircuitBreaker("broker_api", CircuitType.CONNECTION_FAILURE)

        # Protect an async function
        try:
            result = await breaker.call(broker.get_positions)
        except CircuitOpenException:
            # Handle circuit open state
            pass

        # Register callbacks
        breaker.register_trip_callback(lambda name, type: alert_ops(name))
        breaker.register_recovery_callback(lambda name, type: log_recovery(name))
    """

    def __init__(
        self,
        name: str,
        circuit_type: CircuitType,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Unique name for this circuit breaker
            circuit_type: Type of circuit breaker (determines behavior)
            config: Configuration options (uses defaults if None)
        """
        self.name = name
        self.circuit_type = circuit_type
        self.config = config or CircuitBreakerConfig()

        # State management (thread-safe)
        self.state = CircuitState.CLOSED
        self.state_changed_time = datetime.now()
        self._lock = threading.RLock()

        # Metrics and history
        self.metrics = CircuitBreakerMetrics()
        self.request_history: deque = deque(maxlen=1000)
        self.recent_failures: deque = deque()
        self.recent_successes = 0

        # Backoff tracking
        self.backoff_count = 0
        self.current_backoff = self.config.open_timeout_seconds

        # Callbacks for external notification
        self.trip_callbacks: List[Callable] = []
        self.recovery_callbacks: List[Callable] = []

        logger.info(f"Circuit breaker '{name}' initialized for {circuit_type.value}")

    async def call(self, protected_function: Callable, *args, **kwargs) -> Any:
        """
        Execute a function protected by this circuit breaker.

        Args:
            protected_function: Function to protect (sync or async)
            *args, **kwargs: Arguments for the protected function

        Returns:
            Result of the protected function

        Raises:
            CircuitOpenException: If circuit is open
            Exception: Original exception from protected function
        """
        start_time = time.time()

        # Check if circuit allows the request
        if not self._can_make_request():
            self.metrics.failed_requests += 1
            raise CircuitOpenException(self.name)

        try:
            # Execute the protected function
            if asyncio.iscoroutinefunction(protected_function):
                result = await protected_function(*args, **kwargs)
            else:
                result = protected_function(*args, **kwargs)

            # Record success
            response_time = time.time() - start_time
            await self._record_success(response_time)

            return result

        except CircuitOpenException:
            raise  # Re-raise circuit exceptions as-is
        except Exception as e:
            # Record failure
            response_time = time.time() - start_time
            await self._record_failure(str(e), response_time)
            raise

    def _can_make_request(self) -> bool:
        """Check if a request can be made based on current state."""
        with self._lock:
            current_time = datetime.now()

            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.HALF_OPEN:
                # Allow limited requests to test recovery
                return True

            if self.state != CircuitState.OPEN:
                return False

            # Check if we should transition to half-open
            time_since_trip = (current_time - self.state_changed_time).total_seconds()
            if time_since_trip < self.current_backoff:
                return False

            self._transition_to_half_open()
            return True

    async def _record_success(self, response_time: float):
        """Record a successful request and handle state transitions.

        Thread-safe: Acquires lock for state changes, releases before async callbacks.
        """
        should_execute_recovery = False

        with self._lock:
            current_time = datetime.now()

            # Update metrics
            self.metrics.total_requests += 1
            self.metrics.successful_requests += 1
            self._update_average_response_time(response_time)

            # Record in history
            result = RequestResult(True, response_time, None, current_time)
            self.request_history.append(result)

            # Handle state transitions
            if self.state == CircuitState.HALF_OPEN:
                self.recent_successes += 1
                if self.recent_successes >= self.config.success_threshold:
                    self._transition_to_closed()
                    should_execute_recovery = True

            elif self.state == CircuitState.CLOSED:
                # Clean old failures
                self._clean_old_failures()

        # Execute callbacks OUTSIDE the lock to avoid blocking async operations
        if should_execute_recovery:
            await self._execute_recovery_callbacks()

    async def _record_failure(self, error_message: str, response_time: float):
        """Record a failed request and check for circuit trip.

        Thread-safe: Acquires lock for state changes, releases before async callbacks.
        """
        should_trip = False

        with self._lock:
            current_time = datetime.now()

            # Update metrics
            self.metrics.total_requests += 1
            self.metrics.failed_requests += 1
            self.metrics.last_failure_time = current_time

            # Record in history
            result = RequestResult(False, response_time, error_message, current_time)
            self.request_history.append(result)
            self.recent_failures.append(current_time)

            # Clean old failures
            self._clean_old_failures()

            # Check if circuit should trip (determine but don't execute async yet)
            if self._should_trip_circuit():
                should_trip = True
            elif self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                self._transition_to_open()

        # Execute async operations OUTSIDE the lock
        if should_trip:
            await self._trip_circuit()

    def _update_average_response_time(self, response_time: float):
        """Update rolling average response time."""
        if self.metrics.total_requests == 1:
            self.metrics.average_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics.average_response_time = (
                alpha * response_time +
                (1 - alpha) * self.metrics.average_response_time
            )

    def _should_trip_circuit(self) -> bool:
        """Determine if circuit breaker should trip based on failures."""
        if self.state != CircuitState.CLOSED:
            return False

        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=self.config.failure_window_seconds)

        # Count failures in window
        recent_failure_count = len(self.recent_failures)

        # Get total requests in window
        recent_requests = [
            req for req in self.request_history
            if req.timestamp >= window_start
        ]
        total_recent = len(recent_requests)

        # Check failure count threshold
        if recent_failure_count >= self.config.failure_threshold:
            return True

        # Check failure rate threshold
        if (total_recent >= self.config.min_requests_for_rate and total_recent > 0):
            failure_rate = recent_failure_count / total_recent
            if failure_rate >= self.config.failure_rate_threshold:
                return True

        return False

    async def _trip_circuit(self):
        """Trip the circuit breaker to open state.

        Thread-safe: Acquires lock for state changes, releases before async callbacks.
        """
        logger.warning(f"Circuit breaker '{self.name}' tripping to OPEN state")

        with self._lock:
            self._transition_to_open()
            self.metrics.circuit_trips += 1
            self.metrics.last_trip_time = datetime.now()

            # Calculate backoff with exponential increase
            if self.config.exponential_backoff:
                self.current_backoff = min(
                    self.config.open_timeout_seconds * (self.config.backoff_multiplier ** self.backoff_count),
                    self.config.max_backoff_seconds
                )
                self.backoff_count += 1
            else:
                self.current_backoff = self.config.open_timeout_seconds

        # Execute callbacks OUTSIDE the lock
        await self._execute_trip_callbacks()

    def _transition_to_open(self):
        """Transition to OPEN state."""
        if self.state != CircuitState.OPEN:
            old_state = self.state
            self.state = CircuitState.OPEN
            now = datetime.now()

            # Update time tracking
            if old_state == CircuitState.HALF_OPEN:
                time_in_half_open = (now - self.state_changed_time).total_seconds()
                self.metrics.time_in_half_open_state += time_in_half_open

            self.state_changed_time = now
            self.recent_successes = 0

            logger.info(f"Circuit breaker '{self.name}' -> OPEN (backoff: {self.current_backoff}s)")

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state for recovery testing."""
        if self.state != CircuitState.HALF_OPEN:
            old_state = self.state
            now = datetime.now()

            # Update time tracking
            if old_state == CircuitState.OPEN:
                time_in_open = (now - self.state_changed_time).total_seconds()
                self.metrics.time_in_open_state += time_in_open

            self.state = CircuitState.HALF_OPEN
            self.state_changed_time = now
            self.recent_successes = 0

            logger.info(f"Circuit breaker '{self.name}' -> HALF_OPEN")

    def _transition_to_closed(self):
        """Transition to CLOSED state (recovered)."""
        if self.state != CircuitState.CLOSED:
            old_state = self.state
            now = datetime.now()

            # Update time tracking
            if old_state == CircuitState.HALF_OPEN:
                time_in_half_open = (now - self.state_changed_time).total_seconds()
                self.metrics.time_in_half_open_state += time_in_half_open
            elif old_state == CircuitState.OPEN:
                time_in_open = (now - self.state_changed_time).total_seconds()
                self.metrics.time_in_open_state += time_in_open

            self.state = CircuitState.CLOSED
            self.state_changed_time = now
            self.recent_successes = 0
            self.backoff_count = 0  # Reset backoff on successful recovery
            self.current_backoff = self.config.open_timeout_seconds
            self.metrics.last_recovery_time = now

            logger.info(f"Circuit breaker '{self.name}' -> CLOSED (recovered)")

    def _clean_old_failures(self):
        """Remove failures outside the failure window."""
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=self.config.failure_window_seconds)

        while self.recent_failures and self.recent_failures[0] < window_start:
            self.recent_failures.popleft()

    def register_trip_callback(self, callback: Callable[[str, CircuitType], None]):
        """
        Register callback for when circuit trips.

        Args:
            callback: Function called with (breaker_name, circuit_type) when tripped
        """
        self.trip_callbacks.append(callback)

    def register_recovery_callback(self, callback: Callable[[str, CircuitType], None]):
        """
        Register callback for when circuit recovers.

        Args:
            callback: Function called with (breaker_name, circuit_type) on recovery
        """
        self.recovery_callbacks.append(callback)

    async def _execute_trip_callbacks(self):
        """Execute all registered trip callbacks."""
        for callback in self.trip_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.name, self.circuit_type)
                    continue
                callback(self.name, self.circuit_type)
            except Exception as e:
                logger.error(f"Error executing trip callback: {e}")

    async def _execute_recovery_callbacks(self):
        """Execute all registered recovery callbacks."""
        for callback in self.recovery_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.name, self.circuit_type)
                    continue
                callback(self.name, self.circuit_type)
            except Exception as e:
                logger.error(f"Error executing recovery callback: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status as a dictionary."""
        with self._lock:
            current_time = datetime.now()
            time_in_state = (current_time - self.state_changed_time).total_seconds()

            failure_rate = (
                self.metrics.failed_requests / self.metrics.total_requests
                if self.metrics.total_requests > 0 else 0.0
            )

            return {
                'name': self.name,
                'type': self.circuit_type.value,
                'state': self.state.value,
                'time_in_current_state_seconds': time_in_state,
                'total_requests': self.metrics.total_requests,
                'successful_requests': self.metrics.successful_requests,
                'failed_requests': self.metrics.failed_requests,
                'failure_rate': failure_rate,
                'circuit_trips': self.metrics.circuit_trips,
                'current_backoff_seconds': self.current_backoff,
                'recent_failures_count': len(self.recent_failures),
                'average_response_time': self.metrics.average_response_time,
                'last_failure': (self.metrics.last_failure_time.isoformat()
                               if self.metrics.last_failure_time else None),
                'last_trip': (self.metrics.last_trip_time.isoformat()
                            if self.metrics.last_trip_time else None),
                'last_recovery': (self.metrics.last_recovery_time.isoformat()
                                if self.metrics.last_recovery_time else None)
            }

    async def force_open(self):
        """Force circuit breaker to open state (manual intervention)."""
        logger.warning(f"Force opening circuit breaker '{self.name}'")
        with self._lock:
            self._transition_to_open()
        await self._execute_trip_callbacks()

    async def force_close(self):
        """Force circuit breaker to closed state (manual intervention)."""
        logger.info(f"Force closing circuit breaker '{self.name}'")
        with self._lock:
            self._transition_to_closed()
        await self._execute_recovery_callbacks()

    def reset(self):
        """Reset circuit breaker to initial state, clearing all history."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.state_changed_time = datetime.now()
            self.metrics = CircuitBreakerMetrics()
            self.request_history.clear()
            self.recent_failures.clear()
            self.recent_successes = 0
            self.backoff_count = 0
            self.current_backoff = self.config.open_timeout_seconds

        logger.info(f"Circuit breaker '{self.name}' reset to initial state")

    @property
    def is_open(self) -> bool:
        """Check if circuit is currently open (blocking requests)."""
        return self.state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is currently closed (allowing requests)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is currently half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers in a trading system.

    Provides centralized creation, monitoring, and coordination of
    circuit breakers across the application.

    Example:
        manager = CircuitBreakerManager()

        # Create breakers
        api_breaker = manager.create_circuit_breaker("broker_api", CircuitType.CONNECTION_FAILURE)
        loss_breaker = manager.create_circuit_breaker("daily_loss", CircuitType.DAILY_LOSS)

        # Get system-wide status
        status = manager.get_system_status()
        print(f"Open breakers: {status['open_breakers']}")
    """

    def __init__(self):
        """Initialize circuit breaker manager."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()

        logger.info("Circuit Breaker Manager initialized")

    def create_circuit_breaker(
        self,
        name: str,
        circuit_type: CircuitType,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Create and register a new circuit breaker.

        Args:
            name: Unique name for the breaker
            circuit_type: Type of circuit breaker
            config: Optional configuration

        Returns:
            The created CircuitBreaker instance

        Raises:
            ValueError: If a breaker with this name already exists
        """
        with self._lock:
            if name in self.circuit_breakers:
                raise ValueError(f"Circuit breaker '{name}' already exists")

            circuit_breaker = CircuitBreaker(name, circuit_type, config)
            self.circuit_breakers[name] = circuit_breaker

            logger.info(f"Created circuit breaker: {name} ({circuit_type.value})")
            return circuit_breaker

    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        with self._lock:
            return self.circuit_breakers.get(name)

    def remove_circuit_breaker(self, name: str) -> bool:
        """Remove a circuit breaker by name."""
        with self._lock:
            if name in self.circuit_breakers:
                del self.circuit_breakers[name]
                logger.info(f"Removed circuit breaker: {name}")
                return True
            return False

    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers."""
        with self._lock:
            circuit_statuses = {}

            for name, circuit in self.circuit_breakers.items():
                circuit_statuses[name] = circuit.get_status()

            # Calculate system-wide metrics
            total_breakers = len(self.circuit_breakers)
            open_breakers = sum(1 for cb in self.circuit_breakers.values()
                              if cb.state == CircuitState.OPEN)
            half_open_breakers = sum(1 for cb in self.circuit_breakers.values()
                                   if cb.state == CircuitState.HALF_OPEN)

            return {
                'total_circuit_breakers': total_breakers,
                'open_breakers': open_breakers,
                'half_open_breakers': half_open_breakers,
                'closed_breakers': total_breakers - open_breakers - half_open_breakers,
                'circuit_breakers': circuit_statuses
            }

    def get_open_breakers(self) -> List[str]:
        """Get list of names of currently open circuit breakers."""
        with self._lock:
            return [
                name for name, cb in self.circuit_breakers.items()
                if cb.state == CircuitState.OPEN
            ]

    def any_open(self) -> bool:
        """Check if any circuit breakers are currently open."""
        with self._lock:
            return any(cb.state == CircuitState.OPEN for cb in self.circuit_breakers.values())

    async def shutdown_all(self):
        """Shutdown all circuit breakers gracefully."""
        logger.info("Shutting down all circuit breakers")

        with self._lock:
            # Force all circuits to closed state for graceful shutdown
            for circuit in self.circuit_breakers.values():
                await circuit.force_close()

        logger.info("All circuit breakers shut down")

    def reset_all(self):
        """Reset all circuit breakers to initial state."""
        with self._lock:
            for circuit in self.circuit_breakers.values():
                circuit.reset()

        logger.info("All circuit breakers reset")
