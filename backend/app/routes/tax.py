"""Tax endpoints (/api/tax).

Read-only views over tax_service: the live year-to-date estimate and the record of prior-year
settlements. The actual tax calculation and the April 15th settlement run in tax_service.
"""
from flask import Blueprint, jsonify, g
from ..utils.auth import require_session
from ..services.tax_service import get_ytd_estimate, get_settlement_history

tax_bp = Blueprint('tax', __name__, url_prefix='/api/tax')


@tax_bp.route('/estimate')
@require_session
def tax_estimate():
    """GET /api/tax/estimate — current-year liability breakdown (short/long-term, dividends, fed+state)."""
    return jsonify(get_ytd_estimate(g.user))


@tax_bp.route('/history')
@require_session
def tax_history():
    """GET /api/tax/history — prior-year TAX_PAYMENT settlement records."""
    return jsonify(get_settlement_history(g.user))
