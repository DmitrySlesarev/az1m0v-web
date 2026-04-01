from app.auth import is_safe_relative_redirect


def test_is_safe_relative_redirect_accepts_paths():
    assert is_safe_relative_redirect("/workspace")
    assert is_safe_relative_redirect("/login?next=%2F")
    assert not is_safe_relative_redirect("//evil.com")
    assert not is_safe_relative_redirect("https://evil.com")
    assert not is_safe_relative_redirect("")
    assert not is_safe_relative_redirect("ftp://x")
