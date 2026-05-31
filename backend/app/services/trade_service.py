# Core BUY/SELL execution — validates balance/holdings, applies FIFO lot consumption, calculates realized gains,
# and atomically updates users.balance, holdings_ledger, and transactions. Callers pass an already-resolved fill price.
from datetime import datetime
from decimal import Decimal

from .. import db
from ..models.holdings_ledger import HoldingLot
from ..models.transaction import Transaction
from ..utils.errors import AppError
from ..utils.fractional import truncate_shares, truncate_money

LONG_TERM_DAYS = 365


def execute_buy(user, ticker, quantity, fill_price, executed_at=None, note=None):
    """Deduct cash, open a new tax lot, log a BUY. Atomic. Returns the created lot."""
    quantity   = truncate_shares(quantity)
    fill_price = Decimal(str(fill_price))
    executed_at = executed_at or datetime.utcnow()

    if quantity <= 0:
        raise AppError('Quantity must be positive')

    cost = truncate_money(quantity * fill_price)
    if Decimal(str(user.balance)) < cost:
        raise AppError('Insufficient balance', 402)

    try:
        user.balance = Decimal(str(user.balance)) - cost
        lot = HoldingLot(
            user_id=user.id,
            ticker=ticker,
            qty_remaining=quantity,
            cost_per_share=fill_price,
            purchased_at=executed_at,
            drip_enabled=False,   # new positions always default to off, even if drip_all is set (per ToS)
        )
        db.session.add(lot)
        db.session.add(Transaction(
            user_id=user.id,
            ticker=ticker,
            type='BUY',
            quantity=quantity,
            price_per_share=fill_price,
            total_value=-cost,
            executed_at=executed_at,
            notes=note,
        ))
        db.session.commit()
        return lot
    except Exception:
        db.session.rollback()
        raise


def execute_sell(user, ticker, quantity, fill_price, executed_at=None, note=None):
    """Consume oldest lots first (FIFO), realize gains by term, credit cash, log a SELL. Atomic."""
    quantity   = truncate_shares(quantity)
    fill_price = Decimal(str(fill_price))
    executed_at = executed_at or datetime.utcnow()

    if quantity <= 0:
        raise AppError('Quantity must be positive')

    lots = (HoldingLot.query
            .filter(HoldingLot.user_id == user.id,
                    HoldingLot.ticker == ticker,
                    HoldingLot.qty_remaining > 0)
            .order_by(HoldingLot.purchased_at.asc())
            .all())

    held = sum(Decimal(str(l.qty_remaining)) for l in lots)
    if held < quantity:
        raise AppError('Insufficient shares held', 422)

    remaining = quantity
    proceeds = Decimal('0')
    short_gain = Decimal('0')
    long_gain = Decimal('0')
    lot_details = []

    try:
        for lot in lots:
            if remaining <= 0:
                break
            lot_qty = Decimal(str(lot.qty_remaining))
            take = min(lot_qty, remaining)

            cost_basis = Decimal(str(lot.cost_per_share))
            lot_proceeds = take * fill_price
            gain = (fill_price - cost_basis) * take
            proceeds += lot_proceeds

            days_held = (executed_at - lot.purchased_at).days
            is_long = days_held >= LONG_TERM_DAYS
            if is_long:
                long_gain += gain
            else:
                short_gain += gain

            lot_details.append({
                'lot_id':         lot.lot_id,
                'qty':            str(take),
                'cost_per_share': str(cost_basis),
                'proceeds':       str(truncate_money(lot_proceeds)),
                'gain':           str(truncate_money(gain)),
                'term':           'LONG' if is_long else 'SHORT',
                'days_held':      days_held,
            })

            new_qty = lot_qty - take
            if new_qty <= 0:
                db.session.delete(lot)
            else:
                lot.qty_remaining = new_qty
            remaining -= take

        proceeds = truncate_money(proceeds)
        user.balance = Decimal(str(user.balance)) + proceeds

        if short_gain != 0 and long_gain != 0:
            term = 'MIXED'
        elif long_gain != 0:
            term = 'LONG'
        else:
            term = 'SHORT'

        db.session.add(Transaction(
            user_id=user.id,
            ticker=ticker,
            type='SELL',
            quantity=quantity,
            price_per_share=fill_price,
            total_value=proceeds,
            short_term_gain=truncate_money(short_gain),
            long_term_gain=truncate_money(long_gain),
            term=term,
            lot_details=lot_details,
            executed_at=executed_at,
            notes=note,
        ))
        db.session.commit()
        return {'proceeds': str(proceeds), 'term': term,
                'short_term_gain': str(truncate_money(short_gain)),
                'long_term_gain': str(truncate_money(long_gain))}
    except AppError:
        db.session.rollback()
        raise
    except Exception:
        db.session.rollback()
        raise


def shares_held(user_id, ticker) -> Decimal:
    total = (db.session.query(db.func.coalesce(db.func.sum(HoldingLot.qty_remaining), 0))
             .filter(HoldingLot.user_id == user_id, HoldingLot.ticker == ticker)
             .scalar())
    return Decimal(str(total or 0))
