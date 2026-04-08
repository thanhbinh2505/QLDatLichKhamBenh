
import pytest
from flask import Flask

from app import db
from app.models import User

# from app.index import register_routes


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.secret_key = 'difhhfoiwufowirgoi'

    db.init_app(app)
    # register_routes(app=app)
    return app


@pytest.fixture
def test_app():
    app = create_app()

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_session(test_app):
    yield db.session
    db.session.rollback()


@pytest.fixture
def test_client(test_app):
    return test_app.test_client()


# @pytest.fixture
# def sample_products(test_session):
#     p1 = Product(name='Iphone 17', price=30, category_id=1)
#     p2 = Product(name='Galaxy a70', price=30, category_id=1)
#     p3 = Product(name='Galaxy a60', price=30, category_id=2)
#     p4 = Product(name='Iphone 16 promax', price=30, category_id=2)
#     p5 = Product(name='Iphone 16 plus', price=30, category_id=1)
#
#
#     test_session.add_all([p1, p2, p3, p4, p5])
#     test_session.commit()
#
#     return [p1, p2, p3, p4, p5]