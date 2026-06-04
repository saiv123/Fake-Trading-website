"""Portfolio service.

Builds the portfolio summary by aggregating the holdings ledger lots per ticker (average cost basis,
market value, unrealized P&L), serves paginated transaction history, and applies DRIP toggles. All money
math uses Decimal and is truncated to 2dp.
"""
from collections import defaultdict
from decimal import Decimal

from .. import db
from ..models.holdings_ledger import HoldingLot
from ..models.transaction import Transaction
from ..models.stock import Stock
from ..utils.errors import AppError
from ..utils.fractional import truncate_money

HISTORY_PAGE_SIZE = 50


def get_holdings(user):
    """Aggregate open lots into per-ticker positions (ACB, market value, unrealized P&L) plus account totals."""
    lots = (HoldingLot.query
            .filter(HoldingLot.user_id == user.id, HoldingLot.qty_remaining > 0)
            .all())

    by_ticker = defaultdict(lambda: {'qty': Decimal('0'), 'cost': Decimal('0'), 'drip': False})
    for lot in lots:
        qty = Decimal(str(lot.qty_remaining))
        agg = by_ticker[lot.ticker]
        agg['qty'] += qty
        agg['cost'] += qty * Decimal(str(lot.cost_per_share))
        agg['drip'] = agg['drip'] or lot.drip_enabled

    positions = []
    total_value = Decimal('0')
    total_cost = Decimal('0')
    for ticker, agg in by_ticker.items():
        qty = agg['qty']
        acb = (agg['cost'] / qty) if qty > 0 else Decimal('0')
        stock = Stock.query.get(ticker)
        price = Decimal(str(stock.last_price)) if stock and stock.last_price is not None else acb
        market_value = truncate_money(qty * price)
        unrealized = truncate_money(market_value - agg['cost'])

        total_value += market_value
        total_cost += agg['cost']

        positions.append({
            'ticker':          ticker,
            'shares':          str(qty),
            'acb':             str(truncate_money(acb)),
            'current_price':   str(price),
            'market_value':    str(market_value),
            'cost_basis':      str(truncate_money(agg['cost'])),
            'unrealized_pnl':  str(unrealized),
            'drip_enabled':    agg['drip'],
        })

    return {
        'cash_balance':       str(user.balance),
        'positions':          positions,
        'total_market_value': str(truncate_money(total_value)),
        'total_unrealized':   str(truncate_money(total_value - total_cost)),
        'total_equity':       str(truncate_money(Decimal(str(user.balance)) + total_value)),
    }


def get_history(user, page=1):
    """Return one page of the user's transactions (newest first) with total count for pagination."""
    page = max(1, int(page))
    q = (Transaction.query
         .filter_by(user_id=user.id)
         .order_by(Transaction.executed_at.desc()))
    total = q.count()
    rows = q.offset((page - 1) * HISTORY_PAGE_SIZE).limit(HISTORY_PAGE_SIZE).all()
    return {
        'page':        page,
        'page_size':   HISTORY_PAGE_SIZE,
        'total':       total,
        'transactions': [t.to_dict() for t in rows],
    }


def enable_all_drip(user):
    """Turn DRIP on for every existing lot and set the user's drip_all UI flag."""
    HoldingLot.query.filter_by(user_id=user.id).update({'drip_enabled': True})
    user.drip_all = True
    db.session.commit()


def toggle_drip(user, ticker, enabled):
    """Set DRIP on/off for all of the user's lots of one ticker; 404 if they hold none."""
    updated = (HoldingLot.query
               .filter_by(user_id=user.id, ticker=ticker)
               .update({'drip_enabled': enabled}))
    if not updated:
        raise AppError('No holdings for that ticker', 404)
    db.session.commit()
