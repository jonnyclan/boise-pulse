"""Data source fetchers for The Boise Pulse.

Every fetcher must return a safe default on failure (empty list or empty dict).
Never raise — we never miss a morning.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

USER_AGENT = "BoisePulse/0.1 (https://boisepulse.com)"
TIMEOUT = 15  # seconds


# ────────────────────────────────────────────────────────────
# low-level HTTP
# ────────────────────────────────────────────────────────────
def _http_get(url: str, headers: dict | None = None) -> bytes | None:
    """GET a URL, return bytes or None on any failure."""
    req_headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None


def _http_get_json(url: str, headers: dict | None = None) -> Any | None:
    body = _http_get(url, headers=headers)
    if not body:
        return None
    try:
        return json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return None


# ────────────────────────────────────────────────────────────
# Google News RSS — 6 topical queries
# ────────────────────────────────────────────────────────────
NEWS_QUERIES = {
    "general": "Boise Idaho",
    "sports": "Boise State OR Broncos OR \"Idaho Steelheads\" OR \"Boise Hawks\"",
    "weather": "Boise weather",
    "arts": "Boise arts OR music OR Treefort",
    "real_estate": "Boise real estate OR housing",
    "tech": "Boise tech OR startup Idaho",
}


def fetch_google_news(query: str, limit: int = 6) -> list[dict]:
    """Return up to `limit` items from Google News RSS for a query.
    Each item: {title, link, source, published}.
    """
    q = urllib.parse.quote_plus(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
    body = _http_get(url)
    if not body:
        return []
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return []

    items = []
    for item in root.findall(".//item")[:limit]:
        title_el = item.find("title")
        link_el = item.find("link")
        src_el = item.find("source")
        pub_el = item.find("pubDate")
        if title_el is None or link_el is None:
            continue
        items.append(
            {
                "title": (title_el.text or "").strip(),
                "link": (link_el.text or "").strip(),
                "source": (src_el.text if src_el is not None else "").strip(),
                "published": (pub_el.text if pub_el is not None else "").strip(),
            }
        )
    return items


def fetch_all_news() -> dict[str, list[dict]]:
    """Fetch all 6 news topic buckets. Returns dict keyed by topic."""
    return {topic: fetch_google_news(q) for topic, q in NEWS_QUERIES.items()}


# ────────────────────────────────────────────────────────────
# NWS — Boise forecast
# ────────────────────────────────────────────────────────────
BOISE_LAT, BOISE_LON = 43.6150, -116.2023


def fetch_nws_forecast() -> dict:
    """Return {'periods': [{'name','temperature','shortForecast','detailedForecast'}...]}.
    Safe default on failure: {'periods': []}.
    """
    # Step 1 — get the gridpoint
    points = _http_get_json(
        f"https://api.weather.gov/points/{BOISE_LAT},{BOISE_LON}",
        headers={"Accept": "application/geo+json"},
    )
    if not points:
        return {"periods": []}
    try:
        forecast_url = points["properties"]["forecast"]
    except (KeyError, TypeError):
        return {"periods": []}

    # Step 2 — fetch the forecast
    forecast = _http_get_json(
        forecast_url, headers={"Accept": "application/geo+json"}
    )
    if not forecast:
        return {"periods": []}
    try:
        periods = forecast["properties"]["periods"][:6]
    except (KeyError, TypeError):
        return {"periods": []}

    trimmed = [
        {
            "name": p.get("name", ""),
            "temperature": p.get("temperature"),
            "temperatureUnit": p.get("temperatureUnit", "F"),
            "shortForecast": p.get("shortForecast", ""),
            "detailedForecast": p.get("detailedForecast", ""),
            "windSpeed": p.get("windSpeed", ""),
            "windDirection": p.get("windDirection", ""),
        }
        for p in periods
    ]
    return {"periods": trimmed}


# ────────────────────────────────────────────────────────────
# Wikipedia On-This-Day
# ────────────────────────────────────────────────────────────
def fetch_on_this_day(date: datetime | None = None, limit: int = 5) -> list[dict]:
    """Return up to `limit` 'events' from Wikipedia On-This-Day."""
    if date is None:
        date = datetime.now(timezone.utc)
    mm = f"{date.month:02d}"
    dd = f"{date.day:02d}"
    url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/{mm}/{dd}"
    data = _http_get_json(url)
    if not data:
        return []
    events = data.get("events", []) if isinstance(data, dict) else []
    out = []
    for e in events[:limit]:
        text = e.get("text", "")
        year = e.get("year", "")
        pages = e.get("pages", []) or []
        first_page = pages[0] if pages else {}
        out.append(
            {
                "year": year,
                "text": text,
                "page_title": first_page.get("normalizedtitle", ""),
                "page_extract": first_page.get("extract", ""),
            }
        )
    return out


# ────────────────────────────────────────────────────────────
# Reddit r/Boise (unauthenticated fallback)
# ────────────────────────────────────────────────────────────
def fetch_reddit_boise(limit: int = 12) -> list[dict]:
    """Top hot posts from r/Boise. Uses OAuth when Reddit creds are set; else
    the unauthenticated .json endpoint. Returns empty list on failure.
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    posts: list[dict] = []

    if client_id and client_secret:
        posts = _fetch_reddit_oauth(client_id, client_secret, limit)
    if posts:
        return posts

    # Fallback: unauthenticated
    url = f"https://www.reddit.com/r/Boise/hot.json?limit={limit}"
    data = _http_get_json(url)
    if not data:
        return []
    try:
        children = data["data"]["children"]
    except (KeyError, TypeError):
        return []
    return [_reddit_item(c.get("data", {})) for c in children[:limit]]


def _fetch_reddit_oauth(cid: str, secret: str, limit: int) -> list[dict]:
    """Try OAuth token flow. On any failure, return []."""
    import base64

    auth = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=data,
        headers={
            "Authorization": f"Basic {auth}",
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            token_body = json.loads(resp.read())
    except Exception:
        return []
    token = token_body.get("access_token")
    if not token:
        return []
    listing = _http_get_json(
        f"https://oauth.reddit.com/r/Boise/hot?limit={limit}",
        headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT},
    )
    if not listing:
        return []
    try:
        children = listing["data"]["children"]
    except (KeyError, TypeError):
        return []
    return [_reddit_item(c.get("data", {})) for c in children[:limit]]


def _reddit_item(d: dict) -> dict:
    return {
        "title": d.get("title", ""),
        "score": d.get("score", 0),
        "num_comments": d.get("num_comments", 0),
        "permalink": "https://www.reddit.com" + d.get("permalink", ""),
        "author": d.get("author", ""),
        "selftext": (d.get("selftext", "") or "")[:400],
    }


# ────────────────────────────────────────────────────────────
# YouTube Data API v3 (keyed)
# ────────────────────────────────────────────────────────────
def fetch_youtube_boise(limit: int = 8) -> list[dict]:
    """Trending Boise videos via YouTube search. Empty list if key missing or failure."""
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        return []
    q = urllib.parse.quote_plus("Boise Idaho")
    url = (
        "https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&q={q}&type=video&order=viewCount"
        f"&maxResults={limit}&publishedAfter="
        + _hours_ago_iso(48)
        + f"&key={key}"
    )
    data = _http_get_json(url)
    if not data or "items" not in data:
        return []
    out = []
    for it in data["items"][:limit]:
        s = it.get("snippet", {}) or {}
        vid = (it.get("id", {}) or {}).get("videoId", "")
        out.append(
            {
                "title": s.get("title", ""),
                "channel": s.get("channelTitle", ""),
                "published": s.get("publishedAt", ""),
                "description": (s.get("description", "") or "")[:300],
                "video_id": vid,
                "link": f"https://www.youtube.com/watch?v={vid}" if vid else "",
            }
        )
    return out


def _hours_ago_iso(hours: int) -> str:
    from datetime import timedelta

    t = datetime.now(timezone.utc) - timedelta(hours=hours)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


# ────────────────────────────────────────────────────────────
# Aggregator
# ────────────────────────────────────────────────────────────
def fetch_all() -> dict:
    """Fetch every source. Never raises. Missing sources → empty collections.
    Includes a _meta.errors list noting which sources came back empty.
    """
    news = fetch_all_news()
    weather = fetch_nws_forecast()
    on_this_day = fetch_on_this_day()
    reddit = fetch_reddit_boise()
    youtube = fetch_youtube_boise()

    empty = []
    if not any(news.values()):
        empty.append("news")
    if not weather["periods"]:
        empty.append("nws")
    if not on_this_day:
        empty.append("wikipedia_otd")
    if not reddit:
        empty.append("reddit")
    if not youtube:
        empty.append("youtube")

    return {
        "news": news,
        "weather": weather,
        "on_this_day": on_this_day,
        "reddit": reddit,
        "youtube": youtube,
        "_meta": {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "empty_sources": empty,
        },
    }


if __name__ == "__main__":
    # Quick smoke test
    data = fetch_all()
    print(json.dumps({k: len(v) if isinstance(v, list) else "ok" for k, v in data.items()}, indent=2))
    print("empty:", data["_meta"]["empty_sources"])
