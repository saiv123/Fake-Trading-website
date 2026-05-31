# SQLAlchemy model for the holdings_ledger table — one row per tax lot; BUYs insert, SELLs reduce qty_remaining FIFO, zeroed rows are deleted
from datetime import datetime
from .. import db


class HoldingLot(db.Model):
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
