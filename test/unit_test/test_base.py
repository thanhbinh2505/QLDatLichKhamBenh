import pytest
from flask import Flask
from selenium import webdriver

from app import db, login
from app.models import User
from app.index import register_routes

def create_app():
    app = Flask('app')
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    db.init_app(app)
    app.secret_key = 'difhhfoiwufowirgoi'
    login.init_app(app)
    register_routes(app=app)
    return app


@pytest.fixture
def test_app():
    app = create_app()

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def test_session(test_app):
    yield db.session
    db.session.rollback()


@pytest.fixture
def test_client(test_app):
    return test_app.test_client()


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()

    options.add_argument("--incognito")

    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "safebrowsing.enabled": False  # Tắt luôn Safe Browsing nếu cần
    }
    options.add_experimental_option("prefs", prefs)

    options.add_argument("--disable-features=PasswordLeakDetection")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)

    yield driver
    driver.quit()