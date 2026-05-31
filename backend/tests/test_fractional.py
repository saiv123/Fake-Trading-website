from decimal import Decimal

from app.utils.fractional import truncate_shares, truncate_money, to_price


def test_truncate_shares_floors_never_rounds_up():
    assert truncate_shares('0.129') == Decimal('0.12')
    assert truncate_shares('0.999') == Decimal('0.99')
    assert truncate_shares('5') == Decimal('5.00')


def test_truncate_shares_does_not_round_half_up():
    assert truncate_shares('0.125') == Decimal('0.12')


def test_truncate_money_floors_to_two_places():
    assert truncate_money('99.999') == Decimal('99.99')
    assert truncate_money('10.001') == Decimal('10.00')


def test_to_price_keeps_four_places():
    assert to_price('1.23456') == Decimal('1.2345')
