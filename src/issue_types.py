"""Issue-type configurations for The Boise Pulse's 3x/week cadence.

Tuesday   — The Deep Dive (meatier voices, longer-form spreads, 6 stories)
Thursday  — The Weekend Guide (event-adjacent voices, listings-heavy, 8 stories)
Friday    — Quick Hits (snappy voices, fewer spreads, 5 stories)

Each config declares:
  - `slug`             short id ("deep_dive", "weekend_guide", "quick_hits")
  - `masthead_label`   text under the nameplate ("THE DEEP DIVE  ·  TUESDAY")
  - `story_count`      N writer-driven stories. NOTE: every issue ALSO has a
                       "Today's Edition" editor's note (Maggie Halstead) in
                       slot 1, so total rendered spreads = story_count + 1.
  - `writer_pool`      writers who DEFAULT into this day's rotation
  - `spread_plan`      ordered list of spread_types. First entry is always
                       "todays_edition" (the editor's opener). Length equals
                       story_count + 1.
  - `tone_hint`        one-line flavor direction for the curator
  - `weather_mandatory` whether Pete must appear (True for Thu/Fri, False for Tue)
  - `override_rule`    when a non-pool writer earns an exception slot
"""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict


class IssueConfig(TypedDict):
    slug: str
    masthead_label: str
    story_count: int
    writer_pool: list[str]
    spread_plan: list[str]
    tone_hint: str
    weather_mandatory: bool
    override_rule: str


TUESDAY_DEEP_DIVE: IssueConfig = {
    "slug": "deep_dive",
    "masthead_label": "THE DEEP DIVE  ·  TUESDAY",
    "story_count": 6,
    "writer_pool": ["sports", "history", "editorial", "real_estate"],
    # Long-form / substantive spreads. No retro_weather, no rose_stamp, no
    # midnight, no terminal — those are weekend/news spreads.
    "spread_plan": ["todays_edition", "hero", "academic", "broadsheet", "big_stat", "editorial", "broadside"],
    "tone_hint": (
        "Tuesday is meatier. Every story earns its spread through substance, not "
        "novelty. Bodies run 4–5 paragraphs, 100–140 words each. Reward the reader "
        "who sits with the magazine for 10 minutes. If a story can't sustain a deep "
        "read, it belongs on Friday, not today."
    ),
    "weather_mandatory": False,
    "override_rule": (
        "Writers outside the pool (weather, food, arts, trending, lifestyle) may "
        "claim ONE Tuesday slot IF their beat has genuinely big news — a major "
        "artist announcement, a restaurant closure of civic significance, a "
        "weather emergency, a viral Boise story that's crossed into national "
        "coverage. The bar is: 'this story would lead a national story about "
        "Boise.' If in doubt, stick to the pool. Lifestyle/TikTok trends almost "
        "never earn Tuesday — Tuesday is substance day."
    ),
}


THURSDAY_WEEKEND_GUIDE: IssueConfig = {
    "slug": "weekend_guide",
    "masthead_label": "THE WEEKEND GUIDE  ·  THURSDAY",
    "story_count": 8,
    "writer_pool": ["food", "arts", "weather", "trending", "lifestyle"],
    # Event-forward mix. Listings spread (uses broadsheet for now; will become
    # a dedicated 'listings' spread type when the Ticketmaster/Eventbrite
    # integrations land).
    "spread_plan": ["todays_edition", "hero", "broadsheet", "rose_stamp", "retro_weather", "midnight", "editorial", "big_stat", "broadside"],
    "tone_hint": (
        "Thursday is the weekend briefing. Readers open this to PLAN Friday–"
        "Sunday. Lead with events. Weather gets early placement because it "
        "changes plans. Food and arts pieces are PICKS with opinions (Nina's "
        "verdict, Dex's drop), not reviews. Every story should answer: 'why "
        "would a Boisean go out for this?'"
    ),
    "weather_mandatory": True,
    "override_rule": (
        "Writers outside the pool (sports, history, real_estate, editorial) may "
        "claim ONE Thursday slot IF their beat produces a clearly weekend-"
        "relevant story — a Steelheads playoff home game, a Wade drive-by "
        "piece about a spot the reader can actually visit this weekend, a "
        "neighborhood open-house crawl, a council meeting the community is "
        "organizing around. Everyday news belongs on Friday."
    ),
}


FRIDAY_QUICK_HITS: IssueConfig = {
    "slug": "quick_hits",
    "masthead_label": "QUICK HITS  ·  FRIDAY",
    "story_count": 5,
    "writer_pool": ["trending", "sports", "editorial", "weather", "lifestyle"],
    # Short, fast, news-dense. Shorter spreads favored (rose_stamp, midnight,
    # terminal), with one editorial kicker.
    "spread_plan": ["todays_edition", "hero", "rose_stamp", "retro_weather", "midnight", "broadside"],
    "tone_hint": (
        "Friday is short, fast, and aimed at the commute. Bodies run 2–3 "
        "paragraphs, 60–90 words each. No windups. Lead with the news the "
        "reader will actually talk about this weekend. Sports = game previews "
        "not game recaps. Weather = Thursday's forecast updated. The kicker "
        "(broadside) sends the reader into the weekend with something quotable."
    ),
    "weather_mandatory": True,
    "override_rule": (
        "Writers outside the pool (history, food, arts, real_estate) may claim "
        "ONE Friday slot IF their beat has breaking news. Friday is reactive: "
        "if a story broke Thursday after our Thursday send, Friday is its home."
    ),
}

# Note on Hayley (lifestyle): she's in both Thu and Fri pools but appears at
# MOST ONCE per week — her format (test-it-and-score-it) loses its punch if
# it runs back-to-back. Thursday when the piece is a weekend project; Friday
# when the piece is a short punchy trend verdict. Never both.


# Mapping: Python weekday() → IssueConfig. Monday=0, Sunday=6.
# Non-publish days return None (cron should not fire, but the generator handles
# it gracefully if somebody runs it manually).
_WEEKDAY_MAP: dict[int, IssueConfig] = {
    1: TUESDAY_DEEP_DIVE,    # Tuesday
    3: THURSDAY_WEEKEND_GUIDE,  # Thursday
    4: FRIDAY_QUICK_HITS,    # Friday
}


def for_date(date: datetime) -> IssueConfig:
    """Return the issue config for the given date.

    Non-publish days (Mon/Wed/Sat/Sun) fall back to TUESDAY_DEEP_DIVE so that
    a manual run always produces something — useful for previews and one-off
    generation. Production cron only triggers on Tue/Thu/Fri, so this fallback
    is purely a developer-ergonomics choice.
    """
    return _WEEKDAY_MAP.get(date.weekday(), TUESDAY_DEEP_DIVE)


def by_slug(slug: str) -> IssueConfig:
    """Look up a config by its slug (for FORCE_ISSUE_TYPE overrides)."""
    by = {c["slug"]: c for c in (TUESDAY_DEEP_DIVE, THURSDAY_WEEKEND_GUIDE, FRIDAY_QUICK_HITS)}
    if slug not in by:
        raise ValueError(f"Unknown issue slug: {slug!r}. Known: {list(by)}")
    return by[slug]
