from app.extensions import db
from app.models import User


def test_index_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"az1m0v" in r.data.lower()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_register_get(client):
    r = client.get("/register")
    assert r.status_code == 200
    assert b"Register" in r.data or b"sandbox" in r.data.lower()


def test_register_redirect_assigns_port(client, app):
    r = client.post(
        "/register",
        data={"email": "new@example.com", "password": "hunter22"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "Location" in r.headers
    assert r.headers["Location"].startswith("http://localhost:")
    with app.app_context():
        u = User.query.filter_by(email="new@example.com").one()
        assert u.vscode_port is not None
        assert 9000 <= u.vscode_port <= 9100


def test_register_duplicate_email(client):
    client.post(
        "/register",
        data={"email": "dup@example.com", "password": "password12"},
    )
    r = client.post(
        "/register",
        data={"email": "dup@example.com", "password": "password12"},
        follow_redirects=False,
    )
    assert r.status_code == 409


def test_register_validation(client):
    r = client.post(
        "/register",
        data={"email": "bad", "password": "short"},
        follow_redirects=False,
    )
    assert r.status_code == 400
