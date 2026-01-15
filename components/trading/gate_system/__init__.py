"""
Gate System - Capital-Based Trading Progression Management

A reusable component for managing trading privileges and constraints based on
capital levels. Implements G0-G12 capital tier progression with configurable
thresholds, position limits, and risk controls.

Example Usage:
    from gate_system import GateManager, GateLevel, GateConfig

    # Basic usage with defaults (G0-G12 tiers)
    manager = GateManager()
    manager.update_capital(500.0)

    # Validate a trade
    result = manager.validate_trade(
        trade_details={'symbol': 'SPY', 'side': 'BUY', 'quantity': 10, 'price': 450.0},
        current_portfolio={'cash': 5000.0, 'total_value': 10000.0, 'positions': {}}
    )

    if result.is_valid:
        print("Trade approved!")
    else:
        print(f"Trade rejected: {result.violations}")

    # Check graduation status
    decision = manager.check_graduation({
        'sharpe_ratio_30d': 1.5,
        'max_drawdown_30d': 0.05,
        'avg_cash_utilization_30d': 0.35
    })

    if decision == 'GRADUATE':
        manager.execute_graduation()

Features:
    - G0-G12 capital tier progression (configurable)
    - Maximum position limits per gate
    - Risk percentage per gate
    - Gate transition logic (graduation/downgrade)
    - Violation tracking and history
    - Performance scoring for progression
    - State persistence (optional)
    - Event callbacks for violations, graduations, downgrades
"""

# Support both package import and direct script execution
try:
    from .gate_manager import (
        # Enums
        GateLevel,
        ViolationType,

        # Data classes
        GateConfig,
        TradeValidationResult,
        ViolationRecord,
        GraduationMetrics,

        # Main class
        GateManager,

        # Helper functions
        create_default_gate_configs,

        # Constants
        DEFAULT_GATE_THRESHOLDS,
    )
except ImportError:
    # Direct execution - use absolute import
    from gate_manager import (
        GateLevel,
        ViolationType,
        GateConfig,
        TradeValidationResult,
        ViolationRecord,
        GraduationMetrics,
        GateManager,
        create_default_gate_configs,
        DEFAULT_GATE_THRESHOLDS,
    )

__all__ = [
    # Enums
    'GateLevel',
    'ViolationType',

    # Data classes
    'GateConfig',
    'TradeValidationResult',
    'ViolationRecord',
    'GraduationMetrics',

    # Main class
    'GateManager',

    # Helper functions
    'create_default_gate_configs',

    # Constants
    'DEFAULT_GATE_THRESHOLDS',
]

__version__ = '1.0.0'
__author__ = 'David Youssef'
__source__ = 'trader-ai'
