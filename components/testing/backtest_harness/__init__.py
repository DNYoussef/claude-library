"""
Backtest Harness - Generalized Backtesting Framework

A domain-agnostic backtesting library providing:
- Walk-forward cross-validation
- Realistic cost modeling
- Comprehensive performance metrics
- Pluggable strategy interface

Example usage:
    from backtest_harness import (
        BacktestEngine,
        BacktestConfig,
        CostModel,
        WindowType,
    )

    # Create config
    config = BacktestConfig(
        train_window=252,
        test_window=63,
        window_type=WindowType.EXPANDING,
        initial_capital=Decimal("10000"),
    )

    # Run backtest
    engine = BacktestEngine(config)
    results = engine.run_walk_forward(strategy, prices)

    # Get summary
    print(results.summary())
"""

# Support both package import and direct import
try:
    from .backtest import (
        # Configuration
        BacktestConfig,
        CostModel,
        WindowType,
        # Engine
        BacktestEngine,
        # Results
        BacktestResults,
        FoldResult,
        Trade,
        # Protocols
        Strategy,
        SignalFunction,
        # Utilities
        PerformanceCalculator,
        run_slippage_sensitivity,
    )
except ImportError:
    from backtest import (
        # Configuration
        BacktestConfig,
        CostModel,
        WindowType,
        # Engine
        BacktestEngine,
        # Results
        BacktestResults,
        FoldResult,
        Trade,
        # Protocols
        Strategy,
        SignalFunction,
        # Utilities
        PerformanceCalculator,
        run_slippage_sensitivity,
    )

__all__ = [
    # Configuration
    "BacktestConfig",
    "CostModel",
    "WindowType",
    # Engine
    "BacktestEngine",
    # Results
    "BacktestResults",
    "FoldResult",
    "Trade",
    # Protocols
    "Strategy",
    "SignalFunction",
    # Utilities
    "PerformanceCalculator",
    "run_slippage_sensitivity",
]

__version__ = "1.0.0"
