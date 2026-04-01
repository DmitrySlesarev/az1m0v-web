from app.extensions import db
from app.models import User


def test_workspace_redirects_when_not_logged_in(client):
    r = client.get("/workspace", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_login_success_and_workspace(client, app):
    with app.app_context():
        u = User(email="auth@example.com")
        u.set_password("password12")
        db.session.add(u)
        db.session.commit()

    r = client.post(
        "/login",
        data={"email": "auth@example.com", "password": "password12"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "/workspace" in r.headers["Location"]

    r2 = client.get("/workspace")
    assert r2.status_code == 200
    assert b"auth@example.com" in r2.data


def test_login_invalid_password(client, app):
    with app.app_context():
        u = User(email="auth2@example.com")
        u.set_password("password12")
        db.session.add(u)
        db.session.commit()

    r = client.post(
        "/login",
        data={"email": "auth2@example.com", "password": "wrongpassword"},
        follow_redirects=False,
    )
    assert r.status_code == 401


def test_logout_clears_session(client, app):
    with app.app_context():
        u = User(email="auth3@example.com")
        u.set_password("password12")
        db.session.add(u)
        db.session.commit()

    client.post(
        "/login",
        data={"email": "auth3@example.com", "password": "password12"},
    )
    assert client.get("/workspace").status_code == 200

    r = client.post("/logout", follow_redirects=False)
    assert r.status_code == 302

    assert client.get("/workspace", follow_redirects=False).status_code == 302


def test_workspace_provision_creates_port(client, app):
    with app.app_context():
        u = User(email="provision@example.com")
        u.set_password("password12")
        db.session.add(u)
        db.session.commit()

    client.post(
        "/login",
        data={"email": "provision@example.com", "password": "password12"},
    )
    r = client.post("/workspace/provision", follow_redirects=False)
    assert r.status_code == 200
    assert b"Open VS Code" in r.data or b"code-server" in r.data.lower()

    with app.app_context():
        u = User.query.filter_by(email="provision@example.com").one()
        assert u.vscode_port is not None
        assert 9000 <= u.vscode_port <= 9100


def test_workspace_provision_skips_when_already_has_port(client, app):
    with app.app_context():
        u = User(email="hasport@example.com")
        u.set_password("password12")
        u.vscode_port = 9005
        db.session.add(u)
        db.session.commit()

    client.post(
        "/login",
        data={"email": "hasport@example.com", "password": "password12"},
    )
    r = client.post("/workspace/provision", follow_redirects=False)
    assert r.status_code == 302
    assert "/workspace" in r.headers["Location"]


def test_login_page_redirects_when_already_logged_in(client, app):
    with app.app_context():
        u = User(email="auth4@example.com")
        u.set_password("password12")
        db.session.add(u)
        db.session.commit()

    client.post(
        "/login",
        data={"email": "auth4@example.com", "password": "password12"},
    )
    r = client.get("/login", follow_redirects=False)
    assert r.status_code == 302
    assert "/workspace" in r.headers["Location"]
