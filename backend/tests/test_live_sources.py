from unittest.mock import patch

from .conftest import make_workspace


def test_scan_ignores_live_sources_when_disabled(client, monkeypatch):
    monkeypatch.delenv("MAGNET_LIVE_SOURCES", raising=False)
    ws = make_workspace(client, "LiveOff")
    r = client.post(f"/api/workspaces/{ws['id']}/leads/scan")
    assert r.json()["live_posts_ingested"] == 0


def test_scan_ingests_live_sources_when_enabled(client, monkeypatch):
    monkeypatch.setenv("MAGNET_LIVE_SOURCES", "1")
    fake_posts = [{
        "source": "reddit", "author": "x", "text": "manual busywork scheduling",
        "url": "https://x/1", "posted_at": None,
    }]
    with patch("app.routers.growth.LIVE_SOURCES", [_FakeSource(fake_posts)]):
        ws = make_workspace(client, "LiveOn")
        r = client.post(f"/api/workspaces/{ws['id']}/leads/scan")
    assert r.json()["live_posts_ingested"] == 1

    posts = client.get(f"/api/workspaces/{ws['id']}/leads").json()
    assert any(p["source"] == "reddit" for p in posts)


def test_a_failing_live_source_does_not_break_the_scan(client, monkeypatch):
    monkeypatch.setenv("MAGNET_LIVE_SOURCES", "1")
    with patch("app.routers.growth.LIVE_SOURCES", [_ExplodingSource()]):
        ws = make_workspace(client, "LiveBroken")
        r = client.post(f"/api/workspaces/{ws['id']}/leads/scan")
    assert r.status_code == 200
    assert r.json()["live_posts_ingested"] == 0


class _FakeSource:
    def __init__(self, posts):
        self._posts = posts

    def fetch(self, keywords):
        return self._posts


class _ExplodingSource:
    def fetch(self, keywords):
        raise RuntimeError("network unavailable")
