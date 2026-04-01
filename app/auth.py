"""Session-based auth helpers (no Flask-Login dependency)."""

from __future__ import annotations

from functools import wraps
from urllib.parse import urlparse

from flask import redirect, request, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(
                url_for("main.login", next=request.path)
            )
        return view(*args, **kwargs)

    return wrapped


def safe_next_url(fallback_endpoint: str = "main.workspace") -> str:
    """Avoid open redirects: only same-site relative paths allowed."""
    target = (
        (request.form.get("next") or request.args.get("next") or "").strip()
    )
    if not target:
        return url_for(fallback_endpoint)
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return url_for(fallback_endpoint)
    if not target.startswith("/") or target.startswith("//"):
        return url_for(fallback_endpoint)
    return target
