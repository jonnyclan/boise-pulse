"""Email delivery for The Boise Pulse via Beehiiv.

Platform: Beehiiv (https://beehiiv.com)
  - Free up to 2,500 subscribers
  - Built-in referral / growth program
  - Web archive + analytics out of the box

Setup (one-time):
  1. Create a free Beehiiv account at beehiiv.com
  2. In Beehiiv: Settings -> API -> Generate an API key
  3. Your publication ID is in the URL: app.beehiiv.com/publications/{pub_id}/...
  4. Add both to your .env (see .env.example)

Usage:
  from src.email_sender import send_issue, draft_issue

  # Post as draft (safe for testing -- nothing goes to subscribers yet):
  post_id = draft_issue(html, subject, preview_text)

  # Post as draft AND immediately send to all subscribers:
  post_id = send_issue(html, subject, preview_text)

API reference: https://developers.beehiiv.com/docs/v2
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime


def _api_key() -> str:
    key = os.getenv("BEEHIIV_API_KEY", "").strip()
    if not key:
        raise EnvironmentError(
            "BEEHIIV_API_KEY is not set. "
            "Generate one at: app.beehiiv.com -> Settings -> API"
        )
    return key


def _pub_id() -> str:
    pid = os.getenv("BEEHIIV_PUBLICATION_ID", "").strip()
    if not pid:
        raise EnvironmentError(
            "BEEHIIV_PUBLICATION_ID is not set. "
            "Find it in your Beehiiv URL: app.beehiiv.com/publications/{pub_id}/..."
        )
    return pid


def build_subject(issue_slug: str, date: datetime) -> str:
    """Generate a subject line from the issue type and date."""
    labels = {
        "deep_dive":     "Deep Dive",
        "weekend_guide": "Weekend Guide",
        "quick_hits":    "Quick Hits",
    }
    label = labels.get(issue_slug, "Pulse")
    day_fmt = "%A, %B %#d" if os.name == "nt" else "%A, %B %-d"
    day_str = date.strftime(day_fmt)
    return f"The Boise Pulse - {label} - {day_str}"


def build_preview_text(stories: list[dict]) -> str:
    """Pull the first non-editor headline as the email preview snippet."""
    for s in stories:
        if s.get("writer_key") != "editor_in_chief":
            hed = s.get("headline", "")
            if hed:
                return hed[:140]
    return "Your Boise briefing is ready."


def _beehiiv_request(method: str, path: str, body: dict | None = None) -> dict:
    """Make an authenticated request to the Beehiiv v2 API."""
    base = "https://api.beehiiv.com/v2"
    url = f"{base}{path}"
    data = json.dumps(body).encode("utf-8") if body else None

    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Beehiiv API error {e.code} on {method} {url}:\n{body_text}"
        ) from e


def _create_post(html: str, subject: str, preview_text: str, status: str, email_html: str | None = None) -> str:
    """Create a post via Beehiiv API. Returns the new post_id."""
    pub_id = _pub_id()
    payload = {
        "title": subject,
        "subject": subject,
        "preview_text": preview_text,
        "content": {
            "web": html,
            "email": email_html or html,
        },
        "status": status,
        "audience": "all",
    }
    resp = _beehiiv_request("POST", f"/publications/{pub_id}/posts", payload)
    post = resp.get("data", resp)
    post_id = post.get("id")
    if not post_id:
        raise RuntimeError(f"Beehiiv returned no post id. Full response:\n{resp}")
    return post_id


def draft_issue(html: str, subject: str, preview_text: str, email_html: str | None = None) -> str:
    """Post the issue to Beehiiv as a DRAFT. Returns the Beehiiv post_id."""
    post_id = _create_post(html, subject, preview_text, status="draft", email_html=email_html)
    pub_id = _pub_id()
    draft_url = f"https://app.beehiiv.com/publications/{pub_id}/posts/{post_id}"
    print(f"[email] Draft created: {draft_url}")
    return post_id


def send_issue(html: str, subject: str, preview_text: str, email_html: str | None = None) -> str:
    """Post the issue to Beehiiv and immediately send to all subscribers."""
    post_id = _create_post(html, subject, preview_text, status="confirmed", email_html=email_html)
    pub_id = _pub_id()
    post_url = f"https://app.beehiiv.com/publications/{pub_id}/posts/{post_id}"
    print(f"[email] Sent! View post: {post_url}")
    return post_id


def check_credentials() -> bool:
    """Quick sanity check -- returns True if the API key and pub_id are valid."""
    try:
        pub_id = _pub_id()
        resp = _beehiiv_request("GET", f"/publications/{pub_id}")
        name = resp.get("data", {}).get("name", "unknown")
        print(f"[email] Beehiiv connected: '{name}' (pub_id={pub_id})")
        return True
    except (EnvironmentError, RuntimeError) as e:
        print(f"[email] Credential check failed: {e}")
        return False
