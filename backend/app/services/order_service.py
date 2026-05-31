# Manages the order lifecycle — validates and queues incoming orders; the hourly check does SELECT DISTINCT ticker FROM
# pending_orders, batch-fetches prices, then applies the slippage model across all matching orders; expires unfilled orders at market close.
from datetime import datetime, timedelta
from decimal import Decimal

from .. import db
from ..models.order import Order
from ..models.pending_order import PendingOrder
from ..models.stock import Stock
from ..utils.errors import AppError
from ..utils import market_hours, slippage
from ..utils.fractional import truncate_shares
from . import trade_service, stock_service

MAX_DURATION = timedelta(hours=6)


def place_order(user, ticker, direction, order_type, quantity,
                limit_price=None, stop_price=None):
    quantity = truncate_shares(quantity)
    if quantity <= 0:
        raise AppError('Quantity must be positive')

    _validate_affordability(user, ticker, direction, order_type, quantity, limit_price)

    # Market order during trading hours fills immediately
    if order_type == 'MARKET' and market_hours.is_market_open():
        price = _current_price(ticker, refresh=True)
        fill = slippage.evaluate_fill(direction, 'MARKET', price)
        return _execute_and_record(user, ticker, direction, order_type,
                                   quantity, fill, limit_price, stop_price).to_dict()

    # Everything else queues as PENDING
    return _queue_order(user, ticker, direction, order_type,
                        quantity, limit_price, stop_price).to_dict()


def get_orders(user):
    rows = (Order.query
            .filter_by(user_id=user.id)
            .order_by(Order.placed_at.desc())
            .limit(100)
            .all())
    return [o.to_dict() for o in rows]


def cancel_order(user, order_id):
    order = Order.query.filter_by(id=order_id, user_id=user.id).first()
    if not order:
        raise AppError('Order not found', 404)
    if order.status != 'PENDING':
        raise AppError('Only pending orders can be cancelled', 409)
    order.status = 'CANCELLED'
    PendingOrder.query.filter_by(order_id=order.id).delete()
    db.session.commit()


# ---- Scheduled job entry points ---------------------------------------------

def check_pending_orders():
    """Hourly: refresh prices for tickers with pending orders, then evaluate fills."""
    tickers = [row[0] for row in db.session.query(PendingOrder.ticker).distinct().all()]
    if not tickers:
        return
    stock_service.refresh_prices(tickers)

    now = market_hours.now_et().replace(tzinfo=None)
    for pending in PendingOrder.query.all():
        order = Order.query.get(pending.order_id)
        if not order or order.status != 'PENDING':
            db.session.delete(pending)
            db.session.commit()
            continue

        if now >= order.expires_at:
            _expire(order, pending)
            continue

        price = _current_price(pending.ticker, refresh=False)
        if price is None:
            continue

        fill = slippage.evaluate_fill(
            pending.direction, pending.order_type, price,
            limit_price=pending.limit_price, stop_price=pending.stop_price,
        )
        if fill is None:
            continue

        _fill_pending(order, pending, fill)


def process_queued_orders():
    """Market open: convert overnight MARKET orders to fills; reset the 6h timer for all pending orders to start now."""
    open_dt = market_hours.now_et().replace(tzinfo=None)
    close_dt = market_hours.market_close_dt().replace(tzinfo=None)
    new_expiry = min(open_dt + MAX_DURATION, close_dt)

    for pending in PendingOrder.query.all():
        order = Order.query.get(pending.order_id)
        if not order or order.status != 'PENDING':
            db.session.delete(pending)
            continue
        order.expires_at = new_expiry
        pending.expires_at = new_expiry
    db.session.commit()

    # Now run a normal fill pass so queued market orders execute at the open price
    check_pending_orders()


def expire_all_pending():
    """Market close: expire every remaining pending order."""
    for pending in PendingOrder.query.all():
        order = Order.query.get(pending.order_id)
        if order and order.status == 'PENDING':
            order.status = 'EXPIRED'
        db.session.delete(pending)
    db.session.commit()


# ---- Internals ---------------------------------------------------------------

def _queue_order(user, ticker, direction, order_type, quantity, limit_price, stop_price):
    now = market_hours.now_et().replace(tzinfo=None)
    if market_hours.is_market_open():
        expires_at = min(now + MAX_DURATION, market_hours.market_close_dt().replace(tzinfo=None))
    else:
        nxt = market_hours.next_market_open_dt().replace(tzinfo=None)
        expires_at = min(nxt + MAX_DURATION, market_hours.market_close_dt(nxt.date()).replace(tzinfo=None))

    order = Order(
        user_id=user.id, ticker=ticker, order_type=order_type, direction=direction,
        quantity=quantity, limit_price=limit_price, stop_price=stop_price,
        status='PENDING', placed_at=now, expires_at=expires_at,
    )
    db.session.add(order)
    db.session.flush()  # populate order.id for the pending row

    db.session.add(PendingOrder(
        order_id=order.id, user_id=user.id, ticker=ticker, order_type=order_type,
        direction=direction, quantity=quantity, limit_price=limit_price,
        stop_price=stop_price, expires_at=expires_at,
    ))
    db.session.commit()
    return order


def _execute_and_record(user, ticker, direction, order_type, quantity,
                        fill_price, limit_price, stop_price):
    _do_execute(user, ticker, direction, quantity, fill_price)
    order = Order(
        user_id=user.id, ticker=ticker, order_type=order_type, direction=direction,
        quantity=quantity, limit_price=limit_price, stop_price=stop_price,
        status='FILLED', fill_price=fill_price,
        placed_at=datetime.utcnow(), expires_at=datetime.utcnow(),
        filled_at=datetime.utcnow(),
    )
    db.session.add(order)
    db.session.commit()
    return order


def _fill_pending(order, pending, fill_price):
    from ..models.user import User
    user = User.query.get(order.user_id)
    # Stage the status change and pending-row removal BEFORE executing, so the trade's commit
    # persists the trade, the FILLED status, and the pending deletion in one atomic transaction.
    order.status = 'FILLED'
    order.fill_price = fill_price
    order.filled_at = datetime.utcnow()
    db.session.delete(pending)
    try:
        _do_execute(user, order.ticker, order.direction, Decimal(str(order.quantity)), fill_price)
    except AppError:
        # Couldn't fill (e.g. balance dropped) — undo the staged changes; the order stays
        # PENDING and will retry next hourly check or expire at market close.
        db.session.rollback()


def _do_execute(user, ticker, direction, quantity, fill_price):
    if direction == 'BUY':
        trade_service.execute_buy(user, ticker, quantity, fill_price)
    else:
        trade_service.execute_sell(user, ticker, quantity, fill_price)


def _expire(order, pending):
    order.status = 'EXPIRED'
    db.session.delete(pending)
    db.session.commit()


def _validate_affordability(user, ticker, direction, order_type, quantity, limit_price):
    if direction == 'BUY':
        ref = limit_price if order_type in ('LIMIT', 'STOP_LIMIT') and limit_price else _current_price(ticker, refresh=True)
        if ref is None:
            raise AppError('Unable to price order', 422)
        est_cost = Decimal(str(quantity)) * Decimal(str(ref))
        if Decimal(str(user.balance)) < est_cost:
            raise AppError('Insufficient balance for this order', 402)
    else:  # SELL
        if trade_service.shares_held(user.id, ticker) < Decimal(str(quantity)):
            raise AppError('Insufficient shares held', 422)


def _current_price(ticker, refresh=False):
    if refresh:
        stock_service.get_quote(ticker)  # refreshes if stale
    stock = Stock.query.get(ticker)
    return Decimal(str(stock.last_price)) if stock and stock.last_price is not None else None
