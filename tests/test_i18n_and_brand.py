from app.brand import BRAND_NAME
from app.i18n import (
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    TRANSLATIONS,
    _,
    attach_locale_to_g,
    get_locale,
)


def test_brand_name_uses_digit_zero():
    assert BRAND_NAME == "az1m0v"
    assert "0" in BRAND_NAME
    assert "o" not in BRAND_NAME.lower()


def test_all_locales_have_same_keys():
    keys_en = set(TRANSLATIONS["en"])
    for loc in SUPPORTED_LOCALES:
        if loc == "en":
            continue
        missing = keys_en - set(TRANSLATIONS[loc])
        assert not missing, f"{loc} missing keys: {missing}"


def test_unknown_translation_falls_back_to_english(app):
    with app.test_request_context("/"):
        attach_locale_to_g()
        # hypothetical key
        assert _("this_key_does_not_exist_xyz") == "this_key_does_not_exist_xyz"


def test_russian_locale_cookie_on_index(client):
    client.set_cookie("locale", "ru", path="/")
    r = client.get("/")
    assert r.status_code == 200
    text = r.get_data(as_text=True)
    assert "Кампания" in text or "кампания" in text.lower()


def test_set_language_sets_cookie_and_redirects(client):
    r = client.get("/set-language/de?next=/login", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]
    set_cookie = r.headers.getlist("Set-Cookie")
    assert any("locale=de" in c for c in set_cookie)


def test_set_language_invalid_falls_back_to_default(client):
    r = client.get("/set-language/xx?next=/", follow_redirects=False)
    assert r.status_code == 302
    set_cookie = r.headers.getlist("Set-Cookie")
    assert any("locale=en" in c for c in set_cookie)


def test_set_language_rejects_open_redirect(client):
    r = client.get("/set-language/ru?next=https://evil.com", follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers["Location"]
    assert not loc.startswith("https://evil.com")
