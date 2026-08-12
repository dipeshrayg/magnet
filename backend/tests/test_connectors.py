import json
from unittest.mock import patch

from app.connectors import HNSource, ProductHuntSource, RedditSource


def test_reddit_source_parses_response():
    fake_response = {
        "data": {"children": [{"data": {
            "title": "Looking for a scheduling tool", "selftext": "any recommendations?",
            "author": "alice", "permalink": "/r/test/1",
        }}]},
    }
    with patch("app.connectors.urllib.request.urlopen") as mock_open:
        body = json.dumps(fake_response).encode()
        mock_open.return_value.__enter__.return_value.read.return_value = body
        posts = RedditSource().fetch(["scheduling"])
    assert len(posts) == 1
    assert posts[0]["source"] == "reddit"
    assert "scheduling tool" in posts[0]["text"]


def test_reddit_source_fails_gracefully():
    with patch("app.connectors.urllib.request.urlopen", side_effect=OSError("blocked")):
        posts = RedditSource().fetch(["scheduling"])
    assert posts == []


def test_hn_source_parses_response():
    fake_response = {"hits": [{"title": "Show HN: a shipping API", "author": "bob", "objectID": "123"}]}
    with patch("app.connectors.urllib.request.urlopen") as mock_open:
        body = json.dumps(fake_response).encode()
        mock_open.return_value.__enter__.return_value.read.return_value = body
        posts = HNSource().fetch(["shipping"])
    assert len(posts) == 1
    assert posts[0]["source"] == "hn"


def test_hn_source_fails_gracefully():
    with patch("app.connectors.urllib.request.urlopen", side_effect=OSError("timeout")):
        posts = HNSource().fetch(["shipping"])
    assert posts == []


def test_empty_keywords_short_circuit():
    assert RedditSource().fetch([]) == []
    assert HNSource().fetch([]) == []


def test_producthunt_is_documented_noop_without_token(monkeypatch):
    monkeypatch.delenv("PRODUCTHUNT_API_TOKEN", raising=False)
    assert ProductHuntSource().fetch(["shipping"]) == []
