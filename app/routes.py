from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.exc import IntegrityError

from app.auth import login_required, safe_next_url
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


def _ide_launch_response(user: User, *, account_created: bool = False):
    """
    Run ensure_vscode_for_user, commit, return ide_launch.html.
    Used after registration and from workspace "provision" when no port yet.
    """
    from flask import current_app

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
        if account_created:
            flash(f"Account created, but the IDE could not be started: {err}", "error")
        else:
            flash(f"Could not start the workspace: {err}", "error")
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


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id") is not None:
        return redirect(url_for("main.workspace"))

    if request.method == "GET":
        return render_template("login.html")

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    if not email or "@" not in email:
        flash("Please enter a valid email.", "error")
        return render_template("login.html"), 400

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        flash("Invalid email or password.", "error")
        return render_template("login.html"), 401

    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    return redirect(safe_next_url())


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "warning")
    return redirect(url_for("main.index"))


@bp.route("/workspace")
@login_required
def workspace():
    uid = session.get("user_id")
    user = db.session.get(User, uid)
    if user is None:
        session.clear()
        flash("Your session is no longer valid. Please log in again.", "warning")
        return redirect(url_for("main.login"))

    host = _resolve_public_host()
    scheme = _resolve_public_scheme()

    if user.vscode_port is None:
        from flask import current_app

        return render_template(
            "workspace.html",
            email=user.email,
            vscode_url=None,
            host=host,
            scheme=scheme,
            no_port=True,
            enable_spawn=current_app.config.get("ENABLE_VSCODE_SPAWN", True),
        )

    vscode_url = f"{scheme}://{host}:{user.vscode_port}/"
    return render_template(
        "workspace.html",
        email=user.email,
        vscode_url=vscode_url,
        host=host,
        scheme=scheme,
        no_port=False,
        enable_spawn=True,
    )


@bp.route("/workspace/provision", methods=["POST"])
@login_required
def workspace_provision():
    """Create or retry the personal code-server sandbox for this account."""
    uid = session.get("user_id")
    user = User.query.filter_by(id=uid).one_or_none()
    if user is None:
        session.clear()
        flash("Your session is no longer valid. Please log in again.", "warning")
        return redirect(url_for("main.login"))

    if user.vscode_port is not None:
        flash("Your workspace is already set up. Use the link below.", "warning")
        return redirect(url_for("main.workspace"))

    return _ide_launch_response(user, account_created=False)


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
        flash("That email is already registered. Try logging in instead.", "error")
        return render_template("register.html"), 409

    user = User.query.filter_by(email=email).one()

    session.clear()
    session["user_id"] = user.id
    session.permanent = True

    return _ide_launch_response(user, account_created=True)


@bp.route("/health")
def health():
    return {"status": "ok"}
