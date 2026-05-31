# SQLAlchemy model for the transactions table — append-only immutable log; rows are never updated or deleted; stores realized gains, lot details, and all credit/debit events
from datetime import datetime
from .. import db

TX_TYPES = (
    'BUY', 'SELL',
    'DIVIDEND_CASH', 'DIVIDEND_STOCK', 'DRIP',
    'SPLIT', 'CORPORATE_ACTION_CASHOUT',
    'STIPEND', 'TAX_PAYMENT',
)


class Transaction(db.Model):
    __tablename__ = 'transactions'

    tx_id           = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ticker          = db.Column(db.String(10))                       # NOT a FK — preserved after delisting
    type            = db.Column(db.Enum(*TX_TYPES, name='tx_type_enum'), nullable=False)
    quantity        = db.Column(db.Numeric(15, 2))
    price_per_share = db.Column(db.Numeric(15, 4))
    total_value     = db.Column(db.Numeric(15, 2), nullable=False)   # positive = credit, negative = debit
    short_term_gain = db.Column(db.Numeric(15, 2))                   # SELL rows only
    long_term_gain  = db.Column(db.Numeric(15, 2))                   # SELL rows only
    term            = db.Column(db.Enum('SHORT', 'LONG', 'MIXED', name='term_enum'))
    lot_details     = db.Column(db.JSON)                             # SELL: breakdown of lots consumed
    notes           = db.Column(db.String(500))
    executed_at     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_tx_user', 'user_id'),
        db.Index('idx_tx_user_date', 'user_id', 'executed_at'),
        db.Index('idx_tx_user_type_date', 'user_id', 'type', 'executed_at'),
    )

    def to_dict(self):
        return {
            'tx_id':           self.tx_id,
            'ticker':          self.ticker,
            'type':            self.type,
            'quantity':        _s(self.quantity),
            'price_per_share': _s(self.price_per_share),
            'total_value':     _s(self.total_value),
            'short_term_gain': _s(self.short_term_gain),
            'long_term_gain':  _s(self.long_term_gain),
            'term':            self.term,
            'lot_details':     self.lot_details,
            'notes':           self.notes,
            'executed_at':     self.executed_at.isoformat() if self.executed_at else None,
        }


def _s(value):
    return str(value) if value is not None else None
