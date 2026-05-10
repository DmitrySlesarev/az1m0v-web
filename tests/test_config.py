from app import create_app


def _base_test_config() -> dict:
    return {
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    }


def test_env_int_invalid_value_falls_back(monkeypatch):
    monkeypatch.setenv("CROWDFUNDING_GOAL_USD", "not-a-number")
    app = create_app(_base_test_config())
    assert app.config["CROWDFUNDING_GOAL_USD"] == 250000


def test_env_bool_parsing(monkeypatch):
    monkeypatch.setenv("ENABLE_VSCODE_SPAWN", "yes")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")
    app = create_app(_base_test_config())
    assert app.config["ENABLE_VSCODE_SPAWN"] is True
    assert app.config["SESSION_COOKIE_SECURE"] is True


def test_invalid_vscode_port_range_is_normalized():
    cfg = _base_test_config()
    cfg["VSCODE_PORT_MIN"] = 9100
    cfg["VSCODE_PORT_MAX"] = 9000
    app = create_app(cfg)
    assert app.config["VSCODE_PORT_MIN"] == 9000
    assert app.config["VSCODE_PORT_MAX"] == 9100
