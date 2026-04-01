import os

from flask import Flask

from app.extensions import db
from app.routes import bp


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    return int(raw)


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            "postgresql://az1m0v:az1m0v@localhost:5432/az1m0v_web",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        VSCODE_PORT_MIN=_env_int("VSCODE_PORT_MIN", 9000),
        VSCODE_PORT_MAX=_env_int("VSCODE_PORT_MAX", 9100),
        # Empty / unset = derive Host and scheme from each request (behind OpenResty).
        VSCODE_PUBLIC_HOST=(os.environ.get("VSCODE_PUBLIC_HOST") or None),
        VSCODE_PUBLIC_SCHEME=(os.environ.get("VSCODE_PUBLIC_SCHEME") or None),
        EV_REPO_GIT_URL=os.environ.get(
            "EV_REPO_GIT_URL",
            "https://github.com/DmitrySlesarev/az1m0v.git",
        ),
        ENABLE_VSCODE_SPAWN=os.environ.get("ENABLE_VSCODE_SPAWN", "1") == "1",
        CROWDFUNDING_GOAL_USD=_env_int("CROWDFUNDING_GOAL_USD", 250000),
        CROWDFUNDING_RAISED_USD=_env_int("CROWDFUNDING_RAISED_USD", 42000),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

    return app
