# Backtest Harness

A generalized, domain-agnostic backtesting framework extracted from the Trader AI project.

## Features

- **Walk-Forward Validation**: Proper time-series cross-validation with expanding or rolling windows
- **No Lookahead Bias**: Strict separation between training and test periods
- **Realistic Cost Modeling**: Slippage, commissions, spread, and execution delay
- **Comprehensive Metrics**: Sharpe, Sortino, Calmar, max drawdown, profit factor, win rate
- **Trade Logging**: Full trade log with entry/exit prices, P&L, and exit reasons
- **Equity Curve Tracking**: Track portfolio value over time
- **Pluggable Strategy Interface**: Use Protocol classes for type-safe strategy implementations
- **Decimal Precision**: Uses Python Decimal for financial calculations

## Installation

Copy the `backtest-harness` directory to your project or add to Python path.

```python
import sys
sys.path.insert(0, "path/to/backtest-harness")
```

## Dependencies

- Python 3.9+
- numpy

## Quick Start

### Basic Usage with Strategy Class

```python
from decimal import Decimal
from backtest_harness import (
    BacktestEngine,
    BacktestConfig,
    CostModel,
    WindowType,
    Strategy,
)
import numpy as np

# Define a simple moving average crossover strategy
class MACrossStrategy:
    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        self.fast_period = fast_period
        self.slow_period = slow_period

    def fit(self, data: np.ndarray) -> None:
        # No fitting needed for simple MA strategy
        pass

    def predict(self, data: np.ndarray) -> list:
        close = data[:, 3]  # Close prices
        signals = []

        for i in range(len(close)):
            if i < self.slow_period:
                signals.append(0)
                continue

            fast_ma = np.mean(close[i - self.fast_period + 1:i + 1])
            slow_ma = np.mean(close[i - self.slow_period + 1:i + 1])

            if fast_ma > slow_ma:
                signals.append(1)   # Long
            elif fast_ma < slow_ma:
                signals.append(-1)  # Short
            else:
                signals.append(0)

        return signals

# Create configuration
config = BacktestConfig(
    train_window=252,           # 1 year training
    test_window=63,             # 3 months testing
    window_type=WindowType.ROLLING,
    initial_capital=Decimal("10000"),
    max_position_pct=Decimal("0.20"),
    cost_model=CostModel(
        slippage_bps=Decimal("5"),
        commission_bps=Decimal("10"),
    ),
)

# Generate sample OHLCV data
np.random.seed(42)
n_bars = 500
prices = np.column_stack([
    100 + np.cumsum(np.random.randn(n_bars) * 0.5),  # Open
    None,  # High (filled below)
    None,  # Low (filled below)
    None,  # Close (filled below)
    np.random.randint(1000000, 5000000, n_bars),     # Volume
])
prices[:, 1] = prices[:, 0] + np.abs(np.random.randn(n_bars) * 0.5)  # High
prices[:, 2] = prices[:, 0] - np.abs(np.random.randn(n_bars) * 0.5)  # Low
prices[:, 3] = prices[:, 0] + np.random.randn(n_bars) * 0.3          # Close

# Run backtest
engine = BacktestEngine(config)
strategy = MACrossStrategy(fast_period=10, slow_period=30)
results = engine.run_walk_forward(strategy, prices)

# Print results
print("Backtest Results:")
print(f"  Total Return: {float(results.total_return * 100):.2f}%")
print(f"  Sharpe Ratio: {results.sharpe_ratio:.2f}")
print(f"  Max Drawdown: {float(results.max_drawdown * 100):.2f}%")
print(f"  Win Rate: {float(results.win_rate * 100):.1f}%")
print(f"  Total Trades: {results.total_trades}")
```

### Using Signal Functions

For simpler strategies, you can use a signal function instead of a full class:

```python
from backtest_harness import BacktestEngine, BacktestConfig

def simple_momentum_signal(data: np.ndarray, idx: int):
    """
    Simple momentum signal: buy if up 3 days in a row.

    Args:
        data: Historical OHLCV data up to idx
        idx: Current bar index

    Returns:
        (signal, metadata) tuple
    """
    if idx < 3:
        return 0, {}

    close = data[:, 3]
    returns = np.diff(close[-4:])

    if all(r > 0 for r in returns):
        return 1, {"reason": "3-day up streak"}
    elif all(r < 0 for r in returns):
        return -1, {"reason": "3-day down streak"}
    else:
        return 0, {}

# Run backtest with signal function
engine = BacktestEngine()
results = engine.run_signal_backtest(simple_momentum_signal, prices)
```

### Slippage Sensitivity Analysis

Test how your strategy performs under different slippage assumptions:

```python
from backtest_harness import BacktestEngine, run_slippage_sensitivity

engine = BacktestEngine()
sensitivity = run_slippage_sensitivity(
    engine,
    simple_momentum_signal,
    prices,
    slippage_range=[0, 5, 10, 20, 50],  # basis points
)

for slippage, result in sensitivity.items():
    print(f"Slippage {slippage}bps: Sharpe={result.sharpe_ratio:.2f}")
```

## Configuration Options

### BacktestConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `train_window` | int | 252 | Training window in bars |
| `test_window` | int | 63 | Test window in bars |
| `window_type` | WindowType | EXPANDING | EXPANDING or ROLLING |
| `min_train_size` | int | 126 | Minimum training samples |
| `initial_capital` | Decimal | 10000 | Starting capital |
| `max_position_pct` | Decimal | 0.20 | Max position as % of capital |
| `risk_per_trade_pct` | Decimal | 0.02 | Risk per trade as % of capital |
| `atr_stop_mult` | Decimal | 2.0 | ATR multiplier for stop loss |
| `atr_target_mult` | Decimal | 3.0 | ATR multiplier for take profit |
| `max_holding_bars` | int | 20 | Maximum holding period |
| `require_min_trades` | int | 10 | Min trades for valid fold |
| `bars_per_year` | int | 252 | For annualization |

### CostModel

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `slippage_bps` | Decimal | 5.0 | Market impact slippage |
| `commission_bps` | Decimal | 10.0 | Trading commission |
| `spread_bps` | Decimal | 2.0 | Bid-ask spread |
| `delay_bars` | int | 1 | Execution delay |
| `funding_rate_daily_bps` | Decimal | 0.0 | Daily funding rate |

## Results Structure

### BacktestResults

```python
results.total_return        # Decimal: Total return
results.annualized_return   # Decimal: Annualized return
results.sharpe_ratio        # float: Sharpe ratio
results.sortino_ratio       # float: Sortino ratio
results.max_drawdown        # Decimal: Maximum drawdown
results.calmar_ratio        # float: Calmar ratio
results.win_rate            # Decimal: Win rate
results.profit_factor       # Decimal: Profit factor
results.total_trades        # int: Total trades
results.all_trades          # List[Trade]: Full trade log
results.equity_curve        # List[Decimal]: Equity curve
results.folds               # List[FoldResult]: Per-fold results

# Get summary dictionary
results.summary()

# Get trade log as list of dicts
results.get_trade_log()
```

### Trade

```python
trade.trade_id       # Unique ID
trade.entry_time     # Entry timestamp
trade.exit_time      # Exit timestamp
trade.symbol         # Symbol
trade.direction      # 'long' or 'short'
trade.entry_price    # Entry price (Decimal)
trade.exit_price     # Exit price (Decimal)
trade.quantity       # Position size (Decimal)
trade.pnl            # Net P&L (Decimal)
trade.pnl_pct        # P&L percentage (Decimal)
trade.holding_bars   # Holding period
trade.exit_reason    # 'target', 'stop', 'timeout', 'signal'
trade.slippage_cost  # Slippage cost (Decimal)
trade.commission_cost # Commission cost (Decimal)
```

## Performance Metrics

The `PerformanceCalculator` class provides standalone metric calculations:

```python
from backtest_harness import PerformanceCalculator
import numpy as np

returns = np.array([0.01, -0.005, 0.02, -0.01, 0.015])
equity = np.array([10000, 10100, 10050, 10250, 10150, 10300])

sharpe = PerformanceCalculator.sharpe_ratio(returns)
sortino = PerformanceCalculator.sortino_ratio(returns)
max_dd = PerformanceCalculator.max_drawdown(equity)
calmar = PerformanceCalculator.calmar_ratio(returns, equity)
```

## Best Practices

1. **Use Walk-Forward Validation**: Always use walk-forward to avoid overfitting
2. **Include Realistic Costs**: Set slippage and commission to realistic values
3. **Test Multiple Slippage Levels**: Use `run_slippage_sensitivity()` to ensure robustness
4. **Check Fold Consistency**: Look at `fold_sharpe_std` and `pct_profitable_folds`
5. **Use Decimal for Money**: The library uses Decimal for financial precision

## License

MIT License
