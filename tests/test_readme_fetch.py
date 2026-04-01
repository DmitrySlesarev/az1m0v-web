import pytest

from app.readme_fetch import clear_readme_cache, fetch_readme_html, readme_raw_url


def test_readme_raw_url():
    u = readme_raw_url("master")
    assert "DmitrySlesarev/az1m0v" in u
    assert u.endswith("/README.md")


def test_fetch_readme_html_uses_cache(monkeypatch):
    clear_readme_cache()
    calls = {"n": 0}

    def fake_urlopen(*a, **kw):
        calls["n"] += 1
        class R:
            def read(self):
                return b"# Hi\n"
            def __enter__(self):
                return self
            def __exit__(self, *x):
                pass
        return R()

    monkeypatch.setattr("app.readme_fetch.urllib.request.urlopen", fake_urlopen)
    h1, e1 = fetch_readme_html("master")
    h2, e2 = fetch_readme_html("master")
    assert e1 is None and e2 is None
    assert h1 and h1 == h2
    assert calls["n"] == 1


def test_bind_error_recoverable():
    from app.vscode_manager import _bind_error_recoverable

    assert _bind_error_recoverable(Exception("port is already allocated"))
    assert _bind_error_recoverable(Exception("Bind for 0.0.0.0:9000 failed: x"))
    assert not _bind_error_recoverable(Exception("something else"))
