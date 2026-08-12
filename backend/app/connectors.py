"""Connector SDK: pluggable sources of community posts. DemoFixtureSource
(the seeded CommunityPost rows) is always available and is the zero-key
default. Live sources are opt-in (MAGNET_LIVE_SOURCES=1) and public-data-only:
Reddit's and HN's public search endpoints, an honest identifying User-Agent,
one small request per scan (not a crawl), and a hard-fail-safe -- any
network/parse error returns an empty list rather than raising, so one bad
source never breaks the scan pipeline (per the scheduler's resilience
requirement). Product Hunt's API requires an OAuth token; without one it's a
documented no-op rather than a silent fake."""
import json
import os
import urllib.parse
import urllib.request

from .config import USER_AGENT


class Source:
    name = "base"

    def fetch(self, keywords: list) -> list:
        """Returns a list of {source, author, text, url, posted_at} dicts.
        Must never raise -- callers assume best-effort."""
        raise NotImplementedError


class DemoFixtureSource(Source):
    """No-op: DemoFixtureSource's data already lives in CommunityPost rows
    from seed.py. Kept as an explicit class so the Source list is complete
    and self-documenting, not because it needs to fetch anything."""
    name = "demo_fixture"

    def fetch(self, keywords: list) -> list:
        return []


class RedditSource(Source):
    """Reddit's public, unauthenticated search.json endpoint. One request,
    small page size, honest User-Agent. Any failure (rate limit, 403, network)
    degrades to an empty result rather than raising."""
    name = "reddit"

    def fetch(self, keywords: list) -> list:
        if not keywords:
            return []
        query = urllib.parse.quote(" OR ".join(keywords[:3]))
        url = f"https://www.reddit.com/search.json?q={query}&limit=10&sort=new"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
            posts = []
            for child in data.get("data", {}).get("children", []):
                d = child.get("data", {})
                text = d.get("title", "") + " " + (d.get("selftext", "") or "")
                posts.append({
                    "source": "reddit", "author": d.get("author", ""), "text": text.strip()[:500],
                    "url": f"https://reddit.com{d.get('permalink', '')}", "posted_at": None,
                })
            return posts
        except Exception:
            return []


class HNSource(Source):
    """Hacker News via Algolia's public search API (hn.algolia.com) -- built
    for exactly this kind of unauthenticated, low-volume search use."""
    name = "hn"

    def fetch(self, keywords: list) -> list:
        if not keywords:
            return []
        query = urllib.parse.quote(" ".join(keywords[:3]))
        url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage=10"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
            posts = []
            for hit in data.get("hits", []):
                text = hit.get("title", "") + " " + (hit.get("story_text", "") or "")
                posts.append({
                    "source": "hn", "author": hit.get("author", ""), "text": text.strip()[:500],
                    "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    "posted_at": None,
                })
            return posts
        except Exception:
            return []


class ProductHuntSource(Source):
    """Product Hunt's API requires an OAuth token (no public unauthenticated
    search). Without PRODUCTHUNT_API_TOKEN this is a documented no-op, not a
    fake result set."""
    name = "producthunt"

    def fetch(self, keywords: list) -> list:
        if not os.environ.get("PRODUCTHUNT_API_TOKEN"):
            return []
        return []  # not implemented: would need PH's GraphQL API + token


LIVE_SOURCES = [RedditSource(), HNSource(), ProductHuntSource()]
