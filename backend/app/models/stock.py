"""Stock price-cache model.

The `stocks` table is a local cache of the latest quote per ticker, refreshed at market open/close,
on-demand when a quote is stale, and hourly for tickers with pending orders — never on every page load.
`after_hours_price` is shown to users but is never used for order execution.
"""
from datetime import datetime
from .. import db


class Stock(db.Model):
    """Cached latest quote for one ticker (price, bid/ask, day & 52-week ranges, volume)."""

    __tablename__ = 'stocks'

    ticker            = db.Column(db.String(10), primary_key=True)
    company_name      = db.Column(db.String(255))
    last_price        = db.Column(db.Numeric(15, 4))
    day_open          = db.Column(db.Numeric(15, 4))
    day_high          = db.Column(db.Numeric(15, 4))
    day_low           = db.Column(db.Numeric(15, 4))
    after_hours_price = db.Column(db.Numeric(15, 4))   # displayed only, never used in execution
    bid               = db.Column(db.Numeric(15, 4))
    ask               = db.Column(db.Numeric(15, 4))
    change_amount     = db.Column(db.Numeric(15, 4))
    change_percent    = db.Column(db.Numeric(8, 4))
    week_52_high      = db.Column(db.Numeric(15, 4))
    week_52_low       = db.Column(db.Numeric(15, 4))
    volume            = db.Column(db.BigInteger)
    last_updated      = db.Column(db.DateTime, default=datetime.utcnow)
    is_active         = db.Column(db.Boolean, default=True, nullable=False)  # false for delisted/renamed

    def to_dict(self):
        """Serialize the quote to JSON-safe primitives (Decimals → strings) for API responses."""
        return {
            'ticker':            self.ticker,
            'company_name':      self.company_name,
            'last_price':        _s(self.last_price),
            'day_open':          _s(self.day_open),
            'day_high':          _s(self.day_high),
            'day_low':           _s(self.day_low),
            'after_hours_price': _s(self.after_hours_price),
            'bid':               _s(self.bid),
            'ask':               _s(self.ask),
            'change_amount':     _s(self.change_amount),
            'change_percent':    _s(self.change_percent),
            'week_52_high':      _s(self.week_52_high),
            'week_52_low':       _s(self.week_52_low),
            'volume':            self.volume,
            'last_updated':      self.last_updated.isoformat() if self.last_updated else None,
            'is_active':         self.is_active,
        }


def _s(value):
    return str(value) if value is not None else None
