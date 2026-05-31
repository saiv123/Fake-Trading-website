from flask import Blueprint, jsonify, g
from ..utils.auth import require_api_key
from ..services.tax_service import get_ytd_estimate, get_settlement_history

tax_bp = Blueprint('tax', __name__, url_prefix='/api/tax')


@tax_bp.route('/estimate')
@require_api_key
def tax_estimate():
    return jsonify(get_ytd_estimate(g.user))


@tax_bp.route('/history')
@require_api_key
def tax_history():
    return jsonify(get_settlement_history(g.user))
