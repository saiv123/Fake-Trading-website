"""Portfolio endpoints (/api/portfolio).

User-scoped views and DRIP controls backed by portfolio_service: current holdings with ACB and
unrealized P&L, paginated transaction history, and per-position / bulk dividend-reinvestment toggles.
"""
from flask import Blueprint, request, jsonify, g
from ..utils.auth import require_session_or_bot_user
from ..services.portfolio_service import get_holdings, get_history, enable_all_drip, toggle_drip

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolio')


@portfolio_bp.route('')
@require_session_or_bot_user
def get_portfolio():
    """GET /api/portfolio — holdings with ACB, current value, unrealized P&L, and totals."""
    return jsonify(get_holdings(g.user))


@portfolio_bp.route('/history')
@require_session_or_bot_user
def get_portfolio_history():
    """GET /api/portfolio/history?page= — paginated transaction history."""
    page = request.args.get('page', 1, type=int)
    return jsonify(get_history(g.user, page))


@portfolio_bp.route('/drip/enable-all', methods=['POST'])
@require_session_or_bot_user
def enable_drip_all():
    """POST /api/portfolio/drip/enable-all — turn DRIP on for every current holding."""
    enable_all_drip(g.user)
    return jsonify({'message': 'DRIP enabled for all positions'})


@portfolio_bp.route('/<ticker>/drip', methods=['PATCH'])
@require_session_or_bot_user
def patch_drip(ticker):
    """PATCH /api/portfolio/<ticker>/drip — toggle DRIP for a single position. Body: {drip_enabled: bool}."""
    data        = request.get_json()
    drip_enabled = data.get('drip_enabled')
    if drip_enabled is None:
        return jsonify({'error': 'Missing drip_enabled'}), 400
    toggle_drip(g.user, ticker.upper(), bool(drip_enabled))
    return jsonify({'message': 'DRIP updated'})
