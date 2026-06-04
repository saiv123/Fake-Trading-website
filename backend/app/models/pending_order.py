"""Pending-orders model — the small "work queue" of orders still awaiting execution.

Mirrors the open subset of the `orders` table (same `order_id`). The hourly check pulls DISTINCT
tickers from here, batch-fetches prices for just those tickers, then evaluates fill conditions across
the rows. A row is deleted the instant its order fills, expires, or is cancelled, so this table stays
tiny — the whole point of separating it from the full `orders` history.
"""
from datetime import datetime
from .. import db


class PendingOrder(db.Model):
    """An open order awaiting a fill; carries only the fields the hourly check needs."""

    __tablename__ = 'pending_orders'

    # order_id mirrors the orders.id of the same order — one pending row per open order
    order_id    = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ticker      = db.Column(db.String(10), nullable=False)
    order_type  = db.Column(db.Enum('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT', name='pending_type_enum'), nullable=False)
    direction   = db.Column(db.Enum('BUY', 'SELL', name='pending_direction_enum'), nullable=False)
    quantity    = db.Column(db.Numeric(15, 2), nullable=False)
    limit_price = db.Column(db.Numeric(15, 4))
    stop_price  = db.Column(db.Numeric(15, 4))
    expires_at  = db.Column(db.DateTime, nullable=False)

    __table_args__ = (
        db.Index('idx_pending_ticker', 'ticker'),
    )
