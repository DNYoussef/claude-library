"""
Tests for Money class - CRITICAL: Ensures float rejection works.

Run with: pytest library/patterns/money-handling/tests/
"""

import pytest
from decimal import Decimal
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from money import Money, FloatNotAllowedError, CurrencyMismatchError


class TestMoneyConstruction:
    """Test Money object creation."""

    def test_from_decimal(self):
        """Valid: Create from Decimal."""
        m = Money(Decimal("19.99"))
        assert m.amount == Decimal("19.99")
        assert m.currency == "USD"

    def test_from_string(self):
        """Valid: Create from string."""
        m = Money("19.99")
        assert m.amount == Decimal("19.99")

    def test_from_int(self):
        """Valid: Create from integer."""
        m = Money(100)
        assert m.amount == Decimal("100")

    def test_from_cents(self):
        """Valid: Create from cents."""
        m = Money.from_cents(1999)
        assert m.amount == Decimal("19.99")

    def test_from_string_classmethod(self):
        """Valid: Use from_string classmethod."""
        m = Money.from_string("123.45", "EUR")
        assert m.amount == Decimal("123.45")
        assert m.currency == "EUR"

    def test_zero(self):
        """Valid: Create zero value."""
        m = Money.zero("USD")
        assert m.amount == Decimal("0")

    def test_rejects_float_construction(self):
        """CRITICAL: Must reject float in constructor."""
        with pytest.raises(FloatNotAllowedError):
            Money(19.99)  # This MUST fail!

    def test_rejects_float_with_clear_message(self):
        """Verify error message guides user to correct usage."""
        with pytest.raises(FloatNotAllowedError) as exc_info:
            Money(19.99)
        assert "Decimal" in str(exc_info.value)
        assert "NOT float" in str(exc_info.value)

    def test_currency_uppercase(self):
        """Currency codes are normalized to uppercase."""
        m = Money("100", "usd")
        assert m.currency == "USD"


class TestMoneyArithmetic:
    """Test arithmetic operations."""

    def test_addition(self):
        """Add two Money values."""
        a = Money("10.00")
        b = Money("5.50")
        assert (a + b).amount == Decimal("15.50")

    def test_subtraction(self):
        """Subtract two Money values."""
        a = Money("10.00")
        b = Money("3.50")
        assert (a - b).amount == Decimal("6.50")

    def test_multiplication_by_int(self):
        """Multiply by integer."""
        m = Money("10.00")
        assert (m * 3).amount == Decimal("30.00")

    def test_multiplication_by_decimal(self):
        """Multiply by Decimal."""
        m = Money("10.00")
        assert (m * Decimal("1.5")).amount == Decimal("15.00")

    def test_rejects_float_multiplication(self):
        """CRITICAL: Must reject float in multiplication."""
        m = Money("100.00")
        with pytest.raises(FloatNotAllowedError):
            m * 1.5  # This MUST fail!

    def test_rejects_float_division(self):
        """CRITICAL: Must reject float in division."""
        m = Money("100.00")
        with pytest.raises(FloatNotAllowedError):
            m / 2.0  # This MUST fail!

    def test_division_by_int(self):
        """Divide by integer."""
        m = Money("100.00")
        assert (m / 2).amount == Decimal("50.00")

    def test_division_by_decimal(self):
        """Divide by Decimal."""
        m = Money("100.00")
        assert (m / Decimal("4")).amount == Decimal("25.00")

    def test_division_by_zero(self):
        """Division by zero raises error."""
        m = Money("100.00")
        with pytest.raises(ZeroDivisionError):
            m / 0

    def test_negation(self):
        """Negate a Money value."""
        m = Money("50.00")
        assert (-m).amount == Decimal("-50.00")

    def test_absolute(self):
        """Absolute value."""
        m = Money("-50.00")
        assert abs(m).amount == Decimal("50.00")

    def test_sum_builtin(self):
        """sum() works with Money."""
        values = [Money("10.00"), Money("20.00"), Money("30.00")]
        total = sum(values)
        assert total.amount == Decimal("60.00")


class TestMoneyCurrency:
    """Test currency handling."""

    def test_currency_mismatch_addition(self):
        """Cannot add different currencies."""
        usd = Money("100", "USD")
        eur = Money("100", "EUR")
        with pytest.raises(CurrencyMismatchError):
            usd + eur

    def test_currency_mismatch_subtraction(self):
        """Cannot subtract different currencies."""
        usd = Money("100", "USD")
        eur = Money("100", "EUR")
        with pytest.raises(CurrencyMismatchError):
            usd - eur

    def test_currency_mismatch_comparison(self):
        """Cannot compare different currencies."""
        usd = Money("100", "USD")
        eur = Money("100", "EUR")
        with pytest.raises(CurrencyMismatchError):
            usd < eur


class TestMoneyComparison:
    """Test comparison operations."""

    def test_equality(self):
        """Equal values are equal."""
        a = Money("10.00")
        b = Money("10.00")
        assert a == b

    def test_inequality(self):
        """Different values are not equal."""
        a = Money("10.00")
        b = Money("20.00")
        assert a != b

    def test_less_than(self):
        """Less than comparison."""
        a = Money("10.00")
        b = Money("20.00")
        assert a < b

    def test_greater_than(self):
        """Greater than comparison."""
        a = Money("20.00")
        b = Money("10.00")
        assert a > b

    def test_less_than_or_equal(self):
        """Less than or equal comparison."""
        a = Money("10.00")
        b = Money("10.00")
        assert a <= b

    def test_greater_than_or_equal(self):
        """Greater than or equal comparison."""
        a = Money("10.00")
        b = Money("10.00")
        assert a >= b


class TestMoneyRounding:
    """Test rounding operations."""

    def test_round_to_cents(self):
        """Round to 2 decimal places."""
        m = Money("10.999")
        assert m.round_to_cents().amount == Decimal("11.00")

    def test_bankers_rounding(self):
        """Uses banker's rounding (round half to even)."""
        # 10.125 rounds to 10.12 (even)
        # 10.135 rounds to 10.14 (even)
        m1 = Money("10.125")
        m2 = Money("10.135")
        assert m1.round(2).amount == Decimal("10.12")
        assert m2.round(2).amount == Decimal("10.14")


class TestMoneyConversion:
    """Test type conversion methods."""

    def test_to_decimal(self):
        """Convert to Decimal."""
        m = Money("19.99")
        assert m.to_decimal() == Decimal("19.99")
        assert isinstance(m.to_decimal(), Decimal)

    def test_to_cents(self):
        """Convert to integer cents."""
        m = Money("19.99")
        assert m.to_cents() == 1999
        assert isinstance(m.to_cents(), int)

    def test_to_float(self):
        """Convert to float (for external APIs)."""
        m = Money("19.99")
        assert m.to_float() == 19.99
        assert isinstance(m.to_float(), float)


class TestMoneyRepresentation:
    """Test string representations."""

    def test_str_usd(self):
        """String format for USD."""
        m = Money("1234.56", "USD")
        assert str(m) == "$1,234.56"

    def test_str_eur(self):
        """String format for EUR."""
        m = Money("1234.56", "EUR")
        assert str(m) == "1,234.56 EUR"

    def test_repr(self):
        """Debug representation."""
        m = Money("19.99", "USD")
        assert "Money" in repr(m)
        assert "19.99" in repr(m)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_amount(self):
        """Handle very small amounts."""
        m = Money("0.01")
        assert m.amount == Decimal("0.01")

    def test_very_large_amount(self):
        """Handle very large amounts."""
        m = Money("999999999999.99")
        assert m.amount == Decimal("999999999999.99")

    def test_negative_amount(self):
        """Handle negative amounts."""
        m = Money("-100.50")
        assert m.amount == Decimal("-100.50")

    def test_zero_comparison(self):
        """Zero equals zero."""
        z1 = Money.zero()
        z2 = Money("0")
        assert z1 == z2

    def test_immutability(self):
        """Money values are immutable."""
        m = Money("100.00")
        with pytest.raises(AttributeError):
            m.amount = Decimal("200.00")

    def test_hashable(self):
        """Money can be used in sets and dicts."""
        m1 = Money("100.00")
        m2 = Money("100.00")
        s = {m1, m2}
        assert len(s) == 1  # Same value = same hash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
