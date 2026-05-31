# Processes cash, stock, and special dividends on pay date — credits balance or reinvests as DRIP shares,
# inserts DIVIDEND_CASH/DIVIDEND_STOCK/DRIP transactions. ACB is computed on read, so nothing to recompute here.
from datetime import datetime
from decimal import Decimal

from .. import db
from ..models.holdings_ledger import HoldingLot
from ..models.transaction import Transaction
from ..models.stock import Stock
from ..models.user import User
from ..utils.fractional import truncate_shares, truncate_money
from . import notification_service


def process_cash_dividend(ticker, amount_per_share, executed_at=None):
    """Credit cash to every holder; reinvest as shares for positions with DRIP enabled."""
    amount_per_share = Decimal(str(amount_per_share))
    executed_at = executed_at or datetime.utcnow()
    price = _price(ticker)

    for user_id, qty, drip in _positions(ticker):
        cash = truncate_money(amount_per_share * qty)
        if cash <= 0:
            continue
        user = User.query.get(user_id)

        if drip and price and price > 0:
            shares = truncate_shares(cash / price)
            spent = truncate_money(shares * price)
            remainder = cash - spent
            if shares > 0:
                db.session.add(HoldingLot(
                    user_id=user_id, ticker=ticker, qty_remaining=shares,
                    cost_per_share=price, purchased_at=executed_at, drip_enabled=True,
                ))
            user.balance = Decimal(str(user.balance)) + remainder
            db.session.add(Transaction(
                user_id=user_id, ticker=ticker, type='DRIP', quantity=shares,
                price_per_share=price, total_value=remainder, executed_at=executed_at,
                notes=f'Reinvested ${cash} dividend into {shares} shares',
            ))
            notification_service.create_notification(
                user_id, 'Dividend reinvested',
                f'{ticker}: ${cash} dividend reinvested as {shares} shares.', ticker)
        else:
            user.balance = Decimal(str(user.balance)) + cash
            db.session.add(Transaction(
                user_id=user_id, ticker=ticker, type='DIVIDEND_CASH', quantity=qty,
                price_per_share=amount_per_share, total_value=cash, executed_at=executed_at,
                notes=f'Cash dividend ${amount_per_share}/share',
            ))
            notification_service.create_notification(
                user_id, 'Dividend paid', f'{ticker}: ${cash} cash dividend credited.', ticker)

    db.session.commit()


def process_stock_dividend(ticker, ratio, executed_at=None):
    """Add shares directly at the position's current ACB. DRIP toggle does not apply."""
    ratio = Decimal(str(ratio))
    executed_at = executed_at or datetime.utcnow()

    for user_id, qty, _ in _positions(ticker):
        new_shares = truncate_shares(qty * ratio)
        if new_shares <= 0:
            continue
        acb = _acb(user_id, ticker)
        db.session.add(HoldingLot(
            user_id=user_id, ticker=ticker, qty_remaining=new_shares,
            cost_per_share=acb, purchased_at=executed_at, drip_enabled=False,
        ))
        db.session.add(Transaction(
            user_id=user_id, ticker=ticker, type='DIVIDEND_STOCK', quantity=new_shares,
            price_per_share=acb, total_value=Decimal('0'), executed_at=executed_at,
            notes=f'Stock dividend: {new_shares} shares',
        ))
        notification_service.create_notification(
            user_id, 'Stock dividend', f'{ticker}: received {new_shares} additional shares.', ticker)

    db.session.commit()


# ---- Helpers -----------------------------------------------------------------

def _positions(ticker):
    """Yield (user_id, total_qty, drip_enabled) per holder of the ticker."""
    rows = (db.session.query(
                HoldingLot.user_id,
                db.func.sum(HoldingLot.qty_remaining),
                db.func.max(db.cast(HoldingLot.drip_enabled, db.Integer)))
            .filter(HoldingLot.ticker == ticker, HoldingLot.qty_remaining > 0)
            .group_by(HoldingLot.user_id)
            .all())
    for user_id, qty, drip in rows:
        yield user_id, Decimal(str(qty)), bool(drip)


def _acb(user_id, ticker) -> Decimal:
    qty, cost = Decimal('0'), Decimal('0')
    for lot in HoldingLot.query.filter_by(user_id=user_id, ticker=ticker).all():
        q = Decimal(str(lot.qty_remaining))
        qty += q
        cost += q * Decimal(str(lot.cost_per_share))
    return (cost / qty) if qty > 0 else Decimal('0')


def _price(ticker):
    stock = Stock.query.get(ticker)
    return Decimal(str(stock.last_price)) if stock and stock.last_price is not None else None
