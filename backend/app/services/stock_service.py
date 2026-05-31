# Fetches stock quotes from the DB and refreshes from MarketData.app if stale; also handles ticker search by name or symbol.
import os
from datetime import datetime, timedelta, timezone

import requests

from .. import db
from ..models.stock import Stock
from ..utils import market_hours
from ..utils.errors import AppError

MARKETDATA_BASE = 'https://api.marketdata.app/v1'
STALE_MINUTES = 15


def _token():
    return os.environ.get('MARKETDATA_API_TOKEN', '')


def is_stale(stock: Stock) -> bool:
    if stock.last_updated is None:
        return True
    now = datetime.utcnow()
    if market_hours.is_market_open():
        return stock.last_updated < now - timedelta(minutes=STALE_MINUTES)
    # Outside market hours: stale if older than today's close (last_updated is naive UTC)
    close_utc = market_hours.market_close_dt().astimezone(timezone.utc).replace(tzinfo=None)
    return stock.last_updated < close_utc


def get_quote(ticker: str):
    stock = Stock.query.get(ticker)
    if stock is None or is_stale(stock):
        stock = refresh_one(ticker)
    return stock.to_dict() if stock else None


def search(query: str):
    like = f'%{query}%'
    rows = (Stock.query
            .filter(db.or_(Stock.ticker.ilike(like), Stock.company_name.ilike(like)))
            .filter(Stock.is_active.is_(True))
            .limit(25)
            .all())
    return [{'ticker': s.ticker, 'company_name': s.company_name, 'last_price': str(s.last_price) if s.last_price else None}
            for s in rows]


def refresh_prices(tickers):
    """Batch-refresh a list of tickers (used by the hourly order check and market open/close jobs)."""
    for ticker in set(tickers):
        try:
            refresh_one(ticker)
        except AppError:
            continue


def refresh_one(ticker: str):
    """Fetch a single ticker from MarketData.app and upsert the stocks row."""
    ticker = ticker.upper()
    resp = requests.get(
        f'{MARKETDATA_BASE}/stocks/quotes/{ticker}/',
        params={'52week': 'true'},
        headers={'Authorization': f'Bearer {_token()}'},
        timeout=10,
    )
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise AppError('Price provider unavailable', 502)

    data = resp.json()
    if data.get('s') != 'ok':
        return None

    # MarketData returns parallel arrays; index 0 is the requested ticker
    stock = Stock.query.get(ticker) or Stock(ticker=ticker)
    stock.last_price     = _first(data.get('last'))
    stock.bid            = _first(data.get('bid'))
    stock.ask            = _first(data.get('ask'))
    stock.day_open       = _first(data.get('open'))
    stock.day_high       = _first(data.get('high'))
    stock.day_low        = _first(data.get('low'))
    stock.change_amount  = _first(data.get('change'))
    stock.change_percent = _first(data.get('changepct'))
    stock.week_52_high   = _first(data.get('52weekHigh'))
    stock.week_52_low    = _first(data.get('52weekLow'))
    stock.volume         = _first(data.get('volume'))
    stock.last_updated   = datetime.utcnow()
    stock.is_active      = True

    db.session.add(stock)
    db.session.commit()
    return stock


def _first(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value
