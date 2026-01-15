"""
Library Integration Test

Verifies that all library components can be imported and basic functionality works.
Run from library root: python test_integration.py
"""

import sys
import os
from pathlib import Path

# Add library to path
library_root = Path(__file__).parent
sys.path.insert(0, str(library_root))

def test_common_types():
    """Test common/types.py imports and works"""
    print("Testing common/types.py...")
    from common.types import (
        Severity,
        Money,
        Violation,
        ValidationResult,
        QualityResult,
        TaggedEntry,
        FloatNotAllowedError
    )

    # Test Severity enum
    assert Severity.CRITICAL.value == "critical"
    assert Severity.HIGH.value == "high"

    # Test Money with Decimal
    from decimal import Decimal
    money = Money(amount=Decimal("100.50"), currency="USD")
    assert money.amount == Decimal("100.50")

    # Test FloatNotAllowedError
    try:
        bad_money = Money(amount=1.5, currency="USD")  # type: ignore
        raise AssertionError("Should have raised FloatNotAllowedError")
    except FloatNotAllowedError:
        pass  # Expected

    print("  PASS: common/types.py")


def test_trading_components():
    """Test trading component imports"""
    print("Testing trading components...")

    # Circuit breakers
    sys.path.insert(0, str(library_root / "components" / "trading" / "circuit_breakers"))
    from trading_breakers import TradingCircuitBreakers, TradingBreakerConfig
    print("  PASS: circuit_breakers")

    # Gate system
    sys.path.insert(0, str(library_root / "components" / "trading" / "gate_system"))
    from gate_manager import GateManager, GateConfig, GateLevel
    print("  PASS: gate_system")

    # Kelly criterion
    sys.path.insert(0, str(library_root / "components" / "trading" / "position_sizing"))
    from kelly_criterion import KellyCriterion, KellyResult
    from decimal import Decimal

    kelly = KellyCriterion()
    result = kelly.calculate(
        win_probability=Decimal("0.55"),
        win_loss_ratio=Decimal("1.5")
    )
    assert isinstance(result, KellyResult)
    print("  PASS: position_sizing")

    return None


def test_pattern_components():
    """Test pattern component imports"""
    print("Testing pattern components...")

    # Auditor base
    sys.path.insert(0, str(library_root / "components" / "patterns" / "auditor_base"))
    from auditor_base import BaseAuditor, AuditorResult, ActionClass
    assert ActionClass.ACCEPT.value == "ACCEPT"
    print("  PASS: auditor_base")

    # Pattern matcher
    sys.path.insert(0, str(library_root / "components" / "analysis" / "pattern_matcher"))
    from pattern_matcher import PatternMatcher, PatternDatabase, SignalLevel

    db = PatternDatabase()
    db.add_word("test", weight=1.0)
    matcher = PatternMatcher(db)
    result = matcher.analyze("This is a test string")
    assert result.score > 0
    print("  PASS: pattern_matcher")

    return None


def test_validation_components():
    """Test validation component imports"""
    print("Testing validation components...")

    # Quality validator
    sys.path.insert(0, str(library_root / "components" / "validation" / "quality_validator"))
    from quality_validator import QualityValidator, QualityValidationResult, Violation

    validator = QualityValidator()
    validator.add_violation(
        rule_id="TEST-001",
        message="Test violation",
        file="test.py",
        line=1,
        severity="medium"
    )
    result = validator.analyze()
    assert len(result.violations) == 1
    print("  PASS: quality_validator")

    return None


def test_analysis_components():
    """Test analysis component imports"""
    print("Testing analysis components...")

    # AST visitor base
    sys.path.insert(0, str(library_root / "components" / "analysis" / "ast_visitor_base"))
    from visitor_base import (
        BaseConnascenceVisitor,
        VisitorContext,
        MagicLiteralVisitor,
        ComplexityVisitor
    )

    import ast
    code = "x = 42"
    tree = ast.parse(code)
    visitor = MagicLiteralVisitor()
    context = VisitorContext(file_path="test.py", source_code=code)
    violations = visitor.visit_with_context(tree, context)
    assert len(violations) == 1  # Magic literal 42 detected
    print("  PASS: ast_visitor_base")

    return None


def test_observability_components():
    """Test observability component imports"""
    print("Testing observability components...")

    # Tagging protocol
    sys.path.insert(0, str(library_root / "components" / "observability" / "tagging_protocol"))
    from tagging_protocol import TaggingProtocol, Intent, AgentCategory, create_simple_tagger

    tagger = create_simple_tagger("test-agent", "test-project")
    tags = tagger.generate_tags(Intent.TESTING)
    assert tags["who"]["agent_id"] == "test-agent"
    assert tags["why"]["intent"] == "testing"
    print("  PASS: tagging_protocol")

    return None


def test_security_components():
    """Test security component imports"""
    print("Testing security components...")

    # JWT auth
    sys.path.insert(0, str(library_root / "components" / "security" / "jwt_auth"))
    from jwt_auth import JWTAuth, JWTConfig, generate_secure_token

    # Generate a secure enough key for testing
    test_key = generate_secure_token(32)
    auth = JWTAuth(JWTConfig(secret_key=test_key))

    # Test token creation
    token = auth.create_access_token({"sub": "test-user"})
    assert token is not None

    # Test token verification
    payload = auth.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "test-user"

    # Test refresh token
    refresh = auth.create_refresh_token({"sub": "test-user"})
    new_access = auth.refresh_access_token(refresh)
    assert new_access is not None

    print("  PASS: jwt_auth")

    return None


def main():
    """Run all integration tests"""
    print("=" * 60)
    print("Library Integration Test Suite")
    print("=" * 60)
    print()

    tests = [
        ("Common Types", test_common_types),
        ("Trading Components", test_trading_components),
        ("Pattern Components", test_pattern_components),
        ("Validation Components", test_validation_components),
        ("Analysis Components", test_analysis_components),
        ("Observability Components", test_observability_components),
        ("Security Components", test_security_components),
    ]

    passed = 0
    failed = 0
    errors = []

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append((name, str(e)))
            print(f"  FAIL: {name} - {e}")

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if errors:
        print("\nErrors:")
        for name, error in errors:
            print(f"  - {name}: {error}")
        return 1

    print("\nAll integration tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
