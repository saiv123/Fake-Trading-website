# Calculates YTD tax estimates, applies loss harvesting, and runs the April 15th annual settlement —
# deducts from balance or auto-liquidates FIFO positions to cover the bill.
from datetime import datetime, date
from decimal import Decimal

from .. import db
from ..models.transaction import Transaction
from ..models.holdings_ledger import HoldingLot
from ..models.stock import Stock
from ..models.user import User
from ..utils.fractional import truncate_money
from ..utils.state_tax_rates import rate_for
from . import trade_service, notification_service

SHORT_TERM_RATE = Decimal('0.22')
LONG_TERM_RATE  = Decimal('0.15')
DIVIDEND_RATE   = Decimal('0.15')


def compute_liability(user, year: int) -> dict:
    """Core calculation shared by the YTD estimate and the annual settlement."""
    start = datetime(year, 1, 1)
    end   = datetime(year, 12, 31, 23, 59, 59)

    rows = (Transaction.query
            .filter(Transaction.user_id == user.id,
                    Transaction.type.in_(['SELL', 'DIVIDEND_CASH', 'DRIP']),
                    Transaction.executed_at.between(start, end))
            .all())

    net_short = Decimal('0')
    net_long  = Decimal('0')
    dividends = Decimal('0')

    for tx in rows:
        if tx.type == 'SELL':
            net_short += Decimal(str(tx.short_term_gain or 0))
            net_long  += Decimal(str(tx.long_term_gain or 0))
        elif tx.type == 'DIVIDEND_CASH':
            dividends += Decimal(str(tx.total_value or 0))
        elif tx.type == 'DRIP':
            # Gross dividend = shares bought * price + leftover cash credited (total_value)
            gross = Decimal(str(tx.quantity or 0)) * Decimal(str(tx.price_per_share or 0)) + Decimal(str(tx.total_value or 0))
            dividends += gross

    net_short, net_long = _harvest_losses(net_short, net_long)

    taxable_short = max(Decimal('0'), net_short)
    taxable_long  = max(Decimal('0'), net_long)

    federal = (taxable_short * SHORT_TERM_RATE
               + taxable_long * LONG_TERM_RATE
               + dividends * DIVIDEND_RATE)
    total_net = taxable_short + taxable_long + dividends
    state = total_net * rate_for(user.state)

    federal = truncate_money(federal)
    state   = truncate_money(state)

    return {
        'year':            year,
        'net_short_gain':  str(truncate_money(net_short)),
        'net_long_gain':   str(truncate_money(net_long)),
        'dividends':       str(truncate_money(dividends)),
        'taxable_short':   str(truncate_money(taxable_short)),
        'taxable_long':    str(truncate_money(taxable_long)),
        'federal_tax':     str(federal),
        'state_tax':       str(state),
        'state':           user.state,
        'total_tax':       str(truncate_money(federal + state)),
    }


def get_ytd_estimate(user):
    return compute_liability(user, datetime.utcnow().year)


def get_settlement_history(user):
    rows = (Transaction.query
            .filter_by(user_id=user.id, type='TAX_PAYMENT')
            .order_by(Transaction.executed_at.desc())
            .all())
    return [t.to_dict() for t in rows]


# ---- Annual settlement (April 15th, 10:00 AM ET) ----------------------------

def settle_all_users(year: int = None):
    """Settle the prior tax year for every user."""
    year = year or (datetime.utcnow().year - 1)
    for user in User.query.all():
        try:
            settle_user(user, year)
        except Exception:
            db.session.rollback()
            continue


def settle_user(user, year: int):
    liability = compute_liability(user, year)
    owed = Decimal(liability['total_tax'])
    if owed <= 0:
        return

    if Decimal(str(user.balance)) < owed:
        _auto_liquidate(user, owed - Decimal(str(user.balance)))

    paid = min(owed, Decimal(str(user.balance)))  # can't go negative even after liquidation
    user.balance = Decimal(str(user.balance)) - paid

    db.session.add(Transaction(
        user_id=user.id, type='TAX_PAYMENT', total_value=-paid,
        executed_at=datetime.utcnow(),
        notes=(f"{year} tax: federal ${liability['federal_tax']}, "
               f"state ${liability['state_tax']} ({user.state})"),
    ))
    notification_service.create_notification(
        user.id, 'Tax settled', f"{year} tax bill of ${paid} deducted.")
    db.session.commit()


def _auto_liquidate(user, shortfall: Decimal):
    """Sell oldest lots across all tickers (FIFO) until the shortfall is covered."""
    raised = Decimal('0')
    while raised < shortfall:
        lot = (HoldingLot.query
               .filter(HoldingLot.user_id == user.id, HoldingLot.qty_remaining > 0)
               .order_by(HoldingLot.purchased_at.asc())
               .first())
        if not lot:
            break
        stock = Stock.query.get(lot.ticker)
        price = Decimal(str(stock.last_price)) if stock and stock.last_price is not None else Decimal(str(lot.cost_per_share))
        qty = Decimal(str(lot.qty_remaining))
        result = trade_service.execute_sell(user, lot.ticker, qty, price,
                                             note='Auto-liquidation to cover tax bill')
        raised += Decimal(result['proceeds'])


def _harvest_losses(net_short: Decimal, net_long: Decimal):
    """Within-type netting already done by the caller. Cross-offset remaining loss against the other type."""
    if net_short < 0 and net_long > 0:
        applied = min(-net_short, net_long)
        net_short += applied
        net_long  -= applied
    elif net_long < 0 and net_short > 0:
        applied = min(-net_long, net_short)
        net_long  += applied
        net_short -= applied
    # Any remaining net loss is discarded (no carry-forward, per ToS)
    return net_short, net_long
