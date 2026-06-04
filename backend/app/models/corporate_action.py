"""Corporate actions log model.

Records dividends, splits, mergers, acquisitions, spinoffs, ticker changes, and delistings fetched
daily from FMP. `details` holds action-specific data as JSON (e.g. amount-per-share, split ratio,
cash price, new ticker). `processed_at` stays NULL until the 9:25 AM processor job applies the action
to every affected holding — making it the queue of pending corporate actions.
"""
from datetime import datetime
from .. import db

ACTION_TYPES = (
    'DIVIDEND_CASH', 'DIVIDEND_STOCK',
    'SPLIT_FORWARD', 'SPLIT_REVERSE',
    'MERGER', 'ACQUISITION', 'SPINOFF',
    'TICKER_CHANGE', 'DELISTING',
)


class CorporateAction(db.Model):
    """A single corporate action to apply on its effective date; unprocessed while `processed_at` is NULL."""

    __tablename__ = 'corporate_actions_log'

    id             = db.Column(db.Integer, primary_key=True)
    ticker         = db.Column(db.String(10), nullable=False)
    action_type    = db.Column(db.Enum(*ACTION_TYPES, name='action_type_enum'), nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    details        = db.Column(db.JSON, nullable=False)
    processed_at   = db.Column(db.DateTime)                  # null until applied
    created_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index('idx_ca_ticker', 'ticker'),
        db.Index('idx_ca_date', 'effective_date'),
        db.Index('idx_ca_unprocessed', 'processed_at', 'effective_date'),
    )
