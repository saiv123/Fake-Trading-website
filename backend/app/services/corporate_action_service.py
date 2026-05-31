# Fetches corporate actions from FMP and applies them — forward/reverse splits, ticker changes, mergers,
# acquisitions, spinoffs, and bankruptcy/delisting position zeroing. Cash/stock dividends delegate to dividend_service.
import os
from datetime import datetime, date, timedelta
from decimal import Decimal

import requests

from .. import db
from ..models.corporate_action import CorporateAction
from ..models.holdings_ledger import HoldingLot
from ..models.transaction import Transaction
from ..models.stock import Stock
from ..models.user import User
from ..utils.fractional import truncate_shares, truncate_money, to_price
from . import dividend_service, notification_service

FMP_BASE = 'https://financialmodelingprep.com/api/v3'


def _key():
    return os.environ.get('FMP_API_KEY', '')


# ---- Daily fetch (9:00 AM ET) -----------------------------------------------

def fetch_corporate_actions(days_ahead: int = 7):
    """Pull the next N days of dividends and splits from FMP into the corporate_actions_log."""
    today = date.today()
    end = today + timedelta(days=days_ahead)
    held = {t[0] for t in db.session.query(HoldingLot.ticker).distinct().all()}
    if not held:
        return

    _fetch_dividends(today, end, held)
    _fetch_splits(today, end, held)
    db.session.commit()


def _fetch_dividends(start, end, held):
    resp = requests.get(f'{FMP_BASE}/stock_dividend_calendar',
                        params={'from': start, 'to': end, 'apikey': _key()}, timeout=15)
    if resp.status_code != 200:
        return
    for item in resp.json():
        ticker = item.get('symbol')
        if ticker not in held:
            continue
        eff = _parse_date(item.get('paymentDate') or item.get('date'))
        if not eff:
            continue
        _upsert_action(ticker, 'DIVIDEND_CASH', eff,
                       {'amount_per_share': item.get('dividend')})


def _fetch_splits(start, end, held):
    resp = requests.get(f'{FMP_BASE}/stock_split_calendar',
                        params={'from': start, 'to': end, 'apikey': _key()}, timeout=15)
    if resp.status_code != 200:
        return
    for item in resp.json():
        ticker = item.get('symbol')
        if ticker not in held:
            continue
        eff = _parse_date(item.get('date'))
        numerator = item.get('numerator') or 1
        denominator = item.get('denominator') or 1
        if not eff or numerator == denominator:
            continue
        if numerator > denominator:
            action_type, ratio = 'SPLIT_FORWARD', Decimal(str(numerator)) / Decimal(str(denominator))
        else:
            action_type, ratio = 'SPLIT_REVERSE', Decimal(str(denominator)) / Decimal(str(numerator))
        _upsert_action(ticker, action_type, eff, {'ratio': str(ratio)})


# ---- Processor (9:25 AM ET, trading days) -----------------------------------

def process_due_actions(as_of: date = None):
    """Apply all unprocessed actions whose effective date has arrived."""
    as_of = as_of or date.today()
    due = (CorporateAction.query
           .filter(CorporateAction.processed_at.is_(None),
                   CorporateAction.effective_date <= as_of)
           .order_by(CorporateAction.effective_date.asc())
           .all())

    for action in due:
        _dispatch(action)
        action.processed_at = datetime.utcnow()
        db.session.commit()


def _dispatch(action: CorporateAction):
    t = action.action_type
    d = action.details or {}
    ticker = action.ticker

    if t == 'DIVIDEND_CASH':
        dividend_service.process_cash_dividend(ticker, d.get('amount_per_share', 0))
    elif t == 'DIVIDEND_STOCK':
        dividend_service.process_stock_dividend(ticker, d.get('ratio', 0))
    elif t == 'SPLIT_FORWARD':
        _apply_forward_split(ticker, Decimal(str(d.get('ratio', 1))))
    elif t == 'SPLIT_REVERSE':
        _apply_reverse_split(ticker, Decimal(str(d.get('ratio', 1))))
    elif t == 'TICKER_CHANGE':
        _apply_ticker_change(ticker, d.get('new_ticker'))
    elif t in ('MERGER', 'ACQUISITION', 'SPINOFF'):
        _close_position(ticker, cash_price=d.get('cash_price'), reason=t)
    elif t == 'DELISTING':
        _zero_position(ticker)


def _apply_forward_split(ticker, ratio):
    for lot in HoldingLot.query.filter_by(ticker=ticker).all():
        lot.qty_remaining = truncate_shares(Decimal(str(lot.qty_remaining)) * ratio)
        lot.cost_per_share = to_price(Decimal(str(lot.cost_per_share)) / ratio)
    _notify_holders(ticker, 'Stock split', f'{ticker}: {ratio}-for-1 forward split applied.')


def _apply_reverse_split(ticker, ratio):
    for lot in HoldingLot.query.filter_by(ticker=ticker).all():
        lot.qty_remaining = truncate_shares(Decimal(str(lot.qty_remaining)) / ratio)
        lot.cost_per_share = to_price(Decimal(str(lot.cost_per_share)) * ratio)
    _notify_holders(ticker, 'Reverse split', f'{ticker}: 1-for-{ratio} reverse split applied.')


def _apply_ticker_change(old_ticker, new_ticker):
    if not new_ticker:
        return
    HoldingLot.query.filter_by(ticker=old_ticker).update({'ticker': new_ticker})

    old_stock = Stock.query.get(old_ticker)
    if old_stock:
        old_stock.is_active = False
    if not Stock.query.get(new_ticker):
        db.session.add(Stock(ticker=new_ticker,
                             company_name=old_stock.company_name if old_stock else None,
                             is_active=True))
    _notify_holders(new_ticker, 'Ticker change', f'{old_ticker} is now trading as {new_ticker}.')


def _close_position(ticker, cash_price=None, reason='MERGER'):
    """Close every holder's position. Cash deal pays acquisition price; otherwise pays cost basis."""
    for user_id in _holders(ticker):
        lots = HoldingLot.query.filter_by(user_id=user_id, ticker=ticker).all()
        qty = sum(Decimal(str(l.qty_remaining)) for l in lots)
        if qty <= 0:
            continue
        if cash_price:
            proceeds = truncate_money(qty * Decimal(str(cash_price)))
        else:
            proceeds = truncate_money(sum(Decimal(str(l.qty_remaining)) * Decimal(str(l.cost_per_share)) for l in lots))

        user = User.query.get(user_id)
        user.balance = Decimal(str(user.balance)) + proceeds
        for lot in lots:
            db.session.delete(lot)
        db.session.add(Transaction(
            user_id=user_id, ticker=ticker, type='CORPORATE_ACTION_CASHOUT',
            quantity=qty, total_value=proceeds, executed_at=datetime.utcnow(),
            notes=f'{reason}: position closed for ${proceeds}',
        ))
        notification_service.create_notification(
            user_id, reason.title(), f'{ticker}: position closed, ${proceeds} credited.', ticker)


def _zero_position(ticker):
    """Bankruptcy/delisting — wipe positions, return no cash."""
    for user_id in _holders(ticker):
        lots = HoldingLot.query.filter_by(user_id=user_id, ticker=ticker).all()
        qty = sum(Decimal(str(l.qty_remaining)) for l in lots)
        if qty <= 0:
            continue
        for lot in lots:
            db.session.delete(lot)
        db.session.add(Transaction(
            user_id=user_id, ticker=ticker, type='CORPORATE_ACTION_CASHOUT',
            quantity=qty, total_value=Decimal('0'), executed_at=datetime.utcnow(),
            notes='Delisting/bankruptcy: position zeroed, no cash returned',
        ))
        notification_service.create_notification(
            user_id, 'Delisting', f'{ticker} was delisted. Position zeroed, no cash returned.', ticker)

    stock = Stock.query.get(ticker)
    if stock:
        stock.is_active = False


# ---- Helpers -----------------------------------------------------------------

def _holders(ticker):
    return [r[0] for r in db.session.query(HoldingLot.user_id)
            .filter(HoldingLot.ticker == ticker, HoldingLot.qty_remaining > 0)
            .distinct().all()]


def _notify_holders(ticker, title, message):
    for user_id in _holders(ticker):
        notification_service.create_notification(user_id, title, message, ticker)


def _upsert_action(ticker, action_type, effective_date, details):
    exists = CorporateAction.query.filter_by(
        ticker=ticker, action_type=action_type, effective_date=effective_date).first()
    if exists:
        return
    db.session.add(CorporateAction(
        ticker=ticker, action_type=action_type,
        effective_date=effective_date, details=details))


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None
