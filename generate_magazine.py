"""Lean orchestrator for The Boise Pulse.

Pipeline:
  1. Fetch all data sources (never raises)
  2. Hand raw data to the AI curator (Claude / Gemini / mock)
  3. Render the returned story list into HTML
  4. Write magazines/YYYY-MM-DD.html
  5. Regenerate magazines/index.html (archive)

Run: python generate_magazine.py
Env: see .env.example
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Allow running as a script from the project root
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src import ai_engine, data_sources, html_renderer, issue_types, voice_lint  # noqa: E402
from src import vitals as pulse_vitals  # noqa: E402
from src import email_renderer as email_render  # noqa: E402

MAGAZINES_DIR = PROJECT_ROOT / "magazines"

# Weekdays on which we publish by default (Python: Mon=0, Sun=6).
PUBLISH_WEEKDAYS = {1, 3, 4}  # Tue / Thu / Fri


def _mountain_now() -> datetime:
    """Return current time in US Mountain (Boise). Falls back to a fixed
    -06:00 offset on systems without IANA tzdata (e.g. Windows without `tzdata`)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(tz=ZoneInfo("America/Denver"))
    except Exception:
        # Rough approximation — good enough for a date stamp on the issue.
        return datetime.now(tz=timezone(timedelta(hours=-6)))


def _load_dotenv() -> None:
    """Load .env into os.environ. A non-empty shell override wins; an existing
    EMPTY env var (common on Windows when a key has been declared-but-unset)
    does not block the .env value."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if os.environ.get(key):  # non-empty shell value wins
            continue
        os.environ[key] = val


def _resolve_issue(date: datetime):
    """Pick the issue config. FORCE_ISSUE_TYPE=<slug> env var wins."""
    forced = os.getenv("FORCE_ISSUE_TYPE", "").strip()
    if forced:
        return issue_types.by_slug(forced)
    return issue_types.for_date(date)


def build_issue(date: datetime) -> Path:
    issue = _resolve_issue(date)
    print(f"[{datetime.now().isoformat(timespec='seconds')}] Fetching raw data…")
    print(f"  issue type: {issue['masthead_label']} ({len(issue['spread_plan'])} spreads)")
    raw = data_sources.fetch_all()
    empty = raw.get("_meta", {}).get("empty_sources", [])
    if empty:
        print(f"  [warn] empty sources: {empty}")

    # Gemini research handoff — load today's pre-generated research file if present.
    # This is the ONLY way Gemini data enters the pipeline now.
    # No API fallback. If no research file exists, Claude self-selects stories.
    research_data = None
    _research_path = PROJECT_ROOT / "research" / f"{date.strftime('%Y-%m-%d')}.json"
    if _research_path.exists():
        _age_hours = (time.time() - _research_path.stat().st_mtime) / 3600
        if _age_hours < 18:
            try:
                _research = json.loads(_research_path.read_text(encoding="utf-8"))
                research_data = _research
                if _research.get("assignments"):
                    raw = dict(raw)
                    raw["story_assignments"] = _research["assignments"]
                    print(
                        f"[research] Loaded research file ({_age_hours:.1f}h old) — "
                        f"{len(_research['assignments'])} writer assignments locked."
                    )
                else:
                    print("[research] Research file found but no assignments — Claude will self-select.")
            except Exception as _e:
                print(f"[research] Could not load research file ({_e}) — Claude will self-select.")
        else:
            print(f"[research] Research file is {_age_hours:.1f}h old (>18h) — Claude will self-select.")
    else:
        print("[research] No research file for today — Claude will self-select stories.")

    print("Curating stories…")
    stories = ai_engine.curate(raw, date, issue=issue)
    print(f"  got {len(stories)} stories; spreads = "
          f"{[s.get('spread_type') for s in stories]}")

    findings = voice_lint.lint(stories, issue["spread_plan"], issue_slug=issue["slug"])
    voice_lint.report(findings)

    # Write debug payload and render HTML before enforcing — so stories.json
    # and the rendered preview exist even when the issue has lint FAILs.
    MAGAZINES_DIR.mkdir(parents=True, exist_ok=True)
    debug_path = MAGAZINES_DIR / f"{date.strftime('%Y-%m-%d')}.stories.json"
    debug_path.write_text(
        json.dumps(
            {"_meta": raw.get("_meta", {}), "issue": issue, "stories": stories},
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Rendering HTML…")
    vitals = pulse_vitals.build_vitals(raw, research_data, date)
    html = html_renderer.render_issue(date, stories, issue=issue, vitals=vitals)

    out_path = MAGAZINES_DIR / f"{date.strftime('%Y-%m-%d')}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"  wrote {out_path} ({len(html):,} bytes)")

    web_base = os.getenv("WEB_BASE_URL", "https://boisepulse.com").rstrip("/")
    web_url = f"{web_base}/{date.strftime('%Y-%m-%d')}.html"
    email_html = email_render.render_email_issue(date, stories, issue=issue, vitals=vitals, web_url=web_url)
    email_path = MAGAZINES_DIR / f"{date.strftime('%Y-%m-%d')}.email.html"
    email_path.write_text(email_html, encoding="utf-8")
    print(f"  wrote {email_path} ({len(email_html):,} bytes)")

    voice_lint.enforce(findings)
    return out_path


def regenerate_archive(date: datetime) -> Path:
    issues: list[dict] = []
    for f in sorted(MAGAZINES_DIR.glob("*.html"), reverse=True):
        if f.name == "index.html":
            continue
        m = re.match(r"(\d{4}-\d{2}-\d{2})\.html$", f.name)
        if not m:
            continue
        iso = m.group(1)
        lead_headline = _sniff_lead_headline(f)
        issues.append(
            {"date": iso, "lead_headline": lead_headline, "filename": f.name}
        )
    index_html = html_renderer.render_archive_index(date, issues)
    idx_path = MAGAZINES_DIR / "index.html"
    idx_path.write_text(index_html, encoding="utf-8")
    print(f"Archive index: {idx_path} ({len(issues)} issue(s))")
    return idx_path


def _sniff_lead_headline(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    m = re.search(r'class="headline"[^>]*>(.+?)<', content, re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return "Today's issue"


def main() -> int:
    """Entry point called by pre_publish_check.py and the bat files."""
    _load_dotenv()
    date = _mountain_now()
    try:
        build_issue(date)
        regenerate_archive(date)
        print(f"\n[done] Open file:///{(MAGAZINES_DIR / (date.strftime('%Y-%m-%d') + '.html')).as_posix()}")
        return 0
    except SystemExit as exc:
        # voice_lint.enforce raises SystemExit(1) on hard FAILs
        code = exc.code if isinstance(exc.code, int) else 1
        return code
    except Exception as exc:
        import traceback
        print(f"\n[ERROR] Pipeline crashed: {exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
