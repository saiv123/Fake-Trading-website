from decimal import Decimal

from app.services import trade_service, portfolio_service
from app.models.holdings_ledger import HoldingLot


def test_holdings_report_acb_and_unrealized_pnl(app, make_user, make_stock):
    user = make_user(balance=10000)
    make_stock('AAPL', 120)
    trade_service.execute_buy(user, 'AAPL', 10, 100)
    trade_service.execute_buy(user, 'AAPL', 10, 110)

    data = portfolio_service.get_holdings(user)
    pos = next(p for p in data['positions'] if p['ticker'] == 'AAPL')

    assert Decimal(pos['shares']) == Decimal('20.00')
    assert Decimal(pos['acb']) == Decimal('105.00')          # (1000 + 1100) / 20
    assert Decimal(pos['current_price']) == Decimal('120.0000')
    # market value 20*120 = 2400, cost 2100 → unrealized 300
    assert Decimal(pos['unrealized_pnl']) == Decimal('300.00')


def test_enable_all_drip_flips_every_lot(app, make_user, make_stock):
    user = make_user(balance=10000)
    make_stock('AAPL', 100)
    trade_service.execute_buy(user, 'AAPL', 10, 100)
    trade_service.execute_buy(user, 'AAPL', 5, 100)

    portfolio_service.enable_all_drip(user)

    lots = HoldingLot.query.filter_by(user_id=user.id).all()
    assert all(lot.drip_enabled for lot in lots)
    assert user.drip_all is True


def test_toggle_drip_for_single_ticker(app, make_user, make_stock):
    user = make_user(balance=10000)
    make_stock('AAPL', 100)
    make_stock('MSFT', 200)
    trade_service.execute_buy(user, 'AAPL', 10, 100)
    trade_service.execute_buy(user, 'MSFT', 1, 200)

    portfolio_service.toggle_drip(user, 'AAPL', True)

    aapl = HoldingLot.query.filter_by(user_id=user.id, ticker='AAPL').all()
    msft = HoldingLot.query.filter_by(user_id=user.id, ticker='MSFT').all()
    assert all(lot.drip_enabled for lot in aapl)
    assert all(not lot.drip_enabled for lot in msft)
