"""Order endpoints (/api/orders).

Thin HTTP layer over order_service: it validates the request shape (direction, order type, and that the
right price fields are present) and then delegates all placement/cancellation logic to the service.
Every route is user-scoped via require_session_or_bot_user, which injects the acting user as g.user —
either the website's logged-in session or the bot acting for a linked Discord user.
"""
from flask import Blueprint, request, jsonify, g
from ..utils.auth import require_session_or_bot_user
from ..services.order_service import place_order, get_orders, cancel_order

orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')

VALID_ORDER_TYPES = {'MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT'}
VALID_DIRECTIONS  = {'BUY', 'SELL'}


@orders_bp.route('', methods=['POST'])
@require_session_or_bot_user
def create_order():
    """POST /api/orders — validate and place a new order; fills immediately or queues as pending."""
    data       = request.get_json()
    ticker     = data.get('ticker')
    direction  = data.get('direction', '').upper()
    order_type = data.get('order_type', '').upper()
    quantity   = data.get('quantity')
    limit_price = data.get('limit_price')
    stop_price  = data.get('stop_price')

    if not all([ticker, direction, order_type, quantity]):
        return jsonify({'error': 'Missing required fields'}), 400

    if direction not in VALID_DIRECTIONS:
        return jsonify({'error': 'Invalid direction'}), 400

    if order_type not in VALID_ORDER_TYPES:
        return jsonify({'error': 'Invalid order_type'}), 400

    if order_type in ('LIMIT', 'STOP_LIMIT') and limit_price is None:
        return jsonify({'error': 'limit_price required for LIMIT and STOP_LIMIT orders'}), 400

    if order_type in ('STOP', 'STOP_LIMIT') and stop_price is None:
        return jsonify({'error': 'stop_price required for STOP and STOP_LIMIT orders'}), 400

    order = place_order(
        user=g.user,
        ticker=ticker.upper(),
        direction=direction,
        order_type=order_type,
        quantity=quantity,
        limit_price=limit_price,
        stop_price=stop_price,
    )
    return jsonify(order), 201


@orders_bp.route('')
@require_session_or_bot_user
def list_orders():
    """GET /api/orders — the user's pending and recent orders."""
    return jsonify(get_orders(g.user))


@orders_bp.route('/<int:order_id>', methods=['DELETE'])
@require_session_or_bot_user
def delete_order(order_id):
    """DELETE /api/orders/<id> — cancel one of the user's pending orders."""
    cancel_order(g.user, order_id)
    return jsonify({'message': 'Order cancelled'})
