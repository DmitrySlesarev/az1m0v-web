"""Fetch and render README from the public az1m0v GitHub repository."""

from __future__ import annotations

import logging
import time
import urllib.error
import urllib.request

import bleach
import markdown

log = logging.getLogger(__name__)

_CACHE: dict[str, tuple[float, str | None, str | None]] = {}
_CACHE_TTL_SEC = 300.0

ALLOWED_TAGS = frozenset(bleach.sanitizer.ALLOWED_TAGS) | frozenset(
    {
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "pre",
        "p",
        "span",
        "div",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "hr",
        "img",
    }
)
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "code": ["class"],
    "pre": ["class"],
    "img": ["src", "alt", "title"],
    "th": ["align"],
    "td": ["align"],
}


def _repo_slug_from_url(repo_url: str | None) -> str:
    if not repo_url:
        return "DmitrySlesarev/az1m0v"

    cleaned = repo_url.strip()
    if cleaned.startswith("git@github.com:"):
        path = cleaned.split("git@github.com:", 1)[1]
    elif "github.com/" in cleaned:
        path = cleaned.split("github.com/", 1)[1]
    else:
        return "DmitrySlesarev/az1m0v"

    slug = path.strip("/")
    if slug.endswith(".git"):
        slug = slug[:-4]
    parts = slug.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return "DmitrySlesarev/az1m0v"
    return f"{parts[0]}/{parts[1]}"


def readme_raw_url(branch: str, repo_url: str | None = None) -> str:
    slug = _repo_slug_from_url(repo_url)
    return (
        f"https://raw.githubusercontent.com/{slug}/{branch}/README.md"
    )


def fetch_readme_html(branch: str, repo_url: str | None = None) -> tuple[str | None, str | None]:
    """
    Returns (html, error_message).
    html is None on failure.
    """
    now = time.monotonic()
    key = f"{_repo_slug_from_url(repo_url)}:{branch}"
    if key in _CACHE:
        ts, html, err = _CACHE[key]
        if now - ts < _CACHE_TTL_SEC:
            return html, err

    url = readme_raw_url(branch, repo_url=repo_url)
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "az1m0v-web-readme-fetch/1.0"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        msg = f"HTTP {e.code}"
        log.warning("README fetch failed: %s %s", url, msg)
        _CACHE[key] = (now, None, msg)
        return None, msg
    except Exception as e:
        msg = str(e)
        log.warning("README fetch failed: %s", msg)
        _CACHE[key] = (now, None, msg)
        return None, msg

    md = markdown.markdown(
        raw,
        extensions=["fenced_code", "tables", "nl2br"],
        output_format="html",
    )
    safe = bleach.clean(
        md,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )
    _CACHE[key] = (now, safe, None)
    return safe, None


def clear_readme_cache() -> None:
    _CACHE.clear()
