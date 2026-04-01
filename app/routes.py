from flask import (
    Blueprint,
    flash,
    render_template,
    request,
)
from sqlalchemy.exc import IntegrityError

from app.ev_content import (
    EV_CROWDFUNDING_PITCH,
    EV_HIGHLIGHTS,
    EV_TAGLINE,
    EV_TECH_BLURB,
)
from app.extensions import db
from app.models import User
from app.vscode_manager import ensure_vscode_for_user

bp = Blueprint("main", __name__)


def _resolve_public_host() -> str:
    from flask import current_app

    cfg = current_app.config
    h = cfg.get("VSCODE_PUBLIC_HOST")
    if h:
        return str(h)
    return request.headers.get("X-Forwarded-Host") or request.host.split(":")[0]


def _resolve_public_scheme() -> str:
    from flask import current_app

    cfg = current_app.config
    s = cfg.get("VSCODE_PUBLIC_SCHEME")
    if s:
        return str(s)
    return request.headers.get("X-Forwarded-Proto") or request.scheme


@bp.route("/")
def index():
    from flask import current_app

    cfg = current_app.config
    return render_template(
        "index.html",
        tagline=EV_TAGLINE,
        highlights=EV_HIGHLIGHTS,
        pitch=EV_CROWDFUNDING_PITCH,
        tech=EV_TECH_BLURB,
        goal_usd=cfg["CROWDFUNDING_GOAL_USD"],
        raised_usd=cfg["CROWDFUNDING_RAISED_USD"],
    )


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    if not email or "@" not in email:
        flash("Please enter a valid email.", "error")
        return render_template("register.html"), 400
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return render_template("register.html"), 400

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("That email is already registered.", "error")
        return render_template("register.html"), 409

    from flask import current_app

    # Fresh ORM instance after commit (avoids expired/detached user when spawn touches the DB).
    user = User.query.filter_by(email=email).one()

    try:
        port, err, ide_password = ensure_vscode_for_user(user, dict(current_app.config))
    except Exception as e:
        current_app.logger.exception("ensure_vscode_for_user")
        port = current_app.config["VSCODE_PORT_MIN"]
        err, ide_password = str(e), None

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    host = _resolve_public_host()
    scheme = _resolve_public_scheme()
    vscode_url = f"{scheme}://{host}:{port}/"

    if err and ide_password is None:
        flash(f"Account created, but the IDE could not be started: {err}", "error")
        return render_template(
            "ide_launch.html",
            vscode_url=vscode_url,
            ide_password=None,
            warn=None,
            error_detail=err,
        )

    warn = err if err else None

    return render_template(
        "ide_launch.html",
        vscode_url=vscode_url,
        ide_password=ide_password,
        warn=warn,
        error_detail=None,
    )


@bp.route("/health")
def health():
    return {"status": "ok"}
