"""Stock quote endpoints (/api/stocks).

search is website-only (the bot has no search command) and requires a valid login session.
get_stock is called by both the website's Trade page and the bot's /price command, so it accepts
either a session token or the bot's Discord-user credentials. stock_service handles cache reads and
refreshing stale prices from MarketData.app.
"""
from flask import Blueprint, request, jsonify
from ..utils.auth import require_session, require_session_or_bot_user
from ..services.stock_service import get_quote, search

stocks_bp = Blueprint('stocks', __name__, url_prefix='/api/stocks')


@stocks_bp.route('/search')
@require_session
def search_stocks():
    """GET /api/stocks/search?q= — find tickers by symbol or company name."""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'error': 'Missing query'}), 400
    return jsonify(search(q))


@stocks_bp.route('/<ticker>')
@require_session_or_bot_user
def get_stock(ticker):
    """GET /api/stocks/<ticker> — one quote, refreshed from the provider if the cache is stale."""
    stock = get_quote(ticker.upper())
    if not stock:
        return jsonify({'error': 'Ticker not found'}), 404
    return jsonify(stock)
