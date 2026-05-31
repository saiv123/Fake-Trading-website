from flask import Blueprint, request, jsonify
from ..utils.auth import require_any_key
from ..services.stock_service import get_quote, search

stocks_bp = Blueprint('stocks', __name__, url_prefix='/api/stocks')


@stocks_bp.route('/search')
@require_any_key
def search_stocks():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'error': 'Missing query'}), 400
    return jsonify(search(q))


@stocks_bp.route('/<ticker>')
@require_any_key
def get_stock(ticker):
    stock = get_quote(ticker.upper())
    if not stock:
        return jsonify({'error': 'Ticker not found'}), 404
    return jsonify(stock)
