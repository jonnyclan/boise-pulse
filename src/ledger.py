"""Recent-issue memory for The Boise Pulse.

Every generated issue dumps its story payload to
`magazines/YYYY-MM-DD.stories.json`. This module reads the last N of those
files and turns them into a compact "what's already been covered" block that
gets injected into the curation prompt — so Claude can actively avoid
repeating subjects, pull quotes, or opening patterns across issues.

Nothing here talks to the network. Nothing here mutates state. Safe to call
on every generation; returns "" gracefully on the first publish when no
prior issues exist.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAGAZINES_DIR = PROJECT_ROOT / "magazines"

# How many recent issues to consider by default. 12 issues ≈ 4 weeks at the
# Tue/Thu/Fri cadence — long enough to catch monthly repetition, short enough
# that the prompt stays compact.
DEFAULT_WINDOW = 12

# How many recent pieces per writer to echo back. Writers who run every issue
# (Pete on Thu/Fri) need a slightly longer tail to show variety; 4 is plenty
# to nail down repetition patterns without bloating the prompt.
PER_WRITER_LIMIT = 4


def _iter_recent_payloads(window: int) -> list[dict]:
    """Return the last `window` issue payloads, newest first.

    Silently skips corrupt/unreadable files — a bad archive entry should not
    break today's publish.
    """
    if not MAGAZINES_DIR.exists():
        return []
    files = sorted(
        MAGAZINES_DIR.glob("*.stories.json"),
        key=lambda p: p.name,
        reverse=True,
    )[:window]
    out: list[dict] = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        # Stamp the issue date from the filename so callers can show it.
        m = re.match(r"(\d{4}-\d{2}-\d{2})\.stories\.json$", f.name)
        data["_date"] = m.group(1) if m else ""
        out.append(data)
    return out


def _first_sentence(body: str, max_chars: int = 90) -> str:
    """Grab the first sentence-ish chunk of a story body, stripped of markdown."""
    if not body:
        return ""
    # Strip markdown-ish decoration and the Dex's-Drop blockquote that leads
    # some stories — we care about the prose opener, not the formatting.
    cleaned = re.sub(r"^[>\*_#\s]+", "", body.strip().split("\n\n")[0])
    cleaned = re.sub(r"[*_`]", "", cleaned).strip()
    m = re.match(r"(.+?[\.\?\!])(\s|$)", cleaned)
    snippet = m.group(1) if m else cleaned
    if len(snippet) > max_chars:
        snippet = snippet[: max_chars - 1].rstrip() + "…"
    return snippet


def _truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def build_recent_coverage_block(window: int = DEFAULT_WINDOW) -> str:
    """Render a prompt-ready 'what shipped recently' block.

    Groups recent stories by writer_key and shows for each piece: the issue
    date, the topic_label/headline, the first sentence, and the pull quote.
    Empty string if no prior issues exist (first publish).
    """
    payloads = _iter_recent_payloads(window)
    if not payloads:
        return ""

    # writer_key -> list[ (date, story) ]; newest first because payloads are
    # already newest-first. Mock-curator placeholders (source="Mock curator")
    # are filler, not real coverage — they'd tell Claude "don't repeat this
    # placeholder" and waste prompt budget.
    by_writer: dict[str, list[tuple[str, dict]]] = {}
    for p in payloads:
        date = p.get("_date", "")
        for s in p.get("stories", []) or []:
            if (s.get("source") or "").strip().lower() == "mock curator":
                continue
            key = (s.get("writer_key") or "").strip()
            if not key:
                continue
            by_writer.setdefault(key, []).append((date, s))

    if not by_writer:
        return ""

    lines: list[str] = []
    lines.append("=== RECENT COVERAGE — DO NOT REPEAT ===")
    lines.append(
        f"These pieces shipped in the last {len(payloads)} issues. Do not "
        "repeat the subject, the angle, the opening sentence pattern, or "
        "the pull quote. Each writer today must pick something genuinely "
        "new. If the only story a writer has is one they just ran, they "
        "sit this issue out — the curator picks a different writer."
    )
    lines.append("")

    # Stable writer ordering for prompt cache friendliness.
    for writer_key in sorted(by_writer.keys()):
        rows = by_writer[writer_key][:PER_WRITER_LIMIT]
        lines.append(f"**{writer_key}** — last {len(rows)}:")
        for date, s in rows:
            topic = _truncate(s.get("headline") or s.get("topic_label") or "", 70)
            opener = _truncate(_first_sentence(s.get("body", "")), 110)
            quote = _truncate(s.get("pull_quote") or "", 90)
            bits = [f"  {date}: {topic}"]
            if opener:
                bits.append(f"    opened: \"{opener}\"")
            if quote:
                bits.append(f"    pull:   \"{quote}\"")
            lines.append("\n".join(bits))
        lines.append("")

    # A flat list of pull quotes recently used — cheap belt-and-suspenders
    # against verbatim phrase repetition.
    recent_quotes: list[str] = []
    for rows in by_writer.values():
        for _, s in rows[:PER_WRITER_LIMIT]:
            q = (s.get("pull_quote") or "").strip()
            if q:
                recent_quotes.append(q)
    if recent_quotes:
        lines.append("PULL QUOTES USED RECENTLY — do not reuse verbatim:")
        for q in recent_quotes[:24]:
            lines.append(f"  · \"{_truncate(q, 100)}\"")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def recent_fingerprint_set(window: int = DEFAULT_WINDOW) -> set[str]:
    """Return a set of (writer_key, headline-lowercased) fingerprints for
    recent stories. Callable from lints or tests to assert no exact repeat."""
    payloads = _iter_recent_payloads(window)
    out: set[str] = set()
    for p in payloads:
        for s in p.get("stories", []) or []:
            key = (s.get("writer_key") or "").strip()
            head = (s.get("headline") or "").strip().lower()
            if key and head:
                out.add(f"{key}::{head}")
    return out
