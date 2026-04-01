import os
from datetime import timedelta

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
        EV_README_BRANCH=os.environ.get("EV_README_BRANCH", "master"),
        EV_REPO_PAGE_URL=os.environ.get(
            "EV_REPO_PAGE_URL",
            "https://github.com/DmitrySlesarev/az1m0v",
        ),
        CROWDFUNDING_GOAL_USD=_env_int("CROWDFUNDING_GOAL_USD", 250000),
        CROWDFUNDING_RAISED_USD=_env_int("CROWDFUNDING_RAISED_USD", 42000),
        PERMANENT_SESSION_LIFETIME=timedelta(days=14),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(bp)

    @app.before_request
    def _attach_request_locale():
        from app.i18n import attach_locale_to_g

        attach_locale_to_g()

    @app.context_processor
    def _i18n_globals():
        from app.i18n import inject_template_globals

        return inject_template_globals()

    with app.app_context():
        db.create_all()

    return app
