from decimal import Decimal

from app.utils.state_tax_rates import rate_for


def test_known_state_rate():
    assert rate_for('CA') == Decimal('0.093')


def test_no_income_tax_states_are_zero():
    for state in ('TX', 'FL', 'WA', 'NV', 'WY', 'SD', 'AK', 'TN', 'NH'):
        assert rate_for(state) == Decimal('0.00')


def test_lookup_is_case_insensitive():
    assert rate_for('ny') == rate_for('NY')


def test_unknown_state_falls_back_to_default():
    assert rate_for('ZZ') == Decimal('0.05')
