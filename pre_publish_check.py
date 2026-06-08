#!/usr/bin/env python3
"""Pre-publish smoke check — run the full pipeline then eyeball-check the
output in one pass. Prints a concise report covering:

  - lint verdict (FAIL / WARN counts)
  - writer-assignment table with spread pairings
  - writer duplication flags (hard FAIL)
  - signature-line presence (Pete's MOOD OF THE SKY, Nina's Table, Dex's Drop)
  - final GO / NO-GO verdict

Usage:  python pre_publish_check.py [--preview] [--send | --draft]

Flags:
  --preview   On GO verdict, auto-open the rendered HTML in the default browser.
  --draft     On GO verdict, post to Beehiiv as a DRAFT (proof before sending).
  --send      On GO verdict, post to Beehiiv and SEND to all subscribers.
              Requires BEEHIIV_API_KEY and BEEHIIV_PUBLICATION_ID in .env.

Exit code 0 = GO, 1 = NO-GO. Intended to be run right before distribution
so you can gut-check the issue in under 60 seconds.
"""
from __future__ import annotations

import json
import os
import sys
import webbrowser
from collections import Counter
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
MAGAZINES_DIR = PROJECT_ROOT / "magazines"
sys.path.insert(0, str(PROJECT_ROOT))


def _run_email_step(issue_date: str, stories: list[dict], send: bool) -> None:
    """Post the rendered HTML to Beehiiv as a draft or live send."""
    from src.email_sender import build_subject, build_preview_text, send_issue, draft_issue
    from src.issue_types import for_date

    html = _load_html(issue_date)
    if not html:
        print(f"[email] SKIPPED -- {issue_date}.html not found in magazines/")
        return

    try:
        date = datetime.strptime(issue_date, "%Y-%m-%d")
    except ValueError:
        print(f"[email] SKIPPED -- couldn't parse date from '{issue_date}'")
        return

    issue = for_date(date)
    subject = build_subject(issue["slug"], date)
    preview = build_preview_text(stories)

    print(f"\n[email] Subject:  {subject}")
    print(f"[email] Preview:  {preview}")

    email_html = _load_email_html(issue_date)
    if email_html:
        print(f"[email] Inbox version: {len(email_html):,} bytes of email-safe HTML.")
    try:
        if send:
            print("[email] Sending to all subscribers ...")
            send_issue(html, subject, preview, email_html=email_html)
        else:
            print("[email] Posting as draft (--draft mode, no send) ...")
            draft_issue(html, subject, preview, email_html=email_html)
    except (EnvironmentError, RuntimeError) as exc:
        print(f"[email] ERROR: {exc}")
        print("[email] Issue was not sent. Check your .env (BEEHIIV_API_KEY, BEEHIIV_PUBLICATION_ID).")


def _load_latest_stories() -> tuple[str, list[dict]]:
    """Find the most recently written stories.json in magazines/."""
    stories_files = sorted(
        MAGAZINES_DIR.glob("*.stories.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not stories_files:
        raise SystemExit("[ERROR] No stories.json found in magazines/ -- run generate_magazine.py first.")
    latest = stories_files[0]
    data = json.loads(latest.read_text(encoding="utf-8"))
    stories = data if isinstance(data, list) else data.get("stories", [])
    return latest.name.replace(".stories.json", ""), stories


def _signature_check(stories: list[dict]) -> list[str]:
    """Verify writer signature lines made it into the final copy."""
    misses = []
    for s in stories:
        writer = (s.get("writer_key") or "").lower()
        body = s.get("body", "") or ""
        rbc = s.get("recurring_bit_content", "") or ""
        combined = body + " " + rbc

        if writer == "weather" and "MOOD OF THE SKY" not in combined:
            misses.append(f"Pete (weather, slot {s.get('slot','?')}): missing 'MOOD OF THE SKY:' opener")
        elif writer == "food" and "Nina's Table" not in combined and "Nina\u2019s Table" not in combined:
            misses.append(f"Nina (food, slot {s.get('slot','?')}): missing Nina's Table sig line")
        elif writer == "arts" and "Dex's Drop" not in combined and "Dex\u2019s Drop" not in combined:
            misses.append(f"Dex (arts, slot {s.get('slot','?')}): missing Dex's Drop opener")
        elif writer == "trending" and "FRESH OFF THE PRESS" not in combined:
            misses.append(f"Jess (trending, slot {s.get('slot','?')}): missing 'FRESH OFF THE PRESS' box")
        elif writer == "history" and "DRIVE-BY HISTORY" not in combined and "Arlene" not in combined:
            misses.append(f"Wade (history, slot {s.get('slot','?')}): missing history anchor")
    return misses


def _load_html(issue_date: str) -> str | None:
    """Read the rendered HTML for a given issue date slug."""
    html_path = MAGAZINES_DIR / f"{issue_date}.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return None


def _load_email_html(issue_date: str) -> str | None:
    """Read the email-safe HTML (inbox version) for a given issue date slug."""
    p = MAGAZINES_DIR / f"{issue_date}.email.html"
    return p.read_text(encoding="utf-8") if p.exists() else None


def main() -> int:
    preview = "--preview" in sys.argv
    do_send  = "--send"  in sys.argv
    do_draft = "--draft" in sys.argv

    print("=" * 70)
    print("PRE-PUBLISH SMOKE CHECK -- Boise Pulse")
    print("=" * 70)

    # Step 1: run the full pipeline
    print("\n[1/3] Running generate_magazine.py (USE_REAL_AI should be 1) ...")
    os.environ.setdefault("USE_REAL_AI", "1")
    os.environ.setdefault("RETRY_ON_FAIL", "1")
    sys.path.insert(0, str(PROJECT_ROOT))
    import generate_magazine

    rc = generate_magazine.main()
    if rc != 0:
        print(f"\n[NO-GO] generate_magazine.py exited with code {rc}")
        return 1

    # Step 2: load stories and build report
    print("\n[2/3] Loading latest stories.json ...")
    issue_date, stories = _load_latest_stories()
    print(f"  loaded {len(stories)} stories from {issue_date}.stories.json")

    # Writer-assignment table
    print("\n[3/3] Report:")
    print("-" * 70)
    print(f"{'SLOT':<5} {'SPREAD':<18} {'WRITER':<18} {'HEADLINE':<35}")
    print("-" * 70)
    for i, s in enumerate(stories):
        spread = str(s.get("spread_type", "?"))[:17]
        writer = str(s.get("writer_key", "?"))[:17]
        hed = str(s.get("headline", ""))[:34]
        print(f"{i:<5} {spread:<18} {writer:<18} {hed:<35}")

    # Duplication check (hard FAIL)
    writer_counts = Counter(s.get("writer_key") for s in stories)
    dups = [(w, n) for w, n in writer_counts.items() if n > 1 and w != "editor_in_chief"]

    # Signature check
    sig_misses = _signature_check(stories)

    # Final verdict
    print("\n" + "=" * 70)
    problems = []
    if dups:
        problems.append(f"WRITER 2x DUPLICATION: {dups}")
    if sig_misses:
        problems.extend(f"SIGNATURE MISS: {m}" for m in sig_misses)

    if not problems:
        print("VERDICT: GO -- ship it.")
        print("=" * 70)

        if preview:
            html_path = MAGAZINES_DIR / f"{issue_date}.html"
            if html_path.exists():
                print(f"[preview] opening {html_path} ...")
                webbrowser.open(html_path.as_uri())
            else:
                print(f"[preview] skipped -- {html_path} not found")

        if do_send or do_draft:
            _run_email_step(issue_date, stories, send=do_send)

        return 0

    print("VERDICT: NO-GO (or at least eyeball before ship)")
    print("-" * 70)
    for p in problems:
        print(f"  !! {p}")
    print("=" * 70)
    return 1


if __name__ == "__main__":
    sys.exit(main())
