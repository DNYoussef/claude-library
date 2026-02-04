"""
Claude Library Components

Canonical exports for copy-paste use. Import commonly used components from here.

Usage:
    from library.components import Severity, Money, Violation
    from library.components import PatternMatcher, ViolationFactory
    from library.components import CircuitBreaker, GateManager

Note: This module uses lazy imports to avoid issues when components
directory is used as a test root. Imports are attempted on first access.
"""

# Lazy import flag - imports done on first access to __all__ items
_IMPORTS_DONE = False

# Placeholders for exports
Severity = None
Money = None
Violation = None
ValidationResult = None
QualityResult = None
TaggedEntry = None
ConfidenceLevel = None
InputContract = None
OutputContract = None
PatternMatcher = None
ViolationFactory = None
Location = None
ScoringAggregator = None
MetricCollector = None
CircuitBreaker = None
CircuitBreakerManager = None
GateManager = None
KellyCriterion = None
QualityValidator = None
SpecValidator = None
TaggingProtocol = None
Intent = None
AgentCategory = None
create_tagger = None
SkillBase = None
AgentBase = None
VerixParser = None
GenericCircuitBreaker = None
QualityGate = None


def _do_imports():
    """Perform actual imports. Called lazily."""
    global _IMPORTS_DONE
    global Severity, Money, Violation, ValidationResult, QualityResult
    global TaggedEntry, ConfidenceLevel, InputContract, OutputContract
    global PatternMatcher, ViolationFactory, Location, ScoringAggregator, MetricCollector
    global CircuitBreaker, CircuitBreakerManager, GateManager, KellyCriterion
    global QualityValidator, SpecValidator
    global TaggingProtocol, Intent, AgentCategory, create_tagger
    global SkillBase, AgentBase, VerixParser
    global GenericCircuitBreaker, QualityGate

    if _IMPORTS_DONE:
        return

    try:
        # Try library-prefixed import first (when installed as package)
        from library.common.types import (
            Severity as _Severity,
            Money as _Money,
            Violation as _Violation,
            ValidationResult as _ValidationResult,
            QualityResult as _QualityResult,
            TaggedEntry as _TaggedEntry,
            ConfidenceLevel as _ConfidenceLevel,
            InputContract as _InputContract,
            OutputContract as _OutputContract,
        )
        Severity = _Severity
        Money = _Money
        Violation = _Violation
        ValidationResult = _ValidationResult
        QualityResult = _QualityResult
        TaggedEntry = _TaggedEntry
        ConfidenceLevel = _ConfidenceLevel
        InputContract = _InputContract
        OutputContract = _OutputContract
    except ImportError:
        try:
            # Try relative import (when used as subpackage)
            from ..common.types import (
                Severity as _Severity,
                Money as _Money,
                Violation as _Violation,
                ValidationResult as _ValidationResult,
                QualityResult as _QualityResult,
                TaggedEntry as _TaggedEntry,
                ConfidenceLevel as _ConfidenceLevel,
                InputContract as _InputContract,
                OutputContract as _OutputContract,
            )
            Severity = _Severity
            Money = _Money
            Violation = _Violation
            ValidationResult = _ValidationResult
            QualityResult = _QualityResult
            TaggedEntry = _TaggedEntry
            ConfidenceLevel = _ConfidenceLevel
            InputContract = _InputContract
            OutputContract = _OutputContract
        except ImportError:
            pass  # Types not available

    try:
        from .analysis.pattern_matcher.pattern_matcher import PatternMatcher as _PM
        from .analysis.violation_factory.violation_factory import ViolationFactory as _VF, Location as _Loc
        from .analysis.scoring_aggregator.scoring_aggregator import ScoringAggregator as _SA
        from .analysis.metric_collector.metric_collector import MetricCollector as _MC
        PatternMatcher = _PM
        ViolationFactory = _VF
        Location = _Loc
        ScoringAggregator = _SA
        MetricCollector = _MC
    except ImportError:
        pass

    try:
        from .trading.circuit_breakers.circuit_breaker import CircuitBreaker as _CB, CircuitBreakerManager as _CBM
        from .trading.gate_system.gate_manager import GateManager as _GM
        from .trading.position_sizing.kelly import KellyCriterion as _KC
        CircuitBreaker = _CB
        CircuitBreakerManager = _CBM
        GateManager = _GM
        KellyCriterion = _KC
    except ImportError:
        pass

    try:
        from .validation.quality_validator.quality_validator import QualityValidator as _QV
        from .validation.spec_validation.spec_validation import SpecValidator as _SV
        QualityValidator = _QV
        SpecValidator = _SV
    except ImportError:
        pass

    try:
        from .observability.tagging_protocol.tagging_protocol import (
            TaggingProtocol as _TP,
            Intent as _Int,
            AgentCategory as _AC,
            create_tagger as _ct,
        )
        TaggingProtocol = _TP
        Intent = _Int
        AgentCategory = _AC
        create_tagger = _ct
    except ImportError:
        pass

    try:
        from .cognitive.skill_base.skill_base import SkillBase as _SB
        from .cognitive.agent_base.agent_base import AgentBase as _AB
        from .cognitive.verix_parser.verix_parser import VerixParser as _VP
        SkillBase = _SB
        AgentBase = _AB
        VerixParser = _VP
    except ImportError:
        pass

    try:
        from .utilities.circuit_breaker.circuit_breaker import CircuitBreaker as _GCB
        from .utilities.quality_gate.quality_gate import QualityGate as _QG
        GenericCircuitBreaker = _GCB
        QualityGate = _QG
    except ImportError:
        pass

    _IMPORTS_DONE = True


def __getattr__(name):
    """Lazy import on attribute access."""
    _do_imports()
    if name in __all__:
        return globals().get(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Types
    "Severity",
    "Money",
    "Violation",
    "ValidationResult",
    "QualityResult",
    "TaggedEntry",
    "ConfidenceLevel",
    "InputContract",
    "OutputContract",
    # Analysis
    "PatternMatcher",
    "ViolationFactory",
    "Location",
    "ScoringAggregator",
    "MetricCollector",
    # Trading
    "CircuitBreaker",
    "CircuitBreakerManager",
    "GateManager",
    "KellyCriterion",
    # Validation
    "QualityValidator",
    "SpecValidator",
    # Observability
    "TaggingProtocol",
    "Intent",
    "AgentCategory",
    "create_tagger",
    # Cognitive
    "SkillBase",
    "AgentBase",
    "VerixParser",
    # Utilities
    "GenericCircuitBreaker",
    "QualityGate",
]
