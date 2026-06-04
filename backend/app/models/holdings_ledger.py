"""Holdings ledger model — the "current state" half of the CQRS design.

One row per tax lot. Every BUY inserts a new lot; SELLs reduce `qty_remaining` from the oldest lots
first (FIFO), and lots that reach zero are deleted. Keeping current holdings in this small table means
portfolio reads stay fast no matter how long the transaction history grows. Indexes support the common
per-user and per-user-per-ticker (FIFO-ordered) lookups.
"""
from datetime import datetime
from .. import db


class HoldingLot(db.Model):
    """A single purchase lot: shares remaining, the price paid, when bought, and its DRIP flag."""

    __tablename__ = 'holdings_ledger'

    lot_id         = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ticker         = db.Column(db.String(10), nullable=False)
    qty_remaining  = db.Column(db.Numeric(15, 2), nullable=False)
    cost_per_share = db.Column(db.Numeric(15, 4), nullable=False)
    purchased_at   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    drip_enabled   = db.Column(db.Boolean, default=False, nullable=False)

    __table_args__ = (
        db.Index('idx_holdings_user', 'user_id'),
        db.Index('idx_holdings_user_ticker', 'user_id', 'ticker'),
        db.Index('idx_holdings_user_ticker_date', 'user_id', 'ticker', 'purchased_at'),
    )
