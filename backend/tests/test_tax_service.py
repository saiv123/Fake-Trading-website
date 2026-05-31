from datetime import datetime
from decimal import Decimal

from app import db
from app.services import trade_service, tax_service
from app.models.transaction import Transaction
from app.models.holdings_ledger import HoldingLot


def _add_sell(user, short=0, long=0, when=None):
    db.session.add(Transaction(
        user_id=user.id, ticker='X', type='SELL', quantity=Decimal('1'),
        total_value=Decimal('0'),
        short_term_gain=Decimal(str(short)), long_term_gain=Decimal(str(long)),
        term='SHORT', executed_at=when or datetime.utcnow(),
    ))
    db.session.commit()


def test_short_term_gain_taxed_at_22_percent(app, make_user):
    user = make_user(state='TX')  # no state tax → isolates federal
    _add_sell(user, short=1000)

    liab = tax_service.compute_liability(user, datetime.utcnow().year)
    assert Decimal(liab['federal_tax']) == Decimal('220.00')
    assert Decimal(liab['state_tax']) == Decimal('0.00')
    assert Decimal(liab['total_tax']) == Decimal('220.00')


def test_dividends_taxed_at_15_percent(app, make_user):
    user = make_user(state='TX')
    db.session.add(Transaction(
        user_id=user.id, ticker='X', type='DIVIDEND_CASH', quantity=Decimal('10'),
        price_per_share=Decimal('1'), total_value=Decimal('100'),
        executed_at=datetime.utcnow(),
    ))
    db.session.commit()

    liab = tax_service.compute_liability(user, datetime.utcnow().year)
    assert Decimal(liab['dividends']) == Decimal('100.00')
    assert Decimal(liab['federal_tax']) == Decimal('15.00')


def test_loss_harvesting_cross_offsets(app, make_user):
    user = make_user(state='TX')
    _add_sell(user, short=-500)
    _add_sell(user, long=1000)

    liab = tax_service.compute_liability(user, datetime.utcnow().year)
    # short loss of 500 offsets long gain → net long 500, taxed at 15% = 75
    assert Decimal(liab['net_long_gain']) == Decimal('500.00')
    assert Decimal(liab['taxable_short']) == Decimal('0.00')
    assert Decimal(liab['federal_tax']) == Decimal('75.00')


def test_excess_losses_yield_no_tax(app, make_user):
    user = make_user(state='CA')
    _add_sell(user, short=-2000)
    _add_sell(user, long=1000)

    liab = tax_service.compute_liability(user, datetime.utcnow().year)
    assert Decimal(liab['total_tax']) == Decimal('0.00')


def test_settle_user_deducts_balance(app, make_user):
    prev = datetime.utcnow().year - 1
    user = make_user(balance=10000, state='TX')
    _add_sell(user, short=1000, when=datetime(prev, 6, 1))

    tax_service.settle_user(user, prev)

    assert Decimal(str(user.balance)) == Decimal('9780.00')  # 10000 - 220
    pay = Transaction.query.filter_by(user_id=user.id, type='TAX_PAYMENT').one()
    assert Decimal(str(pay.total_value)) == Decimal('-220.00')


def test_settle_auto_liquidates_when_short_on_cash(app, make_user, make_stock):
    prev = datetime.utcnow().year - 1
    user = make_user(balance=0, state='TX')
    make_stock('AAPL', 100)
    db.session.add(HoldingLot(
        user_id=user.id, ticker='AAPL', qty_remaining=Decimal('10'),
        cost_per_share=Decimal('50'), purchased_at=datetime(prev, 1, 2),
    ))
    _add_sell(user, short=1000, when=datetime(prev, 6, 1))  # owes 220, has no cash

    tax_service.settle_user(user, prev)

    # Auto-liquidation sells 10 @ 100 = 1000, then 220 tax is deducted → 780
    assert Decimal(str(user.balance)) == Decimal('780.00')
    assert HoldingLot.query.filter_by(user_id=user.id, ticker='AAPL').count() == 0
