from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.services import trade_service
from app.utils.errors import AppError
from app.models.holdings_ledger import HoldingLot
from app.models.transaction import Transaction


def test_buy_creates_lot_and_deducts_balance(app, make_user):
    user = make_user(balance=1000)
    trade_service.execute_buy(user, 'AAPL', 10, 50)  # cost 500

    assert Decimal(str(user.balance)) == Decimal('500.00')
    lots = HoldingLot.query.filter_by(user_id=user.id, ticker='AAPL').all()
    assert len(lots) == 1
    assert Decimal(str(lots[0].qty_remaining)) == Decimal('10.00')
    assert lots[0].drip_enabled is False  # new positions always default off

    tx = Transaction.query.filter_by(user_id=user.id, type='BUY').one()
    assert Decimal(str(tx.total_value)) == Decimal('-500.00')


def test_buy_insufficient_balance_raises(app, make_user):
    user = make_user(balance=100)
    with pytest.raises(AppError):
        trade_service.execute_buy(user, 'AAPL', 10, 50)


def test_sell_fifo_consumes_oldest_first(app, make_user):
    user = make_user(balance=10000)
    old = datetime.utcnow() - timedelta(days=10)
    new = datetime.utcnow()
    trade_service.execute_buy(user, 'AAPL', 10, 100, executed_at=old)
    trade_service.execute_buy(user, 'AAPL', 10, 120, executed_at=new)

    # Sell 15 @ 130 → 10 from the $100 lot + 5 from the $120 lot
    result = trade_service.execute_sell(user, 'AAPL', 15, 130)

    # gain = (130-100)*10 + (130-120)*5 = 300 + 50 = 350, all short-term
    assert Decimal(result['short_term_gain']) == Decimal('350.00')

    remaining = HoldingLot.query.filter_by(user_id=user.id, ticker='AAPL').all()
    assert len(remaining) == 1
    assert Decimal(str(remaining[0].qty_remaining)) == Decimal('5.00')


def test_sell_classifies_long_term_holdings(app, make_user):
    user = make_user(balance=10000)
    old = datetime.utcnow() - timedelta(days=400)
    trade_service.execute_buy(user, 'MSFT', 10, 100, executed_at=old)

    result = trade_service.execute_sell(user, 'MSFT', 10, 150)

    assert Decimal(result['long_term_gain']) == Decimal('500.00')
    assert Decimal(result['short_term_gain']) == Decimal('0.00')
    assert result['term'] == 'LONG'


def test_sell_insufficient_shares_raises(app, make_user):
    user = make_user(balance=10000)
    trade_service.execute_buy(user, 'AAPL', 5, 100)
    with pytest.raises(AppError):
        trade_service.execute_sell(user, 'AAPL', 10, 100)
