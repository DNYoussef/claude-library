"""
Generalized Backtesting Harness

A domain-agnostic backtesting framework extracted from Trader AI, providing:
- Walk-forward cross-validation with expanding/rolling windows
- Realistic cost modeling (slippage, fees, spread)
- Comprehensive performance metrics (Sharpe, Sortino, Calmar, max drawdown)
- Trade log generation and equity curve tracking
- Pluggable strategy interface

Uses Decimal from money-handling patterns for financial precision.

Author: Library extraction from Trader AI
License: MIT
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
)

import numpy as np

logger = logging.getLogger(__name__)

# Type variable for generic price/return types
T = TypeVar("T")


class WindowType(Enum):
    """Type of training window for walk-forward validation."""
    EXPANDING = "expanding"  # Train on all historical data
    ROLLING = "rolling"      # Train on fixed-size window


@dataclass
class CostModel:
    """
    Realistic transaction cost modeling.

    All values in basis points (bps) unless otherwise noted.
    1 bps = 0.01% = 0.0001
    """
    slippage_bps: Decimal = Decimal("5.0")      # Market impact slippage
    commission_bps: Decimal = Decimal("10.0")   # Trading commission
    spread_bps: Decimal = Decimal("2.0")        # Bid-ask spread
    delay_bars: int = 1                          # Execution delay in bars
    funding_rate_daily_bps: Decimal = Decimal("0.0")  # Daily funding rate

    @property
    def total_cost_bps(self) -> Decimal:
        """Total round-trip cost in basis points."""
        return self.slippage_bps + self.commission_bps + self.spread_bps

    def apply_slippage(self, price: Decimal, direction: str) -> Decimal:
        """
        Apply slippage to a price based on trade direction.

        Args:
            price: Base price
            direction: 'buy' or 'sell'

        Returns:
            Price adjusted for slippage
        """
        slippage_factor = self.slippage_bps / Decimal("10000")
        if direction == "buy":
            return price * (Decimal("1") + slippage_factor)
        else:  # sell
            return price * (Decimal("1") - slippage_factor)

    def calculate_commission(self, notional: Decimal) -> Decimal:
        """Calculate commission for a trade."""
        return notional * (self.commission_bps / Decimal("10000"))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "slippage_bps": float(self.slippage_bps),
            "commission_bps": float(self.commission_bps),
            "spread_bps": float(self.spread_bps),
            "delay_bars": self.delay_bars,
            "funding_rate_daily_bps": float(self.funding_rate_daily_bps),
            "total_cost_bps": float(self.total_cost_bps),
        }


@dataclass
class BacktestConfig:
    """Configuration for walk-forward backtesting."""

    # Window settings
    train_window: int = 252        # Training window in bars (1 year of daily)
    test_window: int = 63          # Test window in bars (3 months)
    window_type: WindowType = WindowType.EXPANDING
    min_train_size: int = 126      # Minimum training samples (6 months)

    # Cost model
    cost_model: CostModel = field(default_factory=CostModel)

    # Position sizing
    initial_capital: Decimal = Decimal("10000.0")
    max_position_pct: Decimal = Decimal("0.20")  # Max 20% per position
    risk_per_trade_pct: Decimal = Decimal("0.02")  # 2% risk per trade

    # Risk management
    atr_stop_mult: Decimal = Decimal("2.0")     # ATR multiplier for stop loss
    atr_target_mult: Decimal = Decimal("3.0")   # ATR multiplier for take profit
    max_holding_bars: int = 20                   # Maximum holding period

    # Validation
    require_min_trades: int = 10   # Minimum trades for valid fold

    # Annualization
    bars_per_year: int = 252       # Trading days per year


@dataclass
class Trade:
    """Record of a single executed trade."""
    trade_id: int
    entry_time: datetime
    exit_time: datetime
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    pnl: Decimal
    pnl_pct: Decimal
    holding_bars: int
    exit_reason: str  # 'target', 'stop', 'timeout', 'signal'
    slippage_cost: Decimal
    commission_cost: Decimal

    @property
    def gross_pnl(self) -> Decimal:
        """PnL before costs."""
        return self.pnl + self.slippage_cost + self.commission_cost

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "trade_id": self.trade_id,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": float(self.entry_price),
            "exit_price": float(self.exit_price),
            "quantity": float(self.quantity),
            "pnl": float(self.pnl),
            "pnl_pct": float(self.pnl_pct),
            "holding_bars": self.holding_bars,
            "exit_reason": self.exit_reason,
            "slippage_cost": float(self.slippage_cost),
            "commission_cost": float(self.commission_cost),
        }


@dataclass
class FoldResult:
    """Result of a single walk-forward fold."""
    fold_id: int
    train_start: Optional[datetime]
    train_end: Optional[datetime]
    test_start: Optional[datetime]
    test_end: Optional[datetime]
    trades: List[Trade] = field(default_factory=list)

    # Metrics
    total_return: Decimal = Decimal("0.0")
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: Decimal = Decimal("0.0")
    win_rate: Decimal = Decimal("0.0")
    profit_factor: Decimal = Decimal("0.0")
    avg_trade_pnl: Decimal = Decimal("0.0")
    num_trades: int = 0

    # Equity curve
    equity_curve: List[Decimal] = field(default_factory=list)


@dataclass
class BacktestResults:
    """Aggregated walk-forward backtest results."""
    config: BacktestConfig
    folds: List[FoldResult] = field(default_factory=list)

    # Aggregated metrics
    total_return: Decimal = Decimal("0.0")
    annualized_return: Decimal = Decimal("0.0")
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: Decimal = Decimal("0.0")
    calmar_ratio: float = 0.0
    win_rate: Decimal = Decimal("0.0")
    profit_factor: Decimal = Decimal("0.0")
    total_trades: int = 0

    # Robustness metrics
    fold_sharpe_std: float = 0.0
    pct_profitable_folds: Decimal = Decimal("0.0")
    worst_fold_return: Decimal = Decimal("0.0")
    best_fold_return: Decimal = Decimal("0.0")

    # Full trade log
    all_trades: List[Trade] = field(default_factory=list)

    # Aggregated equity curve
    equity_curve: List[Decimal] = field(default_factory=list)

    def get_trade_log(self) -> List[Dict[str, Any]]:
        """Get trade log as list of dictionaries."""
        return [t.to_dict() for t in self.all_trades]

    def summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            "total_return_pct": float(self.total_return * 100),
            "annualized_return_pct": float(self.annualized_return * 100),
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown_pct": float(self.max_drawdown * 100),
            "calmar_ratio": self.calmar_ratio,
            "win_rate_pct": float(self.win_rate * 100),
            "profit_factor": float(self.profit_factor),
            "total_trades": self.total_trades,
            "num_folds": len(self.folds),
            "pct_profitable_folds": float(self.pct_profitable_folds * 100),
        }


class Strategy(Protocol):
    """
    Protocol for pluggable trading strategies.

    Implement this interface to create custom strategies.
    """

    def fit(self, data: Any) -> None:
        """
        Fit the strategy on training data.

        Args:
            data: Training data (format depends on implementation)
        """
        ...

    def predict(self, data: Any) -> List[int]:
        """
        Generate signals for the given data.

        Args:
            data: Data to generate signals for

        Returns:
            List of signals: +1 (long), -1 (short), 0 (no position)
        """
        ...


class SignalFunction(Protocol):
    """
    Protocol for signal generation functions.

    Simpler alternative to full Strategy class.
    """

    def __call__(self, data: Any, idx: int) -> Tuple[int, Dict[str, Any]]:
        """
        Generate a signal at the given index.

        Args:
            data: Historical data up to and including idx
            idx: Current bar index

        Returns:
            Tuple of (signal, metadata) where signal is +1/-1/0
        """
        ...


class PerformanceCalculator:
    """Calculate performance metrics from returns and equity curves."""

    @staticmethod
    def sharpe_ratio(
        returns: np.ndarray,
        risk_free_rate: float = 0.0,
        annualization: int = 252,
    ) -> float:
        """
        Calculate annualized Sharpe ratio.

        Args:
            returns: Array of periodic returns
            risk_free_rate: Annual risk-free rate
            annualization: Periods per year

        Returns:
            Annualized Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0

        daily_rf = risk_free_rate / annualization
        excess_returns = returns - daily_rf

        mean_excess = np.mean(excess_returns)
        std_returns = np.std(returns, ddof=1)

        if std_returns == 0:
            return 0.0

        return float(np.sqrt(annualization) * mean_excess / std_returns)

    @staticmethod
    def sortino_ratio(
        returns: np.ndarray,
        risk_free_rate: float = 0.0,
        annualization: int = 252,
    ) -> float:
        """
        Calculate Sortino ratio (downside risk only).

        Args:
            returns: Array of periodic returns
            risk_free_rate: Annual risk-free rate
            annualization: Periods per year

        Returns:
            Annualized Sortino ratio
        """
        if len(returns) < 2:
            return 0.0

        daily_rf = risk_free_rate / annualization
        excess_returns = returns - daily_rf

        mean_excess = np.mean(excess_returns)
        downside_returns = returns[returns < 0]

        if len(downside_returns) < 2:
            return float("inf") if mean_excess > 0 else 0.0

        downside_std = np.std(downside_returns, ddof=1)

        if downside_std == 0:
            return float("inf") if mean_excess > 0 else 0.0

        return float(np.sqrt(annualization) * mean_excess / downside_std)

    @staticmethod
    def max_drawdown(equity_curve: np.ndarray) -> float:
        """
        Calculate maximum drawdown.

        Args:
            equity_curve: Array of equity values

        Returns:
            Maximum drawdown as positive decimal (0.10 = 10%)
        """
        if len(equity_curve) < 2:
            return 0.0

        running_max = np.maximum.accumulate(equity_curve)
        drawdowns = (equity_curve - running_max) / running_max
        return float(abs(np.min(drawdowns)))

    @staticmethod
    def calmar_ratio(
        returns: np.ndarray,
        equity_curve: np.ndarray,
        annualization: int = 252,
    ) -> float:
        """
        Calculate Calmar ratio (annualized return / max drawdown).

        Args:
            returns: Array of periodic returns
            equity_curve: Array of equity values
            annualization: Periods per year

        Returns:
            Calmar ratio
        """
        if len(returns) < 2:
            return 0.0

        total_return = np.sum(returns)
        n_years = len(returns) / annualization
        ann_return = total_return / n_years if n_years > 0 else 0.0

        max_dd = PerformanceCalculator.max_drawdown(equity_curve)

        if max_dd == 0:
            return float("inf") if ann_return > 0 else 0.0

        return float(ann_return / max_dd)

    @staticmethod
    def profit_factor(pnls: List[Decimal]) -> Decimal:
        """
        Calculate profit factor (gross profit / gross loss).

        Args:
            pnls: List of trade P&Ls

        Returns:
            Profit factor (>1 is profitable)
        """
        if not pnls:
            return Decimal("0.0")

        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))

        if gross_loss == 0:
            return Decimal("inf") if gross_profit > 0 else Decimal("0.0")

        return gross_profit / gross_loss

    @staticmethod
    def win_rate(pnls: List[Decimal]) -> Decimal:
        """
        Calculate win rate.

        Args:
            pnls: List of trade P&Ls

        Returns:
            Win rate as decimal (0.55 = 55%)
        """
        if not pnls:
            return Decimal("0.0")

        wins = len([p for p in pnls if p > 0])
        return Decimal(wins) / Decimal(len(pnls))


class BacktestEngine:
    """
    Walk-forward backtesting engine for trading strategies.

    Implements proper time-series validation with:
    - No lookahead bias
    - Expanding or rolling training windows
    - Realistic cost modeling
    - Comprehensive performance metrics
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize backtest engine.

        Args:
            config: Backtest configuration (uses defaults if None)
        """
        self.config = config or BacktestConfig()
        self._trade_id_counter = 0

        logger.info(
            f"BacktestEngine initialized: {self.config.window_type.value} window, "
            f"train={self.config.train_window}, test={self.config.test_window}"
        )

    def _next_trade_id(self) -> int:
        """Generate unique trade ID."""
        self._trade_id_counter += 1
        return self._trade_id_counter

    def run_walk_forward(
        self,
        strategy: Strategy,
        prices: np.ndarray,
        timestamps: Optional[List[datetime]] = None,
        symbol: str = "TEST",
    ) -> BacktestResults:
        """
        Run walk-forward validation on a strategy.

        Args:
            strategy: Strategy object implementing fit() and predict()
            prices: OHLCV numpy array with columns [open, high, low, close, volume]
            timestamps: Optional list of timestamps for each bar
            symbol: Symbol name for trade logging

        Returns:
            BacktestResults with all folds and metrics
        """
        self._validate_prices(prices)

        folds = []
        fold_id = 0

        total_bars = len(prices)
        start_idx = self.config.min_train_size

        while start_idx + self.config.test_window <= total_bars:
            # Determine training range
            if self.config.window_type == WindowType.EXPANDING:
                train_start_idx = 0
            else:  # ROLLING
                train_start_idx = max(0, start_idx - self.config.train_window)

            train_end_idx = start_idx
            test_start_idx = start_idx
            test_end_idx = min(start_idx + self.config.test_window, total_bars)

            # Split data
            train_data = prices[train_start_idx:train_end_idx]
            test_data = prices[test_start_idx:test_end_idx]

            # Get timestamps for this fold
            train_timestamps = (
                timestamps[train_start_idx:train_end_idx] if timestamps else None
            )
            test_timestamps = (
                timestamps[test_start_idx:test_end_idx] if timestamps else None
            )

            # Fit strategy on training data
            strategy.fit(train_data)

            # Generate predictions on test data
            signals = strategy.predict(test_data)

            # Execute trades based on signals
            trades = self._execute_trades(
                test_data, signals, test_timestamps, symbol
            )

            # Calculate fold metrics
            fold_result = self._calculate_fold_metrics(
                fold_id=fold_id,
                train_timestamps=train_timestamps,
                test_timestamps=test_timestamps,
                trades=trades,
            )
            folds.append(fold_result)

            fold_id += 1
            start_idx += self.config.test_window

        # Aggregate results
        results = self._aggregate_results(folds)

        logger.info(
            f"Walk-forward complete: {len(folds)} folds, "
            f"Sharpe={results.sharpe_ratio:.2f}, "
            f"Total Return={float(results.total_return * 100):.1f}%"
        )

        return results

    def run_signal_backtest(
        self,
        signal_fn: SignalFunction,
        prices: np.ndarray,
        timestamps: Optional[List[datetime]] = None,
        symbol: str = "TEST",
    ) -> BacktestResults:
        """
        Backtest a signal generation function.

        Args:
            signal_fn: Function(data, idx) -> (signal, metadata)
            prices: OHLCV numpy array
            timestamps: Optional timestamps
            symbol: Symbol name

        Returns:
            BacktestResults with validation
        """
        self._validate_prices(prices)

        folds = []
        fold_id = 0

        total_bars = len(prices)
        start_idx = self.config.min_train_size

        while start_idx + self.config.test_window <= total_bars:
            test_start_idx = start_idx
            test_end_idx = min(start_idx + self.config.test_window, total_bars)

            test_data = prices[test_start_idx:test_end_idx]
            test_timestamps = (
                timestamps[test_start_idx:test_end_idx] if timestamps else None
            )

            # Generate signals for test period
            signals = []
            for i in range(len(test_data)):
                global_idx = test_start_idx + i
                # Only pass data up to current bar (no lookahead)
                historical_data = prices[:global_idx + 1]
                signal, _ = signal_fn(historical_data, len(historical_data) - 1)
                signals.append(signal)

            # Execute trades
            trades = self._execute_trades(
                test_data, signals, test_timestamps, symbol
            )

            # Calculate fold metrics
            train_timestamps = timestamps[:test_start_idx] if timestamps else None

            fold_result = self._calculate_fold_metrics(
                fold_id=fold_id,
                train_timestamps=train_timestamps,
                test_timestamps=test_timestamps,
                trades=trades,
            )
            folds.append(fold_result)

            fold_id += 1
            start_idx += self.config.test_window

        # Aggregate results
        results = self._aggregate_results(folds)

        return results

    def _validate_prices(self, prices: np.ndarray) -> None:
        """Validate price data format."""
        if prices.ndim != 2 or prices.shape[1] < 4:
            raise ValueError(
                f"prices must be 2D array with at least 4 columns (OHLC), "
                f"got shape {prices.shape}"
            )

        min_required = self.config.min_train_size + self.config.test_window
        if len(prices) < min_required:
            raise ValueError(
                f"Insufficient data: {len(prices)} bars, need at least {min_required}"
            )

    def _calculate_atr(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Average True Range."""
        high = prices[:, 1]
        low = prices[:, 2]
        close = prices[:, 3]

        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))

        tr2[0] = tr1[0]
        tr3[0] = tr1[0]

        true_range = np.maximum(np.maximum(tr1, tr2), tr3)

        # Simple moving average of TR
        atr = np.zeros_like(true_range)
        for i in range(len(true_range)):
            start = max(0, i - period + 1)
            atr[i] = np.mean(true_range[start:i + 1])

        return atr

    def _execute_trades(
        self,
        prices: np.ndarray,
        signals: List[int],
        timestamps: Optional[List[datetime]],
        symbol: str,
    ) -> List[Trade]:
        """
        Execute trades based on signals with realistic cost modeling.

        Args:
            prices: OHLCV array for test period
            signals: List of signals (+1 long, -1 short, 0 flat)
            timestamps: Optional timestamps
            symbol: Symbol name

        Returns:
            List of Trade objects
        """
        trades = []
        position = None

        atr = self._calculate_atr(prices)

        for i in range(len(prices)):
            signal = signals[i] if i < len(signals) else 0
            current_price = Decimal(str(prices[i, 3]))  # close
            current_high = Decimal(str(prices[i, 1]))
            current_low = Decimal(str(prices[i, 2]))
            current_atr = Decimal(str(atr[i]))

            timestamp = timestamps[i] if timestamps else datetime.now()

            # Check for exit conditions if in position
            if position is not None:
                exit_reason = None
                exit_price = current_price

                if position["direction"] == "long":
                    # Check stop loss
                    if current_low <= position["stop_price"]:
                        exit_reason = "stop"
                        exit_price = position["stop_price"]
                    # Check take profit
                    elif current_high >= position["target_price"]:
                        exit_reason = "target"
                        exit_price = position["target_price"]
                    # Check timeout
                    elif position["holding_bars"] >= self.config.max_holding_bars:
                        exit_reason = "timeout"
                    # Check signal reversal
                    elif signal == -1:
                        exit_reason = "signal"
                else:  # short
                    if current_high >= position["stop_price"]:
                        exit_reason = "stop"
                        exit_price = position["stop_price"]
                    elif current_low <= position["target_price"]:
                        exit_reason = "target"
                        exit_price = position["target_price"]
                    elif position["holding_bars"] >= self.config.max_holding_bars:
                        exit_reason = "timeout"
                    elif signal == 1:
                        exit_reason = "signal"

                if exit_reason:
                    # Apply slippage
                    exit_direction = "sell" if position["direction"] == "long" else "buy"
                    exit_price = self.config.cost_model.apply_slippage(
                        exit_price, exit_direction
                    )

                    # Calculate P&L
                    if position["direction"] == "long":
                        pnl = (exit_price - position["entry_price"]) * position["quantity"]
                        pnl_pct = (exit_price - position["entry_price"]) / position["entry_price"]
                    else:
                        pnl = (position["entry_price"] - exit_price) * position["quantity"]
                        pnl_pct = (position["entry_price"] - exit_price) / position["entry_price"]

                    slippage_cost = self.config.cost_model.apply_slippage(
                        current_price, "buy"
                    ) - current_price
                    slippage_cost = abs(slippage_cost) * position["quantity"] * 2

                    commission_cost = self.config.cost_model.calculate_commission(
                        position["entry_price"] * position["quantity"]
                    ) * 2

                    trades.append(Trade(
                        trade_id=self._next_trade_id(),
                        entry_time=position["entry_time"],
                        exit_time=timestamp,
                        symbol=symbol,
                        direction=position["direction"],
                        entry_price=position["entry_price"],
                        exit_price=exit_price,
                        quantity=position["quantity"],
                        pnl=pnl - commission_cost,
                        pnl_pct=pnl_pct,
                        holding_bars=position["holding_bars"],
                        exit_reason=exit_reason,
                        slippage_cost=slippage_cost,
                        commission_cost=commission_cost,
                    ))
                    position = None
                else:
                    position["holding_bars"] += 1

            # Check for entry if not in position
            if position is None and signal != 0:
                entry_price = current_price
                entry_direction = "buy" if signal == 1 else "sell"
                entry_price = self.config.cost_model.apply_slippage(
                    entry_price, entry_direction
                )

                if signal == 1:  # Long
                    stop_price = entry_price - (current_atr * self.config.atr_stop_mult)
                    target_price = entry_price + (current_atr * self.config.atr_target_mult)
                    direction = "long"
                else:  # Short
                    stop_price = entry_price + (current_atr * self.config.atr_stop_mult)
                    target_price = entry_price - (current_atr * self.config.atr_target_mult)
                    direction = "short"

                # Calculate position size
                risk_per_share = abs(entry_price - stop_price)
                max_position_value = self.config.initial_capital * self.config.max_position_pct
                risk_capital = self.config.initial_capital * self.config.risk_per_trade_pct

                quantity = min(
                    max_position_value / entry_price,
                    risk_capital / risk_per_share if risk_per_share > 0 else Decimal("0"),
                )

                if quantity > 0:
                    position = {
                        "entry_time": timestamp,
                        "entry_price": entry_price,
                        "direction": direction,
                        "quantity": quantity,
                        "stop_price": stop_price,
                        "target_price": target_price,
                        "holding_bars": 0,
                    }

        return trades

    def _calculate_fold_metrics(
        self,
        fold_id: int,
        train_timestamps: Optional[List[datetime]],
        test_timestamps: Optional[List[datetime]],
        trades: List[Trade],
    ) -> FoldResult:
        """Calculate metrics for a single fold."""
        result = FoldResult(
            fold_id=fold_id,
            train_start=train_timestamps[0] if train_timestamps else None,
            train_end=train_timestamps[-1] if train_timestamps else None,
            test_start=test_timestamps[0] if test_timestamps else None,
            test_end=test_timestamps[-1] if test_timestamps else None,
            trades=trades,
            num_trades=len(trades),
        )

        if not trades:
            return result

        # Calculate returns
        pnls = [t.pnl for t in trades]
        pnl_pcts = [float(t.pnl_pct) for t in trades]

        # Guard against division by zero
        if self.config.initial_capital > 0:
            result.total_return = sum(pnls) / self.config.initial_capital
        else:
            result.total_return = Decimal("0")
            logger.warning("Initial capital is zero - cannot calculate return percentage")
        result.avg_trade_pnl = Decimal(str(np.mean([float(p) for p in pnls])))

        # Win rate and profit factor
        result.win_rate = PerformanceCalculator.win_rate(pnls)
        result.profit_factor = PerformanceCalculator.profit_factor(pnls)

        # Sharpe and Sortino
        if len(pnl_pcts) > 1:
            returns_arr = np.array(pnl_pcts)
            result.sharpe_ratio = PerformanceCalculator.sharpe_ratio(
                returns_arr, annualization=self.config.bars_per_year
            )
            result.sortino_ratio = PerformanceCalculator.sortino_ratio(
                returns_arr, annualization=self.config.bars_per_year
            )

        # Build equity curve and calculate max drawdown
        equity = [float(self.config.initial_capital)]
        for t in trades:
            equity.append(equity[-1] + float(t.pnl))

        result.equity_curve = [Decimal(str(e)) for e in equity]
        result.max_drawdown = Decimal(str(PerformanceCalculator.max_drawdown(np.array(equity))))

        return result

    def _aggregate_results(self, folds: List[FoldResult]) -> BacktestResults:
        """Aggregate fold results into overall backtest results."""
        results = BacktestResults(
            config=self.config,
            folds=folds,
        )

        if not folds:
            return results

        # Collect all trades
        all_trades = []
        for fold in folds:
            all_trades.extend(fold.trades)

        results.all_trades = all_trades
        results.total_trades = len(all_trades)

        if not all_trades:
            return results

        # Calculate aggregate metrics
        all_pnls = [t.pnl for t in all_trades]
        all_pnl_pcts = [float(t.pnl_pct) for t in all_trades]

        # Guard against division by zero
        if self.config.initial_capital > 0:
            results.total_return = sum(all_pnls) / self.config.initial_capital
        else:
            results.total_return = Decimal("0")
            logger.warning("Initial capital is zero - cannot calculate return percentage")

        # Annualized return
        total_bars = sum(f.num_trades for f in folds)
        years = total_bars / self.config.bars_per_year if total_bars > 0 else Decimal("1")
        if years > 0:
            results.annualized_return = (
                (Decimal("1") + results.total_return) ** (Decimal("1") / Decimal(str(years)))
                - Decimal("1")
            )

        # Win rate and profit factor
        results.win_rate = PerformanceCalculator.win_rate(all_pnls)
        results.profit_factor = PerformanceCalculator.profit_factor(all_pnls)

        # Sharpe, Sortino, Calmar
        if len(all_pnl_pcts) > 1:
            returns_arr = np.array(all_pnl_pcts)
            results.sharpe_ratio = PerformanceCalculator.sharpe_ratio(
                returns_arr, annualization=self.config.bars_per_year
            )
            results.sortino_ratio = PerformanceCalculator.sortino_ratio(
                returns_arr, annualization=self.config.bars_per_year
            )

        # Build full equity curve
        equity = [float(self.config.initial_capital)]
        for t in all_trades:
            equity.append(equity[-1] + float(t.pnl))

        results.equity_curve = [Decimal(str(e)) for e in equity]
        results.max_drawdown = Decimal(str(PerformanceCalculator.max_drawdown(np.array(equity))))

        # Calmar ratio
        if results.max_drawdown > 0:
            results.calmar_ratio = float(results.annualized_return) / float(results.max_drawdown)

        # Fold-level statistics
        fold_returns = [float(f.total_return) for f in folds]
        fold_sharpes = [f.sharpe_ratio for f in folds if f.num_trades > 0]

        results.fold_sharpe_std = float(np.std(fold_sharpes)) if len(fold_sharpes) > 1 else 0.0
        profitable_folds = len([r for r in fold_returns if r > 0])
        results.pct_profitable_folds = Decimal(profitable_folds) / Decimal(len(fold_returns)) if fold_returns else Decimal("0")
        results.worst_fold_return = Decimal(str(min(fold_returns))) if fold_returns else Decimal("0")
        results.best_fold_return = Decimal(str(max(fold_returns))) if fold_returns else Decimal("0")

        return results


def run_slippage_sensitivity(
    engine: BacktestEngine,
    signal_fn: SignalFunction,
    prices: np.ndarray,
    slippage_range: List[float] = None,
) -> Dict[float, BacktestResults]:
    """
    Run backtest across multiple slippage levels.

    Args:
        engine: BacktestEngine instance
        signal_fn: Signal function to test
        prices: OHLCV price data
        slippage_range: List of slippage values in basis points

    Returns:
        Dict mapping slippage -> BacktestResults
    """
    if slippage_range is None:
        slippage_range = [0, 5, 10, 20, 50]

    results = {}
    original_slippage = engine.config.cost_model.slippage_bps

    for slippage in slippage_range:
        engine.config.cost_model.slippage_bps = Decimal(str(slippage))
        result = engine.run_signal_backtest(signal_fn, prices)
        results[slippage] = result
        logger.info(
            f"Slippage {slippage}bps: Sharpe={result.sharpe_ratio:.2f}, "
            f"Return={float(result.total_return * 100):.1f}%"
        )

    engine.config.cost_model.slippage_bps = original_slippage

    return results
