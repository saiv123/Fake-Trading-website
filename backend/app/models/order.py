"""Order record model — the full history of every order placed.

Every order (market/limit/stop/stop-limit) gets a row here and its `status` is updated as it resolves
(FILLED / EXPIRED / CANCELLED). This is the source of truth for "show me my orders"; the hourly fill
check never scans this table — it works off the small `pending_orders` table instead (see pending_order.py).
"""
from datetime import datetime
from .. import db


class Order(db.Model):
    """One placed order with its parameters, lifecycle status, and fill details."""

    __tablename__ = 'orders'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ticker      = db.Column(db.String(10), nullable=False)
    order_type  = db.Column(db.Enum('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT', name='order_type_enum'), nullable=False)
    direction   = db.Column(db.Enum('BUY', 'SELL', name='order_direction_enum'), nullable=False)
    quantity    = db.Column(db.Numeric(15, 2), nullable=False)
    limit_price = db.Column(db.Numeric(15, 4))
    stop_price  = db.Column(db.Numeric(15, 4))
    status      = db.Column(db.Enum('PENDING', 'FILLED', 'EXPIRED', 'CANCELLED', name='order_status_enum'),
                            default='PENDING', nullable=False)
    fill_price  = db.Column(db.Numeric(15, 4))
    placed_at   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at  = db.Column(db.DateTime, nullable=False)  # 6hrs from placement OR market close
    filled_at   = db.Column(db.DateTime)

    __table_args__ = (
        db.Index('idx_orders_user', 'user_id'),
    )

    def to_dict(self):
        """Serialize the order to JSON-safe primitives for API responses."""
        return {
            'id':          self.id,
            'ticker':      self.ticker,
            'order_type':  self.order_type,
            'direction':   self.direction,
            'quantity':    _s(self.quantity),
            'limit_price': _s(self.limit_price),
            'stop_price':  _s(self.stop_price),
            'status':      self.status,
            'fill_price':  _s(self.fill_price),
            'placed_at':   self.placed_at.isoformat() if self.placed_at else None,
            'expires_at':  self.expires_at.isoformat() if self.expires_at else None,
            'filled_at':   self.filled_at.isoformat() if self.filled_at else None,
        }


def _s(value):
    return str(value) if value is not None else None
