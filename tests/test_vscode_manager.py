from app.extensions import db
from app.models import User
from app.vscode_manager import ensure_vscode_for_user, next_free_port


def test_next_free_port_starts_at_min(app):
    with app.app_context():
        p = next_free_port(dict(app.config))
        assert p == 9000


def test_next_free_port_skips_used(app):
    with app.app_context():
        u = User(email="occupied@test.dev")
        u.set_password("password12")
        u.vscode_port = 9000
        db.session.add(u)
        db.session.commit()
        p = next_free_port(dict(app.config))
        assert p == 9001


def test_ensure_without_spawn_sets_port(app):
    with app.app_context():
        u = User(email="spawn@test.dev")
        u.set_password("password12")
        db.session.add(u)
        db.session.commit()
        port, err = ensure_vscode_for_user(u, dict(app.config))
        assert err is None
        assert u.vscode_port == port
        assert 9000 <= port <= 9100
