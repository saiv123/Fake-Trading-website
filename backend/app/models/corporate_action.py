# SQLAlchemy model for the corporate_actions_log table — records fetched from FMP daily; processed_at is null until the 9:25 AM job applies them
from datetime import datetime
from .. import db

ACTION_TYPES = (
    'DIVIDEND_CASH', 'DIVIDEND_STOCK',
    'SPLIT_FORWARD', 'SPLIT_REVERSE',
    'MERGER', 'ACQUISITION', 'SPINOFF',
    'TICKER_CHANGE', 'DELISTING',
)


class CorporateAction(db.Model):
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
