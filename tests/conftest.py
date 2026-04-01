import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "ENABLE_VSCODE_SPAWN": False,
            "VSCODE_PUBLIC_HOST": "localhost",
            "VSCODE_PUBLIC_SCHEME": "http",
            # Explicit for tests; leave unset in production compose to use request Host.
            "VSCODE_PORT_MIN": 9000,
            "VSCODE_PORT_MAX": 9100,
        }
    )
    with application.app_context():
        db.create_all()
    yield application
    with application.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
