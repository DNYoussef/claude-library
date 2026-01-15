"""
Gate Management System for Capital-Based Trading Progression

A generalized component for managing trading privileges and constraints based
on capital levels. Enforces risk management rules and tracks performance
metrics for graduation/downgrade decisions.

Features:
- G0-G12 capital tier progression (configurable)
- Maximum position limits per gate
- Risk percentage per gate
- Gate transition logic (graduation/downgrade)
- Violation tracking and history
- Performance scoring for progression

Usage:
    from gate_system import GateManager, GateLevel, GateConfig

    # Basic usage with defaults
    manager = GateManager()
    manager.update_capital(500.0)

    # Validate a trade
    result = manager.validate_trade(trade_details, portfolio)
    if not result.is_valid:
        print(result.violations)

    # Custom configuration
    custom_configs = {
        GateLevel.G0: GateConfig(
            level=GateLevel.G0,
            capital_min=100.0,
            capital_max=499.99,
            allowed_assets={'SPY', 'QQQ'},
            cash_floor_pct=0.50,
            options_enabled=False
        )
    }
    manager = GateManager(gate_configs=custom_configs)
"""

from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class GateLevel(Enum):
    """Trading gate levels based on capital ranges (G0-G12)."""
    G0 = "G0"    # Starter tier
    G1 = "G1"    # Beginner tier
    G2 = "G2"    # Intermediate tier
    G3 = "G3"    # Advanced tier
    G4 = "G4"    # Expert tier
    G5 = "G5"    # Professional tier
    G6 = "G6"    # Elite tier
    G7 = "G7"    # Master tier
    G8 = "G8"    # Grandmaster tier
    G9 = "G9"    # Legend tier
    G10 = "G10"  # Titan tier
    G11 = "G11"  # Apex tier
    G12 = "G12"  # Ultimate tier


class ViolationType(Enum):
    """Types of gate violations."""
    ASSET_NOT_ALLOWED = "asset_not_allowed"
    CASH_FLOOR_VIOLATION = "cash_floor_violation"
    OPTIONS_NOT_ALLOWED = "options_not_allowed"
    THETA_LIMIT_EXCEEDED = "theta_limit_exceeded"
    POSITION_SIZE_EXCEEDED = "position_size_exceeded"
    CONCENTRATION_EXCEEDED = "concentration_exceeded"
    CAPITAL_INSUFFICIENT = "capital_insufficient"


@dataclass
class GateConfig:
    """Configuration for a specific gate level.

    IMPORTANT: All monetary values use Decimal for financial precision.
    Never use float for money calculations!
    """
    level: GateLevel
    capital_min: Decimal
    capital_max: Decimal
    allowed_assets: Set[str]
    cash_floor_pct: Decimal
    options_enabled: bool
    max_theta_pct: Optional[Decimal] = None
    max_position_pct: Decimal = Decimal("0.20")  # 20% max position size
    max_concentration_pct: Decimal = Decimal("0.30")  # 30% max sector concentration
    risk_pct: Decimal = Decimal("0.05")  # 5% max risk per trade
    description: str = ""

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Convert to Decimal if float passed (backwards compatibility)
        if isinstance(self.capital_min, float):
            object.__setattr__(self, 'capital_min', Decimal(str(self.capital_min)))
        if isinstance(self.capital_max, float):
            object.__setattr__(self, 'capital_max', Decimal(str(self.capital_max)))
        if isinstance(self.cash_floor_pct, float):
            object.__setattr__(self, 'cash_floor_pct', Decimal(str(self.cash_floor_pct)))
        if isinstance(self.max_theta_pct, float):
            object.__setattr__(self, 'max_theta_pct', Decimal(str(self.max_theta_pct)))
        if isinstance(self.max_position_pct, float):
            object.__setattr__(self, 'max_position_pct', Decimal(str(self.max_position_pct)))
        if isinstance(self.max_concentration_pct, float):
            object.__setattr__(self, 'max_concentration_pct', Decimal(str(self.max_concentration_pct)))
        if isinstance(self.risk_pct, float):
            object.__setattr__(self, 'risk_pct', Decimal(str(self.risk_pct)))

        if self.capital_min >= self.capital_max:
            raise ValueError(f"Invalid capital range: {self.capital_min} >= {self.capital_max}")
        if not 0 <= self.cash_floor_pct <= 1:
            raise ValueError(f"Invalid cash floor percentage: {self.cash_floor_pct}")
        if self.max_theta_pct is not None and not 0 <= self.max_theta_pct <= 1:
            raise ValueError(f"Invalid theta percentage: {self.max_theta_pct}")
        if not 0 <= self.max_position_pct <= 1:
            raise ValueError(f"Invalid max position percentage: {self.max_position_pct}")
        if not 0 <= self.risk_pct <= 1:
            raise ValueError(f"Invalid risk percentage: {self.risk_pct}")


@dataclass
class TradeValidationResult:
    """Result of trade validation against gate constraints."""
    is_valid: bool
    violations: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)

    def add_violation(self, violation_type: ViolationType, message: str,
                     details: Optional[Dict[str, Any]] = None):
        """Add a violation to the result."""
        self.is_valid = False
        self.violations.append({
            'type': violation_type.value,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })

    def add_warning(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Add a warning to the result."""
        self.warnings.append({
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })


@dataclass
class ViolationRecord:
    """Record of a gate violation."""
    timestamp: datetime
    gate_level: GateLevel
    violation_type: ViolationType
    message: str
    details: Dict[str, Any]
    resolved: bool = False
    resolution_note: Optional[str] = None


@dataclass
class GraduationMetrics:
    """Metrics tracked for gate graduation/downgrade decisions.

    Note: Metrics use Decimal for financial precision where applicable.
    """
    consecutive_compliant_days: int = 0
    total_violations_30d: int = 0
    avg_cash_utilization_30d: Decimal = field(default_factory=lambda: Decimal("0.0"))
    max_drawdown_30d: Decimal = field(default_factory=lambda: Decimal("0.0"))
    sharpe_ratio_30d: Optional[Decimal] = None
    last_violation_date: Optional[datetime] = None
    performance_score: Decimal = field(default_factory=lambda: Decimal("0.0"))


# Maximum capital sentinel value (replaces float('inf') for JSON compatibility)
MAX_CAPITAL_SENTINEL = Decimal("999999999999.99")  # ~1 trillion

# Default gate thresholds (G0 to G12 capital ranges) - uses Decimal for precision
DEFAULT_GATE_THRESHOLDS: list[tuple[Decimal, Decimal]] = [
    (Decimal("200"), Decimal("499.99")),          # G0
    (Decimal("500"), Decimal("999.99")),          # G1
    (Decimal("1000"), Decimal("2499.99")),        # G2
    (Decimal("2500"), Decimal("4999.99")),        # G3
    (Decimal("5000"), Decimal("9999.99")),        # G4
    (Decimal("10000"), Decimal("24999.99")),      # G5
    (Decimal("25000"), Decimal("49999.99")),      # G6
    (Decimal("50000"), Decimal("99999.99")),      # G7
    (Decimal("100000"), Decimal("249999.99")),    # G8
    (Decimal("250000"), Decimal("499999.99")),    # G9
    (Decimal("500000"), Decimal("999999.99")),    # G10
    (Decimal("1000000"), Decimal("9999999.99")),  # G11
    (Decimal("10000000"), MAX_CAPITAL_SENTINEL),  # G12
]


def create_default_gate_configs() -> Dict[GateLevel, GateConfig]:
    """
    Create default gate configurations for G0-G12.

    All monetary and percentage values use Decimal for financial precision.

    Returns:
        Dictionary mapping GateLevel to GateConfig
    """
    configs = {}

    # G0: $200-499, limited assets, 50% cash floor, no options
    configs[GateLevel.G0] = GateConfig(
        level=GateLevel.G0,
        capital_min=Decimal("200"),
        capital_max=Decimal("499.99"),
        allowed_assets={'ULTY', 'AMDY'},
        cash_floor_pct=Decimal("0.50"),
        options_enabled=False,
        max_position_pct=Decimal("0.25"),
        max_concentration_pct=Decimal("0.40"),
        risk_pct=Decimal("0.05"),
        description="Starter tier - Build discipline with limited assets"
    )

    # G1: $500-999, adds hedging assets, 60% cash floor
    configs[GateLevel.G1] = GateConfig(
        level=GateLevel.G1,
        capital_min=Decimal("500"),
        capital_max=Decimal("999.99"),
        allowed_assets={'ULTY', 'AMDY', 'IAU', 'GLDM', 'VTIP'},
        cash_floor_pct=Decimal("0.60"),
        options_enabled=False,
        max_position_pct=Decimal("0.22"),
        max_concentration_pct=Decimal("0.35"),
        risk_pct=Decimal("0.05"),
        description="Beginner tier - Hedging strategies unlocked"
    )

    # G2: $1k-2.5k, adds factor ETFs, 65% cash floor
    configs[GateLevel.G2] = GateConfig(
        level=GateLevel.G2,
        capital_min=Decimal("1000"),
        capital_max=Decimal("2499.99"),
        allowed_assets={
            'ULTY', 'AMDY', 'IAU', 'GLDM', 'VTIP',
            'VTI', 'VTV', 'VUG', 'VEA', 'VWO',
            'SCHD', 'DGRO', 'NOBL', 'VYM'
        },
        cash_floor_pct=Decimal("0.65"),
        options_enabled=False,
        max_position_pct=Decimal("0.20"),
        max_concentration_pct=Decimal("0.30"),
        risk_pct=Decimal("0.05"),
        description="Intermediate tier - Factor ETFs and dividends"
    )

    # G3: $2.5k-5k, enables long options, 70% cash floor, 0.5% theta
    configs[GateLevel.G3] = GateConfig(
        level=GateLevel.G3,
        capital_min=Decimal("2500"),
        capital_max=Decimal("4999.99"),
        allowed_assets={
            'ULTY', 'AMDY', 'IAU', 'GLDM', 'VTIP',
            'VTI', 'VTV', 'VUG', 'VEA', 'VWO',
            'SCHD', 'DGRO', 'NOBL', 'VYM',
            'SPY', 'QQQ', 'IWM', 'DIA'
        },
        cash_floor_pct=Decimal("0.70"),
        options_enabled=True,
        max_theta_pct=Decimal("0.005"),
        max_position_pct=Decimal("0.20"),
        max_concentration_pct=Decimal("0.30"),
        risk_pct=Decimal("0.04"),
        description="Advanced tier - Options trading enabled"
    )

    # G4-G12: Progressively more flexibility
    for i, gate in enumerate([GateLevel.G4, GateLevel.G5, GateLevel.G6,
                              GateLevel.G7, GateLevel.G8, GateLevel.G9,
                              GateLevel.G10, GateLevel.G11, GateLevel.G12]):
        min_cap, max_cap = DEFAULT_GATE_THRESHOLDS[i + 4]
        # Calculate percentages as Decimal
        floor_pct = max(Decimal("0.30"), Decimal("0.70") - (Decimal(str(i)) * Decimal("0.05")))
        theta_pct = min(Decimal("0.02"), Decimal("0.005") + (Decimal(str(i)) * Decimal("0.002")))
        pos_pct = min(Decimal("0.30"), Decimal("0.20") + (Decimal(str(i)) * Decimal("0.01")))
        conc_pct = min(Decimal("0.40"), Decimal("0.30") + (Decimal(str(i)) * Decimal("0.01")))
        risk = max(Decimal("0.02"), Decimal("0.04") - (Decimal(str(i)) * Decimal("0.002")))

        configs[gate] = GateConfig(
            level=gate,
            capital_min=min_cap,
            capital_max=max_cap,
            allowed_assets={'*'},  # All assets allowed at higher tiers
            cash_floor_pct=floor_pct,
            options_enabled=True,
            max_theta_pct=theta_pct,
            max_position_pct=pos_pct,
            max_concentration_pct=conc_pct,
            risk_pct=risk,
            description=f"Tier {gate.value} - Professional level trading"
        )

    return configs


class GateManager:
    """
    Manages trading gates, validation, and progression.

    The gate system controls what assets and strategies a trader can use
    based on their capital level and track record. It enforces progressive
    unlocking of capabilities as the trader demonstrates discipline.

    Thread Safety:
        All public methods are thread-safe via RLock. The lock is reentrant
        to allow nested method calls within the same thread.
    """

    def __init__(
        self,
        data_dir: Optional[str] = None,
        gate_configs: Optional[Dict[GateLevel, GateConfig]] = None,
        graduation_criteria: Optional[Dict[GateLevel, Dict[str, Any]]] = None,
        downgrade_criteria: Optional[Dict[str, Any]] = None,
        on_violation: Optional[Callable[[ViolationRecord], None]] = None,
        on_graduation: Optional[Callable[[GateLevel, GateLevel], None]] = None,
        on_downgrade: Optional[Callable[[GateLevel, GateLevel], None]] = None
    ):
        """
        Initialize the gate manager.

        Args:
            data_dir: Directory for persisting state (optional)
            gate_configs: Custom gate configurations (uses defaults if None)
            graduation_criteria: Custom graduation criteria per gate
            downgrade_criteria: Custom downgrade criteria
            on_violation: Callback for violation events
            on_graduation: Callback for graduation events
            on_downgrade: Callback for downgrade events
        """
        # Thread safety lock (RLock allows reentrant calls)
        self._lock = threading.RLock()

        self.data_dir = Path(data_dir) if data_dir else None
        if self.data_dir:
            self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize gate configurations
        self.gate_configs = gate_configs or create_default_gate_configs()

        # Graduation/downgrade criteria
        self.graduation_criteria = graduation_criteria or self._default_graduation_criteria()
        self.downgrade_criteria = downgrade_criteria or self._default_downgrade_criteria()

        # Callbacks
        self.on_violation = on_violation
        self.on_graduation = on_graduation
        self.on_downgrade = on_downgrade

        # Current state - use Decimal for capital
        self.current_gate = GateLevel.G0
        self.current_capital: Decimal = Decimal("0")
        self.violation_history: List[ViolationRecord] = []
        self.graduation_metrics = GraduationMetrics()

        # Load persisted state
        if self.data_dir:
            self._load_state()

    def _default_graduation_criteria(self) -> Dict[GateLevel, Dict[str, Any]]:
        """Generate default graduation criteria for each gate."""
        return {
            GateLevel.G0: {
                'min_compliant_days': 14,
                'max_violations_30d': 2,
                'min_performance_score': 0.6,
                'min_capital': 500.0
            },
            GateLevel.G1: {
                'min_compliant_days': 21,
                'max_violations_30d': 1,
                'min_performance_score': 0.7,
                'min_capital': 1000.0
            },
            GateLevel.G2: {
                'min_compliant_days': 30,
                'max_violations_30d': 0,
                'min_performance_score': 0.75,
                'min_capital': 2500.0
            },
            GateLevel.G3: {
                'min_compliant_days': 45,
                'max_violations_30d': 0,
                'min_performance_score': 0.80,
                'min_capital': 5000.0
            }
        }

    def _default_downgrade_criteria(self) -> Dict[str, Any]:
        """Generate default downgrade criteria."""
        return {
            'max_violations_30d': 5,
            'min_performance_score': 0.3,
            'max_drawdown_threshold': 0.15  # 15% drawdown
        }

    def get_current_config(self) -> GateConfig:
        """Get the configuration for the current gate level."""
        return self.gate_configs[self.current_gate]

    def get_gate_config(self, level: GateLevel) -> Optional[GateConfig]:
        """Get configuration for a specific gate level."""
        return self.gate_configs.get(level)

    def get_all_gates(self) -> List[Dict[str, Any]]:
        """Get summary of all gate configurations."""
        return [
            {
                'level': config.level.value,
                'capital_range': f"${config.capital_min:,.0f}-${config.capital_max:,.0f}",
                'cash_floor': f"{config.cash_floor_pct*100:.0f}%",
                'options_enabled': config.options_enabled,
                'max_position': f"{config.max_position_pct*100:.0f}%",
                'description': config.description
            }
            for config in self.gate_configs.values()
        ]

    def update_capital(self, new_capital: Decimal | float | int) -> bool:
        """
        Update current capital and check if gate change is needed.

        Thread-safe: Uses RLock for synchronization.

        Args:
            new_capital: New capital amount (accepts Decimal, float, or int)

        Returns:
            True if gate changed, False otherwise
        """
        with self._lock:
            # Convert to Decimal if needed
            if not isinstance(new_capital, Decimal):
                new_capital = Decimal(str(new_capital))

            old_capital = self.current_capital
            self.current_capital = new_capital

            # Check if we need to change gates based on capital
            new_gate = self._determine_gate_by_capital(new_capital)

            if new_gate == self.current_gate:
                return False

            old_gate = self.current_gate
            logger.info(f"Capital change from ${old_capital} to ${new_capital} "
                       f"triggers gate change from {old_gate.value} to {new_gate.value}")
            self.current_gate = new_gate
            self._save_state()
            return True

    def _determine_gate_by_capital(self, capital: Decimal) -> GateLevel:
        """Determine appropriate gate level based on capital amount."""
        for gate_level, config in self.gate_configs.items():
            if config.capital_min <= capital <= config.capital_max:
                return gate_level

        # If capital exceeds all gates, return highest gate
        max_gate = max(self.gate_configs.keys(), key=lambda g: self.gate_configs[g].capital_max)
        if capital > self.gate_configs[max_gate].capital_max:
            return max_gate

        # If capital is below minimum, use G0
        return GateLevel.G0

    def validate_trade(
        self,
        trade_details: Dict[str, Any],
        current_portfolio: Dict[str, Any]
    ) -> TradeValidationResult:
        """
        Validate a trade against current gate constraints.

        Thread-safe: Uses RLock for synchronization.

        Args:
            trade_details: Dict containing trade information
                - symbol: str, asset symbol
                - side: str, 'BUY' or 'SELL'
                - quantity: Decimal, number of shares/contracts
                - price: Decimal, expected execution price
                - trade_type: str, 'STOCK' or 'OPTION'
                - option_type: str, 'CALL' or 'PUT' (if applicable)
                - theta: Decimal, theta exposure (if options)
                - kelly_percentage: Decimal, optional Kelly % for enhanced validation
            current_portfolio: Dict containing current portfolio state
                - cash: Decimal, available cash
                - positions: Dict[str, Dict], current positions
                - total_value: Decimal, total portfolio value

        Returns:
            TradeValidationResult with validation outcome
        """
        with self._lock:
            result = TradeValidationResult(is_valid=True)
            config = self.get_current_config()

            symbol = trade_details.get('symbol', '').upper()
            trade_type = trade_details.get('trade_type', 'STOCK').upper()
            side = trade_details.get('side', '').upper()
            quantity = Decimal(str(trade_details.get('quantity', 0)))
            price = Decimal(str(trade_details.get('price', 0)))

            # 1. Check if asset is allowed (unless wildcard)
            if '*' not in config.allowed_assets and symbol not in config.allowed_assets:
                result.add_violation(
                    ViolationType.ASSET_NOT_ALLOWED,
                    f"Asset {symbol} not allowed in {config.level.value}",
                    {'symbol': symbol, 'allowed_assets': list(config.allowed_assets)}
                )

            # 2. Check options permissions
            if trade_type == 'OPTION' and not config.options_enabled:
                result.add_violation(
                    ViolationType.OPTIONS_NOT_ALLOWED,
                    f"Options trading not enabled for {config.level.value}",
                    {'trade_type': trade_type}
                )

            # 3. Check cash floor after trade
            trade_value = quantity * price
            if side == 'BUY':
                current_cash = Decimal(str(current_portfolio.get('cash', 0)))
                current_total = Decimal(str(current_portfolio.get('total_value', 0)))

                post_trade_cash = current_cash - trade_value
                required_cash = current_total * config.cash_floor_pct

                if post_trade_cash < required_cash:
                    result.add_violation(
                        ViolationType.CASH_FLOOR_VIOLATION,
                        f"Trade would violate {config.cash_floor_pct*100:.0f}% cash floor",
                        {
                            'current_cash': str(current_cash),
                            'post_trade_cash': str(post_trade_cash),
                            'required_cash': str(required_cash),
                            'cash_floor_pct': str(config.cash_floor_pct),
                            'shortfall': str(required_cash - post_trade_cash)
                        }
                    )

            # 4. Check theta limits for options
            if (trade_type == 'OPTION' and config.max_theta_pct is not None and
                side == 'BUY'):

                current_theta = Decimal(str(current_portfolio.get('total_theta', 0)))
                trade_theta = Decimal(str(trade_details.get('theta', 0))) * quantity
                new_total_theta = abs(current_theta + trade_theta)
                max_theta = Decimal(str(current_portfolio.get('total_value', 0))) * config.max_theta_pct

                if new_total_theta > max_theta:
                    result.add_violation(
                        ViolationType.THETA_LIMIT_EXCEEDED,
                        f"Trade would exceed {config.max_theta_pct*100:.1f}% theta limit",
                        {
                            'current_theta': str(current_theta),
                            'trade_theta': str(trade_theta),
                            'new_total_theta': str(new_total_theta),
                            'max_theta': str(max_theta)
                        }
                    )

            # 5. Check position size limits
            if side == 'BUY':
                current_position_value = Decimal("0")
                positions = current_portfolio.get('positions', {})
                if symbol in positions:
                    pos = positions[symbol]
                    current_position_value = Decimal(str(pos.get('quantity', 0))) * Decimal(str(pos.get('current_price', price)))

                new_position_value = current_position_value + trade_value
                max_position_value = Decimal(str(current_portfolio.get('total_value', 0))) * config.max_position_pct

                if new_position_value > max_position_value:
                    result.add_violation(
                        ViolationType.POSITION_SIZE_EXCEEDED,
                        f"Trade would exceed {config.max_position_pct*100:.0f}% position size limit",
                        {
                            'symbol': symbol,
                            'current_position_value': str(current_position_value),
                            'new_position_value': str(new_position_value),
                            'max_position_value': str(max_position_value)
                        }
                    )

            # 6. Kelly percentage validation (if provided)
            kelly_pct = trade_details.get('kelly_percentage')
            if kelly_pct is not None:
                kelly_pct = Decimal(str(kelly_pct))
                if kelly_pct > Decimal("1.0"):
                    result.add_violation(
                        ViolationType.POSITION_SIZE_EXCEEDED,
                        f"Kelly percentage {kelly_pct*100:.1f}% exceeds maximum allowed (100%)",
                        {'kelly_percentage': str(kelly_pct), 'max_kelly': '1.0'}
                    )

                if kelly_pct > config.max_position_pct:
                    result.add_violation(
                        ViolationType.POSITION_SIZE_EXCEEDED,
                        f"Kelly position {kelly_pct*100:.1f}% exceeds gate limit {config.max_position_pct*100:.0f}%",
                        {
                            'kelly_percentage': str(kelly_pct),
                            'max_position_pct': str(config.max_position_pct),
                            'gate_level': config.level.value
                        }
                    )

            # 7. Add warnings for approaching limits
            if side == 'BUY':
                current_cash = Decimal(str(current_portfolio.get('cash', 0)))
                total_value = Decimal(str(current_portfolio.get('total_value', 1)))
                cash_utilization = Decimal("1") - (current_cash / total_value) if total_value > 0 else Decimal("0")

                warning_threshold = config.cash_floor_pct + Decimal("0.1")
                if cash_utilization > warning_threshold:
                    result.add_warning(
                        f"Approaching cash floor limit: {cash_utilization*100:.1f}% utilization",
                        {'cash_utilization': str(cash_utilization), 'threshold': str(warning_threshold)}
                    )

                if kelly_pct is not None and kelly_pct > config.max_position_pct * Decimal("0.8"):
                    result.add_warning(
                        f"Kelly position {kelly_pct*100:.1f}% approaching gate limit",
                        {'kelly_percentage': str(kelly_pct), 'gate_limit': str(config.max_position_pct)}
                    )

            # Record violation if invalid
            if not result.is_valid:
                for violation in result.violations:
                    self._record_violation(
                        ViolationType(violation['type']),
                        violation['message'],
                        violation.get('details', {})
                    )

            return result

    def _record_violation(
        self,
        violation_type: ViolationType,
        message: str,
        details: Dict[str, Any]
    ):
        """Record a gate violation."""
        violation = ViolationRecord(
            timestamp=datetime.now(),
            gate_level=self.current_gate,
            violation_type=violation_type,
            message=message,
            details=details
        )

        self.violation_history.append(violation)
        self.graduation_metrics.last_violation_date = violation.timestamp

        # Update 30-day violation count
        cutoff_date = datetime.now() - timedelta(days=30)
        self.graduation_metrics.total_violations_30d = len([
            v for v in self.violation_history
            if v.timestamp >= cutoff_date and not v.resolved
        ])

        # Trigger callback
        if self.on_violation:
            self.on_violation(violation)

        self._save_state()
        logger.warning(f"Gate violation recorded: {violation_type.value} - {message}")

    def check_graduation(self, portfolio_metrics: Dict[str, Any]) -> str:
        """
        Check if current gate should be graduated, held, or downgraded.

        Thread-safe: Uses RLock for synchronization.

        Args:
            portfolio_metrics: Dict containing performance metrics
                - sharpe_ratio_30d: Decimal
                - max_drawdown_30d: Decimal
                - avg_cash_utilization_30d: Decimal
                - total_return_30d: Decimal

        Returns:
            str: 'GRADUATE', 'HOLD', or 'DOWNGRADE'
        """
        with self._lock:
            # Update graduation metrics (convert to Decimal)
            sharpe = portfolio_metrics.get('sharpe_ratio_30d')
            self.graduation_metrics.sharpe_ratio_30d = Decimal(str(sharpe)) if sharpe is not None else None
            self.graduation_metrics.max_drawdown_30d = Decimal(str(portfolio_metrics.get('max_drawdown_30d', 0)))
            self.graduation_metrics.avg_cash_utilization_30d = Decimal(str(portfolio_metrics.get('avg_cash_utilization_30d', 0)))

            # Calculate performance score
            performance_score = self._calculate_performance_score(portfolio_metrics)
            self.graduation_metrics.performance_score = performance_score

            # Update consecutive compliant days
            if self.graduation_metrics.last_violation_date:
                days_since_violation = (datetime.now() - self.graduation_metrics.last_violation_date).days
                if days_since_violation >= 1:
                    self.graduation_metrics.consecutive_compliant_days = min(
                        days_since_violation, self.graduation_metrics.consecutive_compliant_days + 1
                    )
            else:
                self.graduation_metrics.consecutive_compliant_days += 1

            current_criteria = self.graduation_criteria.get(self.current_gate)

            # Check for downgrade first
            if (self.graduation_metrics.total_violations_30d > self.downgrade_criteria['max_violations_30d'] or
                performance_score < Decimal(str(self.downgrade_criteria['min_performance_score'])) or
                self.graduation_metrics.max_drawdown_30d > Decimal(str(self.downgrade_criteria['max_drawdown_threshold']))):
                return 'DOWNGRADE'

            # Check for graduation
            if (current_criteria and
                self.graduation_metrics.consecutive_compliant_days >= current_criteria['min_compliant_days'] and
                self.graduation_metrics.total_violations_30d <= current_criteria['max_violations_30d'] and
                performance_score >= Decimal(str(current_criteria['min_performance_score'])) and
                self.current_capital >= Decimal(str(current_criteria['min_capital']))):
                return 'GRADUATE'

            return 'HOLD'

    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> Decimal:
        """Calculate a composite performance score (0-1) using Decimal for precision."""
        score = Decimal("0")

        # Sharpe ratio component (0-0.4)
        sharpe = metrics.get('sharpe_ratio_30d', 0)
        if sharpe is not None:
            sharpe_dec = Decimal(str(sharpe))
            score += min(Decimal("0.4"), max(Decimal("0"), sharpe_dec / 2))

        # Drawdown component (0-0.3)
        max_drawdown = abs(Decimal(str(metrics.get('max_drawdown_30d', 0))))
        if max_drawdown <= Decimal("0.05"):
            score += Decimal("0.3")
        elif max_drawdown <= Decimal("0.10"):
            score += Decimal("0.2")
        elif max_drawdown <= Decimal("0.15"):
            score += Decimal("0.1")

        # Cash utilization component (0-0.2)
        cash_util = Decimal(str(metrics.get('avg_cash_utilization_30d', 0)))
        config = self.get_current_config()
        optimal_util = Decimal("1") - config.cash_floor_pct + Decimal("0.05")

        if abs(cash_util - optimal_util) <= Decimal("0.05"):
            score += Decimal("0.2")
        elif abs(cash_util - optimal_util) <= Decimal("0.10"):
            score += Decimal("0.1")

        # Compliance component (0-0.1)
        if self.graduation_metrics.total_violations_30d == 0:
            score += Decimal("0.1")

        return min(Decimal("1.0"), score)

    def execute_graduation(self) -> bool:
        """Execute graduation to next gate level.

        Thread-safe: Uses RLock for synchronization.
        """
        with self._lock:
            current_level = self.current_gate
            gate_levels = list(GateLevel)
            current_index = gate_levels.index(current_level)

            if current_index >= len(gate_levels) - 1:
                logger.warning(f"Cannot graduate from {current_level.value} - already at maximum")
                return False

            next_gate = gate_levels[current_index + 1]
            if next_gate not in self.gate_configs:
                logger.warning(f"Cannot graduate from {current_level.value} - already at maximum")
                return False

            old_gate = self.current_gate
            self.current_gate = next_gate
            self.graduation_metrics = GraduationMetrics()
            self._save_state()

            if self.on_graduation:
                self.on_graduation(old_gate, next_gate)

            logger.info(f"Successfully graduated from {old_gate.value} to {next_gate.value}")
            return True

    def execute_downgrade(self) -> bool:
        """Execute downgrade to previous gate level.

        Thread-safe: Uses RLock for synchronization.
        """
        with self._lock:
            current_level = self.current_gate
            gate_levels = list(GateLevel)
            current_index = gate_levels.index(current_level)

            if current_index <= 0:
                logger.warning(f"Cannot downgrade from {current_level.value} - already at minimum")
                return False

            prev_gate = gate_levels[current_index - 1]
            if prev_gate not in self.gate_configs:
                logger.warning(f"Cannot downgrade from {current_level.value} - already at minimum")
                return False

            old_gate = self.current_gate
            self.current_gate = prev_gate
            self.graduation_metrics = GraduationMetrics()
            self._save_state()

            if self.on_downgrade:
                self.on_downgrade(old_gate, prev_gate)

            logger.warning(f"Downgraded from {old_gate.value} to {prev_gate.value}")
            return True

    def get_violation_history(self, days: int = 30) -> List[ViolationRecord]:
        """Get violation history for specified number of days.

        Thread-safe: Uses RLock for synchronization.
        """
        with self._lock:
            cutoff_date = datetime.now() - timedelta(days=days)
            return [v for v in self.violation_history if v.timestamp >= cutoff_date]

    def resolve_violation(self, index: int, resolution_note: str = "") -> bool:
        """Mark a violation as resolved.

        Thread-safe: Uses RLock for synchronization.
        """
        with self._lock:
            if not 0 <= index < len(self.violation_history):
                return False

            self.violation_history[index].resolved = True
            self.violation_history[index].resolution_note = resolution_note

            # Update 30-day count
            cutoff_date = datetime.now() - timedelta(days=30)
            self.graduation_metrics.total_violations_30d = len([
                v for v in self.violation_history
                if v.timestamp >= cutoff_date and not v.resolved
            ])

            self._save_state()
            return True

    def get_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report.

        Thread-safe: Uses RLock for synchronization.
        Returns Decimal values as strings for JSON compatibility.
        """
        with self._lock:
            config = self.get_current_config()

            return {
                'current_gate': self.current_gate.value,
                'current_capital': str(self.current_capital),
                'gate_config': {
                    'capital_range': f"${config.capital_min:.0f}-${config.capital_max:.0f}",
                    'allowed_assets': list(config.allowed_assets) if '*' not in config.allowed_assets else ['ALL'],
                    'cash_floor_pct': str(config.cash_floor_pct),
                    'options_enabled': config.options_enabled,
                    'max_theta_pct': str(config.max_theta_pct) if config.max_theta_pct else None,
                    'max_position_pct': str(config.max_position_pct),
                    'description': config.description
                },
                'graduation_metrics': {
                    'consecutive_compliant_days': self.graduation_metrics.consecutive_compliant_days,
                    'total_violations_30d': self.graduation_metrics.total_violations_30d,
                    'performance_score': str(self.graduation_metrics.performance_score),
                    'last_violation': (self.graduation_metrics.last_violation_date.isoformat()
                                     if self.graduation_metrics.last_violation_date else None)
                },
                'recent_violations': len(self.get_violation_history(7)),
                'total_violations': len(self.violation_history)
            }

    def _save_state(self):
        """Save current state to disk.

        Note: Called from within locked methods, so already thread-safe.
        Converts Decimal values to strings for JSON compatibility.
        """
        if not self.data_dir:
            return

        state = {
            'current_gate': self.current_gate.value,
            'current_capital': str(self.current_capital),
            'graduation_metrics': {
                'consecutive_compliant_days': self.graduation_metrics.consecutive_compliant_days,
                'total_violations_30d': self.graduation_metrics.total_violations_30d,
                'avg_cash_utilization_30d': str(self.graduation_metrics.avg_cash_utilization_30d),
                'max_drawdown_30d': str(self.graduation_metrics.max_drawdown_30d),
                'sharpe_ratio_30d': str(self.graduation_metrics.sharpe_ratio_30d) if self.graduation_metrics.sharpe_ratio_30d else None,
                'performance_score': str(self.graduation_metrics.performance_score),
                'last_violation_date': (self.graduation_metrics.last_violation_date.isoformat()
                                      if self.graduation_metrics.last_violation_date else None)
            },
            'violation_history': [
                {
                    'timestamp': v.timestamp.isoformat(),
                    'gate_level': v.gate_level.value,
                    'violation_type': v.violation_type.value,
                    'message': v.message,
                    'details': v.details,
                    'resolved': v.resolved,
                    'resolution_note': v.resolution_note
                }
                for v in self.violation_history
            ]
        }

        state_file = self.data_dir / 'gate_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def _load_state(self):
        """Load state from disk.

        Note: Only called during __init__, so no concurrent access.
        Converts string values back to Decimal for financial precision.
        """
        if not self.data_dir:
            return

        state_file = self.data_dir / 'gate_state.json'

        if not state_file.exists():
            return

        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            self.current_gate = GateLevel(state.get('current_gate', 'G0'))
            # Convert capital back to Decimal
            capital_val = state.get('current_capital', '0')
            self.current_capital = Decimal(str(capital_val))

            # Load graduation metrics (convert strings to Decimal)
            metrics_data = state.get('graduation_metrics', {})
            self.graduation_metrics.consecutive_compliant_days = metrics_data.get('consecutive_compliant_days', 0)
            self.graduation_metrics.total_violations_30d = metrics_data.get('total_violations_30d', 0)
            self.graduation_metrics.avg_cash_utilization_30d = Decimal(str(metrics_data.get('avg_cash_utilization_30d', '0')))
            self.graduation_metrics.max_drawdown_30d = Decimal(str(metrics_data.get('max_drawdown_30d', '0')))
            sharpe_val = metrics_data.get('sharpe_ratio_30d')
            self.graduation_metrics.sharpe_ratio_30d = Decimal(str(sharpe_val)) if sharpe_val else None
            self.graduation_metrics.performance_score = Decimal(str(metrics_data.get('performance_score', '0')))

            last_violation_str = metrics_data.get('last_violation_date')
            if last_violation_str:
                self.graduation_metrics.last_violation_date = datetime.fromisoformat(last_violation_str)

            # Load violation history
            self.violation_history = []
            for v_data in state.get('violation_history', []):
                violation = ViolationRecord(
                    timestamp=datetime.fromisoformat(v_data['timestamp']),
                    gate_level=GateLevel(v_data['gate_level']),
                    violation_type=ViolationType(v_data['violation_type']),
                    message=v_data['message'],
                    details=v_data['details'],
                    resolved=v_data.get('resolved', False),
                    resolution_note=v_data.get('resolution_note')
                )
                self.violation_history.append(violation)

            logger.info(f"Loaded gate state: {self.current_gate.value} with ${self.current_capital:.2f} capital")

        except Exception as e:
            logger.error(f"Error loading gate state: {e}")
