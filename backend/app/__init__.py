"""Application factory and shared SQLAlchemy instance.

`db` is created at import time (no app bound yet) so models can import it without a circular dependency;
`create_app()` wires it to a configured Flask app. The factory loads config from the environment,
registers every blueprint and the error handler, creates tables, and — unless ENABLE_SCHEDULER is
false — starts the APScheduler background jobs. Import this module's `db` everywhere; call
`create_app()` once from the entry point (wsgi.py).
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()


def create_app():
    """Build, configure, and return the Flask app (blueprints, DB, error handlers, scheduler)."""
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI']        = os.environ['DATABASE_URL']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['GOOGLE_CLIENT_ID']               = os.environ.get('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET']           = os.environ.get('GOOGLE_CLIENT_SECRET')
    app.config['MICROSOFT_CLIENT_ID']            = os.environ.get('MICROSOFT_CLIENT_ID')
    app.config['MICROSOFT_CLIENT_SECRET']        = os.environ.get('MICROSOFT_CLIENT_SECRET')
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(32))

    db.init_app(app)

    # Import models so SQLAlchemy is aware of every table before create_all
    from .models import (  # noqa: F401
        user, stock, holdings_ledger, transaction,
        order, pending_order, corporate_action, notification,
    )

    # Blueprints
    from .routes.auth import auth_bp, init_oauth
    from .routes.stocks import stocks_bp
    from .routes.portfolio import portfolio_bp
    from .routes.orders import orders_bp
    from .routes.tax import tax_bp
    from .routes.user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(stocks_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(tax_bp)
    app.register_blueprint(user_bp)

    init_oauth(app)

    from .utils.errors import register_error_handlers
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    # Background scheduler — disabled under tests or when explicitly turned off
    if os.environ.get('ENABLE_SCHEDULER', 'true').lower() == 'true':
        from .scheduler.jobs import init_scheduler
        init_scheduler(app)

    @app.route('/health')
    def health():
        return {'status': 'ok'}

    return app
