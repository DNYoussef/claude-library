# Gate System - Capital-Based Trading Progression

A reusable component for managing trading privileges and constraints based on capital levels. Implements G0-G12 capital tier progression with configurable thresholds, position limits, and risk controls.

## Origin

Extracted from `D:\Projects\trader-ai\src\gates\` (Trader AI project).

## Features

- **G0-G12 Capital Tiers**: 13 levels of progressive trading capabilities
- **Trade Validation**: Checks asset permissions, position limits, cash floors, theta limits
- **Graduation Logic**: Automatic progression based on performance and compliance
- **Downgrade Protection**: Automatic downgrade on excessive violations or poor performance
- **Violation Tracking**: Complete history with resolution support
- **State Persistence**: Optional JSON-based state storage
- **Event Callbacks**: Hooks for violations, graduations, and downgrades

## Gate Tier Overview

| Gate | Capital Range | Cash Floor | Options | Max Position | Description |
|------|---------------|------------|---------|--------------|-------------|
| G0 | $200-$500 | 50% | No | 25% | Starter - Limited assets |
| G1 | $500-$1K | 60% | No | 22% | Beginner - Hedging unlocked |
| G2 | $1K-$2.5K | 65% | No | 20% | Intermediate - Factor ETFs |
| G3 | $2.5K-$5K | 70% | Yes | 20% | Advanced - Options enabled |
| G4 | $5K-$10K | 65% | Yes | 21% | Expert tier |
| G5 | $10K-$25K | 60% | Yes | 22% | Professional tier |
| G6 | $25K-$50K | 55% | Yes | 23% | Elite tier |
| G7 | $50K-$100K | 50% | Yes | 24% | Master tier |
| G8 | $100K-$250K | 45% | Yes | 25% | Grandmaster tier |
| G9 | $250K-$500K | 40% | Yes | 26% | Legend tier |
| G10 | $500K-$1M | 35% | Yes | 27% | Titan tier |
| G11 | $1M-$10M | 30% | Yes | 28% | Apex tier |
| G12 | $10M+ | 30% | Yes | 30% | Ultimate tier |

## Installation

Copy the `gate-system` directory to your project:

```bash
cp -r ~/.claude/library/components/trading/gate-system your-project/src/
```

## Quick Start

```python
from gate_system import GateManager, GateLevel

# Initialize with defaults
manager = GateManager()

# Set current capital (determines gate level)
manager.update_capital(500.0)  # -> G1

# Get current status
status = manager.get_status_report()
print(f"Current Gate: {status['current_gate']}")
print(f"Allowed Assets: {status['gate_config']['allowed_assets']}")
```

## Trade Validation

```python
# Validate a trade
result = manager.validate_trade(
    trade_details={
        'symbol': 'SPY',
        'side': 'BUY',
        'quantity': 10,
        'price': 450.0,
        'trade_type': 'STOCK'
    },
    current_portfolio={
        'cash': 5000.0,
        'total_value': 10000.0,
        'positions': {}
    }
)

if result.is_valid:
    print("Trade approved!")
else:
    for violation in result.violations:
        print(f"Violation: {violation['type']} - {violation['message']}")

# Check warnings (approaching limits)
for warning in result.warnings:
    print(f"Warning: {warning['message']}")
```

## Gate Progression

```python
# Check if ready to graduate
decision = manager.check_graduation({
    'sharpe_ratio_30d': 1.5,
    'max_drawdown_30d': 0.05,
    'avg_cash_utilization_30d': 0.35
})

if decision == 'GRADUATE':
    manager.execute_graduation()
    print(f"Congratulations! Now at {manager.current_gate.value}")
elif decision == 'DOWNGRADE':
    manager.execute_downgrade()
    print(f"Downgraded to {manager.current_gate.value}")
else:
    print("Keep building your track record!")
```

## Graduation Criteria (Default)

| From Gate | Min Days | Max Violations | Min Performance | Min Capital |
|-----------|----------|----------------|-----------------|-------------|
| G0 -> G1 | 14 | 2 | 0.60 | $500 |
| G1 -> G2 | 21 | 1 | 0.70 | $1,000 |
| G2 -> G3 | 30 | 0 | 0.75 | $2,500 |
| G3 -> G4 | 45 | 0 | 0.80 | $5,000 |

## Downgrade Criteria (Default)

- More than 5 violations in 30 days
- Performance score below 0.30
- Drawdown exceeding 15%

## Custom Configuration

```python
from gate_system import GateManager, GateConfig, GateLevel

# Custom gate configurations
custom_configs = {
    GateLevel.G0: GateConfig(
        level=GateLevel.G0,
        capital_min=100.0,
        capital_max=499.99,
        allowed_assets={'SPY', 'QQQ', 'IWM'},
        cash_floor_pct=0.40,
        options_enabled=False,
        max_position_pct=0.30,
        risk_pct=0.05,
        description="Custom starter tier"
    ),
    # Add more gates...
}

# Custom graduation criteria
custom_graduation = {
    GateLevel.G0: {
        'min_compliant_days': 7,
        'max_violations_30d': 3,
        'min_performance_score': 0.5,
        'min_capital': 500.0
    }
}

manager = GateManager(
    gate_configs=custom_configs,
    graduation_criteria=custom_graduation
)
```

## Event Callbacks

```python
def on_violation(violation):
    print(f"VIOLATION: {violation.violation_type.value}")
    # Send alert, log to database, etc.

def on_graduation(from_gate, to_gate):
    print(f"GRADUATED: {from_gate.value} -> {to_gate.value}")
    # Send celebration notification

def on_downgrade(from_gate, to_gate):
    print(f"DOWNGRADED: {from_gate.value} -> {to_gate.value}")
    # Send warning notification

manager = GateManager(
    on_violation=on_violation,
    on_graduation=on_graduation,
    on_downgrade=on_downgrade
)
```

## State Persistence

```python
# Enable state persistence
manager = GateManager(data_dir="./data/gates")

# State is automatically saved on:
# - Capital updates
# - Violations
# - Graduations/Downgrades

# State is automatically loaded on initialization
```

## Violation Management

```python
# Get recent violations
violations = manager.get_violation_history(days=7)

for v in violations:
    print(f"{v.timestamp}: {v.violation_type.value} - {v.message}")

# Resolve a violation
manager.resolve_violation(index=0, resolution_note="User acknowledged and adjusted")
```

## API Reference

### GateManager

| Method | Description |
|--------|-------------|
| `update_capital(amount)` | Update capital and check gate changes |
| `validate_trade(trade, portfolio)` | Validate trade against gate constraints |
| `check_graduation(metrics)` | Check if ready for graduation/downgrade |
| `execute_graduation()` | Graduate to next gate |
| `execute_downgrade()` | Downgrade to previous gate |
| `get_status_report()` | Get comprehensive status |
| `get_violation_history(days)` | Get recent violations |
| `resolve_violation(index, note)` | Mark violation as resolved |

### TradeValidationResult

| Attribute | Type | Description |
|-----------|------|-------------|
| `is_valid` | bool | Whether trade passes all checks |
| `violations` | List[Dict] | List of violations |
| `warnings` | List[Dict] | List of warnings |

### ViolationType

- `ASSET_NOT_ALLOWED` - Asset not permitted at current gate
- `CASH_FLOOR_VIOLATION` - Trade would breach cash floor
- `OPTIONS_NOT_ALLOWED` - Options not enabled at current gate
- `THETA_LIMIT_EXCEEDED` - Theta exposure too high
- `POSITION_SIZE_EXCEEDED` - Position too large
- `CONCENTRATION_EXCEEDED` - Sector concentration too high
- `CAPITAL_INSUFFICIENT` - Not enough capital

## Integration with Trader AI

This component was extracted from Trader AI's gate system. To integrate back:

```python
# In trader-ai, replace:
from src.gates.gate_manager import GateManager

# With:
from gate_system import GateManager
```

## License

MIT License - Extracted from Trader AI project.
