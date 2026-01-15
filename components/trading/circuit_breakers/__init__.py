"""
Circuit Breakers Library Component - Financial Protection Mechanisms

This library provides production-ready circuit breaker implementations
for trading systems and financial applications.

Features:
- Generic circuit breaker with standard CLOSED/OPEN/HALF_OPEN states
- Trading-specific breakers for P&L protection
- 6 specialized breaker types for comprehensive coverage
- Thread-safe state management
- Event callbacks for monitoring and alerting
- Decimal precision for financial calculations

Quick Start:
    # Basic circuit breaker for API protection
    from circuit_breakers import CircuitBreaker, CircuitType

    breaker = CircuitBreaker("broker_api", CircuitType.CONNECTION_FAILURE)
    result = await breaker.call(broker.get_positions)

    # Trading circuit breakers for P&L protection
    from circuit_breakers import TradingCircuitBreakers, TradingBreakerConfig

    config = TradingBreakerConfig(
        daily_loss_limit_pct=Decimal("-2.0"),
        max_drawdown_pct=Decimal("-10.0")
    )
    breakers = TradingCircuitBreakers(portfolio, config)
    await breakers.start_monitoring()

    if breakers.can_trade():
        execute_order(order)

Extracted from Trader AI project (D:\\Projects\\trader-ai).
"""

from .circuit_breaker import (
    # Core classes
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitBreakerConfig,
    CircuitBreakerMetrics,

    # Enums
    CircuitState,
    CircuitType,

    # Data classes
    RequestResult,

    # Exceptions
    CircuitOpenException,
)

from .trading_breakers import (
    # Trading-specific classes
    TradingCircuitBreakers,
    TradingBreakerConfig,
    TradingBreakerStatus,
    TradingBreakerType,

    # Protocol for portfolio integration
    PortfolioProvider,
)

__all__ = [
    # Core Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerManager",
    "CircuitBreakerConfig",
    "CircuitBreakerMetrics",
    "CircuitState",
    "CircuitType",
    "RequestResult",
    "CircuitOpenException",

    # Trading Circuit Breakers
    "TradingCircuitBreakers",
    "TradingBreakerConfig",
    "TradingBreakerStatus",
    "TradingBreakerType",
    "PortfolioProvider",
]

__version__ = "1.0.0"
__author__ = "David Youssef"
__source__ = "Extracted from trader-ai"
