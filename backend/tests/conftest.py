# Shared pytest fixtures. Env vars are set here BEFORE importing the app so create_app() picks up
# an in-memory-style SQLite test DB and never starts the scheduler.
import os

os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
os.environ.setdefault('ENABLE_SCHEDULER', 'false')
os.environ.setdefault('WEBSITE_API_KEY', 'test-web-key')
os.environ.setdefault('BOT_API_KEY', 'test-bot-key')
os.environ.setdefault('GOOGLE_CLIENT_ID', 'x')
os.environ.setdefault('GOOGLE_CLIENT_SECRET', 'x')
os.environ.setdefault('MICROSOFT_CLIENT_ID', 'x')
os.environ.setdefault('MICROSOFT_CLIENT_SECRET', 'x')

from datetime import datetime, timedelta  # noqa: E402
from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402

from app import create_app, db  # noqa: E402


@pytest.fixture
def app():
    # Flask-SQLAlchemy 3.x auto-applies StaticPool for in-memory SQLite, so one connection
    # is shared across sessions and the schema/data persists for the whole test.
    application = create_app()
    with application.app_context():
        db.drop_all()
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def session(app):
    return db.session


@pytest.fixture
def make_user(session):
    from app.models.user import User

    def _make(balance=100000, state='CA', drip_all=False):
        user = User(
            email=f'user{User.query.count()}@test.com',
            display_name='Tester',
            google_id=f'g{User.query.count()}',
            starting_balance=Decimal(str(balance)),
            balance=Decimal(str(balance)),
            state=state,
            drip_all=drip_all,
            last_active_at=datetime.utcnow(),
        )
        session.add(user)
        session.commit()
        return user

    return _make


@pytest.fixture
def make_stock(session):
    from app.models.stock import Stock

    def _make(ticker, price):
        stock = Stock(ticker=ticker, company_name=f'{ticker} Inc',
                      last_price=Decimal(str(price)), last_updated=datetime.utcnow())
        session.add(stock)
        session.commit()
        return stock

    return _make
