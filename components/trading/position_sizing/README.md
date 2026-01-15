# Kelly Criterion Position Sizing Library

A production-ready implementation of the Kelly Criterion for optimal position sizing in trading and betting scenarios.

## Overview

The Kelly Criterion is a formula for determining the optimal size of a series of bets to maximize long-term growth rate while managing risk of ruin. Named after John L. Kelly Jr., who published the formula in 1956.

## Mathematical Foundation

### The Kelly Formula

```
Kelly % = (bp - q) / b
```

Where:
- **b** = odds (win amount / loss amount), also called "win/loss ratio"
- **p** = probability of winning
- **q** = probability of losing (1 - p)

### Interpretation

The formula tells you what percentage of your capital to bet on each opportunity to maximize long-term geometric growth.

### Edge

The numerator `(bp - q)` represents your "edge" - the expected value per unit bet:
- **Positive edge** (> 0): You have an advantage, Kelly recommends a position
- **Zero edge** (= 0): Break-even, Kelly recommends no position
- **Negative edge** (< 0): The house has an advantage, don't bet!

## Installation

Copy the `position-sizing` directory to your project:

```bash
cp -r ~/.claude/library/components/trading/position-sizing ./your_project/lib/
```

## Quick Start

```python
from position_sizing import KellyCriterion, HALF_KELLY
from decimal import Decimal

# Initialize calculator with 25% maximum position
kelly = KellyCriterion(max_kelly_fraction=Decimal("0.25"))

# Calculate optimal position
result = kelly.calculate(
    win_probability=Decimal("0.55"),  # 55% win rate
    win_loss_ratio=Decimal("1.5")     # Win $1.50 for every $1 risked
)

print(f"Kelly Percentage: {result.final_kelly:.2%}")
print(f"Edge: {result.edge:.2%}")
print(f"Regime: {result.regime.value}")
```

## Features

### 1. Full Kelly Calculation

```python
result = kelly.calculate(
    win_probability=Decimal("0.60"),
    win_loss_ratio=Decimal("2.0")
)
# Full Kelly for 60% win rate with 2:1 payoff
```

### 2. Fractional Kelly (Risk Management)

Using fractional Kelly reduces variance and drawdowns at the cost of some expected growth:

```python
# Half-Kelly (most common for trading)
result = kelly.calculate(
    win_probability=Decimal("0.55"),
    win_loss_ratio=Decimal("1.5"),
    fraction=Decimal("0.5")  # Half Kelly
)

# Or use the constant
from position_sizing import HALF_KELLY
result = kelly.calculate(
    win_probability=Decimal("0.55"),
    win_loss_ratio=Decimal("1.5"),
    fraction=HALF_KELLY
)
```

### 3. Position Size in Dollar Terms

```python
pos_result = kelly.position_size(
    capital=Decimal("100000"),        # $100,000 account
    win_probability=Decimal("0.55"),
    win_loss_ratio=Decimal("1.5"),
    fraction=HALF_KELLY,
    max_position=Decimal("10000")     # Optional: cap at $10k
)

print(f"Position: ${pos_result.position_size:.2f}")
print(f"As % of capital: {pos_result.position_percentage}%")
```

### 4. Calculate from Trading History

```python
result = kelly.calculate_from_history(
    wins=65,
    losses=35,
    average_win=Decimal("200"),
    average_loss=Decimal("150")
)
# Automatically calculates win rate and win/loss ratio
```

### 5. Maximum Position Cap (Overleverage Protection)

```python
# Never allocate more than 25% to a single position
kelly = KellyCriterion(max_kelly_fraction=Decimal("0.25"))

# Even with extreme edge, position is capped
result = kelly.calculate(
    win_probability=Decimal("0.80"),  # 80% win rate
    win_loss_ratio=Decimal("3.0")     # 3:1 payoff
)
# result.final_kelly will be capped at 0.25
```

### 6. Drawdown-Aware Fraction Selection

```python
fraction, result = kelly.optimal_fraction_for_drawdown(
    win_probability=Decimal("0.55"),
    win_loss_ratio=Decimal("1.5"),
    max_drawdown_tolerance=Decimal("0.15")  # 15% max acceptable DD
)
print(f"Recommended fraction: {fraction}")
```

### 7. Risk of Ruin Estimation

```python
risk = kelly.risk_of_ruin(
    win_probability=Decimal("0.55"),
    win_loss_ratio=Decimal("1.5"),
    kelly_fraction=Decimal("0.5"),
    ruin_threshold=Decimal("0.5")  # 50% loss = ruin
)
print(f"Risk of ruin: {risk:.4%}")
```

## Kelly Regimes

The calculator classifies positions into regimes:

| Regime | Kelly Range | Description |
|--------|-------------|-------------|
| NO_BET | <= 0% | No edge, don't trade |
| MINIMAL | 0-5% | Very small edge, minimal position |
| CONSERVATIVE | 5-10% | Decent edge, conservative position |
| MODERATE | 10-25% | Good edge, standard position |
| AGGRESSIVE | > 25% | Strong edge, large position |

## Why Use Decimal?

**NEVER use float for financial calculations!**

```python
# BAD - float precision issues
>>> 0.1 + 0.2
0.30000000000000004

# GOOD - Decimal is exact
>>> Decimal("0.1") + Decimal("0.2")
Decimal('0.3')
```

All methods in this library require Decimal inputs and return Decimal outputs.

## Common Kelly Fractions

| Fraction | Use Case |
|----------|----------|
| Full (1.0) | Theoretical maximum, rarely used in practice |
| Half (0.5) | Most common for professional traders |
| Quarter (0.25) | Conservative, good for beginners |
| Tenth (0.1) | Ultra-conservative, minimal drawdowns |

## Real-World Considerations

### When to Use Less Than Full Kelly

1. **Parameter Uncertainty**: Your win probability and win/loss ratio are estimates
2. **Correlation**: Multiple positions may be correlated
3. **Drawdown Sensitivity**: Full Kelly can have 50%+ drawdowns
4. **Psychological Comfort**: Smaller positions are easier to manage

### Rule of Thumb

Use **Half-Kelly or less** unless you have:
- High confidence in your edge estimates
- A long time horizon
- Strong psychological discipline
- Low correlation between bets

## Example: Complete Trading System

```python
from position_sizing import KellyCriterion, HALF_KELLY
from decimal import Decimal

class TradingSystem:
    def __init__(self, capital: Decimal):
        self.capital = capital
        self.kelly = KellyCriterion(
            max_kelly_fraction=Decimal("0.20"),  # 20% max per trade
            min_edge=Decimal("0.02")             # Require 2% edge minimum
        )

    def size_position(self, signal_strength: Decimal) -> Decimal:
        # Convert signal to win probability estimate
        win_prob = Decimal("0.50") + (signal_strength * Decimal("0.15"))
        win_loss_ratio = Decimal("1.5")  # Fixed 1.5:1 target

        result = self.kelly.position_size(
            capital=self.capital,
            win_probability=win_prob,
            win_loss_ratio=win_loss_ratio,
            fraction=HALF_KELLY
        )

        if result.kelly_result.is_favorable:
            return result.position_size
        return Decimal("0")

# Usage
system = TradingSystem(capital=Decimal("100000"))
position = system.size_position(signal_strength=Decimal("0.3"))
print(f"Position size: ${position:.2f}")
```

## API Reference

### KellyCriterion

```python
KellyCriterion(
    max_kelly_fraction: Decimal = Decimal("1.0"),
    min_edge: Decimal = Decimal("0.01"),
    default_fraction: Decimal = Decimal("1.0")
)
```

### Methods

- `calculate(win_probability, win_loss_ratio, fraction)` -> `KellyResult`
- `position_size(capital, win_probability, win_loss_ratio, fraction, max_position)` -> `PositionSizeResult`
- `calculate_from_history(wins, losses, average_win, average_loss, fraction)` -> `KellyResult`
- `optimal_fraction_for_drawdown(win_probability, win_loss_ratio, max_drawdown_tolerance)` -> `Tuple[Decimal, KellyResult]`
- `risk_of_ruin(win_probability, win_loss_ratio, kelly_fraction, ruin_threshold)` -> `Decimal`

## Testing

Run the tests:

```bash
python -m pytest tests/test_kelly.py -v
```

## License

MIT License - Extracted from trader-ai project.

## References

1. Kelly, J.L. (1956). "A New Interpretation of Information Rate"
2. Thorp, E.O. (2006). "The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market"
3. MacLean, Thorp, Ziemba (2011). "The Kelly Capital Growth Investment Criterion"
