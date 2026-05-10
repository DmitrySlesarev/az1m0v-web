def test_project_readme_renders_fetched_html(client, monkeypatch):
    def fake_fetch(branch, repo_url=None):
        assert branch == "master"
        assert repo_url and "github.com" in repo_url
        return "<p>TestReadmeBody</p>", None

    monkeypatch.setattr("app.routes.fetch_readme_html", fake_fetch)
    r = client.get("/project/readme")
    assert r.status_code == 200
    assert b"TestReadmeBody" in r.data


def test_project_readme_shows_error_when_fetch_fails(client, monkeypatch):
    monkeypatch.setattr(
        "app.routes.fetch_readme_html",
        lambda b, repo_url=None: (None, "404"),
    )
    r = client.get("/project/readme")
    assert r.status_code == 200
    data = r.get_data(as_text=True)
    assert "404" in data or "Could not load" in data
