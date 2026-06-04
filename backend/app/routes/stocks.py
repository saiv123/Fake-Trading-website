"""Stock quote endpoints (/api/stocks).

Quotes aren't tied to a specific user, so these use require_any_key (a valid website/bot key is enough,
no user identity needed). stock_service handles cache reads and refreshing stale prices from MarketData.app.
"""
from flask import Blueprint, request, jsonify
from ..utils.auth import require_any_key
from ..services.stock_service import get_quote, search

stocks_bp = Blueprint('stocks', __name__, url_prefix='/api/stocks')


@stocks_bp.route('/search')
@require_any_key
def search_stocks():
    """GET /api/stocks/search?q= — find tickers by symbol or company name."""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'error': 'Missing query'}), 400
    return jsonify(search(q))


@stocks_bp.route('/<ticker>')
@require_any_key
def get_stock(ticker):
    """GET /api/stocks/<ticker> — one quote, refreshed from the provider if the cache is stale."""
    stock = get_quote(ticker.upper())
    if not stock:
        return jsonify({'error': 'Ticker not found'}), 404
    return jsonify(stock)
