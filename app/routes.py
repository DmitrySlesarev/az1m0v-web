from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
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

    port, err = ensure_vscode_for_user(user, dict(current_app.config))
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    if err:
        flash(
            f"Account created. VS Code sandbox could not start automatically: {err}. "
            f"Your assigned port is {port}.",
            "warning",
        )
    host = current_app.config["VSCODE_PUBLIC_HOST"]
    scheme = current_app.config["VSCODE_PUBLIC_SCHEME"]
    vscode_url = f"{scheme}://{host}:{port}/"
    return redirect(vscode_url)


@bp.route("/health")
def health():
    return {"status": "ok"}
