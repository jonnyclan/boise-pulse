"""AI curation engine for The Boise Pulse.

Two-phase design:
  Phase 1: curate() — single AI call (or mock) that returns a list of 10 story
           dicts matching the schema in SPEC.md §9.
  Phase 2: render (see html_renderer.py).

Backends, in priority order:
  1. Claude Sonnet 4.6 via anthropic SDK (if ANTHROPIC_API_KEY)
  2. Mock — deterministic, built from the fetched data. Always works.

For first-iteration work the mock is the default; real backends are off unless
both (a) the env var is set and (b) USE_REAL_AI=1 is set.

Note: Gemini is used for RESEARCH only (Jon runs prompts manually in the Gemini
web app and pastes output to Claude). There is no Gemini AI writing backend.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any

from .personas import PERSONAS, all_prompt_voices
from .issue_types import IssueConfig, for_date as _issue_for_date
from . import ledger


# ────────────────────────────────────────────────────────────
# Public entry point
# ────────────────────────────────────────────────────────────
def curate(raw_data: dict, date: datetime, issue: IssueConfig | None = None) -> list[dict]:
    """Return a list of validated story dicts for today's issue.

    `issue` selects the issue type (Tue deep dive / Thu weekend guide / Fri
    quick hits). If omitted, we infer it from the date's weekday.
    """
    issue = issue or _issue_for_date(date)
    # Total rendered spreads = len(spread_plan). When the plan opens with
    # "todays_edition", slot 1 is Maggie Halstead's editor's note and the
    # remaining slots are writer-driven stories (story_count of them).
    count = len(issue["spread_plan"])

    if os.getenv("USE_REAL_AI") == "1":
        print(f"[ai_engine] USE_REAL_AI=1; ANTHROPIC_API_KEY="
              f"{'set' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING'}")
        try:
            stories = _curate_with_claude(raw_data, date, issue)
            print(f"[ai_engine] Claude returned: "
                  f"{'None' if stories is None else str(len(stories)) + ' stories'}")

            # Retry-on-FAIL: run voice_lint against the first draft; if any
            # FAIL findings exist, call Claude once more with a correction
            # block appended to the prompt. Opt-out via RETRY_ON_FAIL=0.
            # Cost ceiling: at most 2 Claude calls per issue.
            if stories and os.getenv("RETRY_ON_FAIL", "1") != "0":
                from . import voice_lint
                findings = voice_lint.lint(
                    stories, issue["spread_plan"], issue_slug=issue["slug"]
                )
                fails = [f for f in findings if f[0] == "FAIL"]
                if fails:
                    print(f"[ai_engine] retry-on-FAIL: first draft tripped "
                          f"{len(fails)} FAIL(s); retrying with corrections")
                    retry = _curate_with_claude(
                        raw_data, date, issue, corrections=fails
                    )
                    if retry:
                        # Lint the retry so we can report whether it cleared.
                        retry_fails = [
                            f for f in voice_lint.lint(
                                retry, issue["spread_plan"],
                                issue_slug=issue["slug"],
                            ) if f[0] == "FAIL"
                        ]
                        print(f"[ai_engine] retry returned {len(retry)} "
                              f"stories, {len(retry_fails)} FAIL(s) remaining")
                        if len(retry_fails) <= len(fails):
                            stories = retry
                        else:
                            print(f"[ai_engine] retry made things worse "
                                  f"({len(fails)} → {len(retry_fails)} FAILs)"
                                  f" — keeping first-draft stories")
                    else:
                        print("[ai_engine] retry call returned None — "
                              "keeping first-draft stories")
                else:
                    print("[ai_engine] retry-on-FAIL: first draft clean, "
                          "no retry needed")

            if stories:
                return _validate_and_fill(stories, count=count)
        except Exception as e:
            import traceback
            print(f"[ai_engine] Claude backend failed: {e}")
            traceback.print_exc()
        print("[ai_engine] Claude backend failed — falling back to mock.")

    return _validate_and_fill(_curate_mock(raw_data, date, issue), count=count)


# ────────────────────────────────────────────────────────────
# Mock curator
#
# Issue-aware: respects the writer pool + spread plan + story count declared
# in issue_types.IssueConfig. Builds one story per pool writer, applies the
# spread plan, pads with fallback if count > pool size.
# ────────────────────────────────────────────────────────────
def _curate_mock(raw: dict, date: datetime, issue: IssueConfig) -> list[dict]:
    news = raw.get("news", {}) or {}
    weather = raw.get("weather", {}) or {}
    otd = raw.get("on_this_day", []) or []
    reddit = raw.get("reddit", []) or []

    date_label = date.strftime("%B %-d").replace(" 0", " ") if os.name != "nt" else date.strftime("%B %#d")

    plan = list(issue["spread_plan"])
    pool = list(issue["writer_pool"])

    # Map writer_key → builder fn. Each returns a story dict (spread_type will
    # be overwritten by the plan). Builders pull from raw data; missing data
    # degrades gracefully into evergreen copy.
    builders = {
        "sports": lambda: _mock_sports(news, date_label),
        "weather": lambda: _mock_weather(weather),
        "history": lambda: _mock_history(otd),
        "trending": lambda: _mock_trending(reddit),
        "real_estate": lambda: _mock_real_estate(news),
        "food": lambda: _mock_food(news),
        "arts": lambda: _mock_arts(news),
        "editorial": lambda: _mock_editorial(news),
        "lifestyle": lambda: _mock_lifestyle(reddit),
    }

    # If plan opens with Maggie's editor's note, slot 0 is ALWAYS the editor
    # (not a pool writer). Pool writers fill the remaining N-1 slots.
    has_editor = bool(plan) and plan[0] == "todays_edition"
    writer_slots = len(plan) - (1 if has_editor else 0)

    # Build pool stories aligned to the plan's writer slots (skipping slot 0
    # when the editor's note is there). Match writers to spread_types using
    # the same canonical pairings enforced by voice_lint (T1.4), so mock runs
    # stay clean and the rendered HTML exercises each spread with the right
    # writer.
    writer_plan_slots = plan[1:] if has_editor else plan[:]
    writer_plan_slots = writer_plan_slots[:writer_slots]

    # Preference map: spread_type → ordered list of writer_keys that fit.
    # First-match-wins among unclaimed writers (pool first, then full roster).
    spread_pref: dict[str, list[str]] = {
        "academic": ["history"],
        "retro_weather": ["weather"],
        "broadsheet": ["sports", "real_estate"],
        "big_stat": ["real_estate", "weather", "editorial"],
        "rose_stamp": ["trending", "lifestyle", "food"],
        "editorial": ["editorial", "arts"],
        "midnight": ["history", "editorial", "arts"],
        "terminal": ["editorial", "trending", "arts"],
        "broadside": ["history", "editorial", "real_estate"],
        "hero": ["sports", "editorial", "real_estate", "weather"],
    }

    # Pool is the preferred source; full roster is the fallback when a strict-
    # match writer (e.g. weather for retro_weather) isn't in today's pool. This
    # mirrors how Claude works in the real curator — pool is a hint, not a cap.
    #
    # T1.4 has both STRICT spreads (retro_weather → weather only, academic →
    # history only, broadsheet → sports/real_estate only) and SOFT spreads
    # (hero, big_stat, etc. — preference, not requirement). We must assign
    # STRICT slots FIRST — otherwise a SOFT slot like hero can steal a writer
    # (e.g. weather) that a STRICT slot downstream requires.
    strict_spreads = {"retro_weather", "academic", "broadsheet"}
    all_roster = list(builders.keys())
    remaining_pool = list(pool)
    remaining_roster = [w for w in all_roster if w not in pool]
    # Pre-size the output so we can fill it out of order (strict slots first).
    ordered_keys: list[str] = [""] * len(writer_plan_slots)
    # Two-pass assignment: strict slots first, then the rest in natural order.
    strict_slots = [(i, s) for i, s in enumerate(writer_plan_slots) if s in strict_spreads]
    soft_slots = [(i, s) for i, s in enumerate(writer_plan_slots) if s not in strict_spreads]
    for i, spread in strict_slots + soft_slots:
        prefs = spread_pref.get(spread, [])
        # Try pool first, matching preference order.
        pick = next((k for k in prefs if k in remaining_pool), None)
        src = "pool"
        if pick is None:
            # Pool exhausted for this spread — try the full roster's top prefs.
            pick = next((k for k in prefs if k in remaining_roster), None)
            src = "roster"
        if pick is None:
            # No preference match anywhere — fall back to any pool writer, then
            # any roster writer.
            if remaining_pool:
                pick = remaining_pool[0]; src = "pool"
            elif remaining_roster:
                pick = remaining_roster[0]; src = "roster"
        if pick is not None:
            (remaining_pool if src == "pool" else remaining_roster).remove(pick)
            ordered_keys[i] = pick
        # else: leave "" — placeholder picked up downstream

    pool_stories: list[dict] = []
    for i, key in enumerate(ordered_keys):
        if key and key in builders:
            pool_stories.append(builders[key]())
        else:
            pool_stories.append(_mock_placeholder(i + 1, pool))
    pool_stories = pool_stories[:writer_slots]

    # Compose final stories: editor's note first (if applicable), then pool.
    # _mock_editor references the pool stories by first name, so it must be
    # built AFTER them.
    stories: list[dict] = []
    if has_editor:
        stories.append(_mock_editor(pool_stories, date, issue))
    stories.extend(pool_stories)

    # Apply spread plan — story at index i gets plan[i].
    for i, s in enumerate(stories):
        if i < len(plan):
            s["spread_type"] = plan[i]
        s["number"] = i + 1

    return stories


# ---- Per-writer mock story builders ------------------------------------------

def _mock_sports(news: dict, date_label: str) -> dict:
    """Kelsey Rowe — The Bench. Fully-voiced demo piece."""
    sports_src = _first_source(news.get("sports"), default="Google News · BSU Athletics")
    return {
        "writer_key": "sports",
        "spread_type": "broadsheet",
        "topic_label": "THE BENCH",
        "context_line": f"BSU Football · Spring Camp · {date_label}",
        "headline": "The walk-on at nickel is the story the wire missed",
        "deck": (
            "Spring camp, Day 12. From The Blue's sideline, what ESPN's "
            "roundup won't tell you about a roster the staff is rebuilding "
            "from the bottom up."
        ),
        "body": (
            "**The Lede:** I watched Cole Aguiar take seven nickel reps before the "
            "sprinklers shut off. The wire will tell you about seven other guys.\n\n"
            "I got to The Blue at 6:40 this morning, two coffees in, Subaru parked "
            "at the east lot where the gate guy pretends he doesn't recognize me. "
            "Aguiar was already in pads. By the time the sun cleared Table Rock he "
            "had rotated through three different looks at the nickel, and the staff "
            "was pencil-noting something on the laminated two-deep the beat guys "
            "aren't allowed to photograph. ESPN's spring-camp roundup will lead with "
            "the quarterback battle (it always leads with the quarterback battle) "
            "and the usual portal names — fine, that's what drives clicks in 400 "
            "markets. This column lives in the other 400.\n\n"
            "Aguiar is a junior, walk-on, Eagle High, never recruited. Last spring "
            "he got thirty-seven snaps of practice tape that none of the national "
            "sites bothered to pull. This spring the staff has him running with the "
            "ones in long-yardage — that's the play Broncos Nation has been nervous "
            "about since the Famous Idaho Potato Bowl. Ran it by Tam at the Ram on "
            "Broad Street, because she watches more BSU film than most beat writers. "
            "\"He's the one who runs to the ball,\" she said, without looking up "
            "from the spread on the chalkboard. Numbers don't argue.\n\n"
            "I was a walk-on point guard at BSU before my ACL got me. Eleven "
            "minutes in a MW quarterfinal — the only eleven that ever mattered — "
            "and I think about those minutes every time I watch a practice-squad "
            "kid get a rep that counts. Aguiar's combine numbers are ordinary. "
            "His film is not. Roster health in the MW gets measured from the "
            "bottom up; that's been true since before my knee did. The name to "
            "write down is Aguiar. Somebody will beat me to it by the spring "
            "game. Good."
        ),
        "pull_quote": "He's the one who runs to the ball.",
        "stat": "37",
        "stat_label": "Practice snaps on tape last spring. The national sites pulled zero.",
        "source": sports_src,
        "recurring_bit_content": (
            "THE LEDE — I watched Cole Aguiar take seven nickel reps before the "
            "sprinklers shut off. The wire will tell you about seven other guys."
        ),
    }


def _mock_weather(weather: dict) -> dict:
    today_period = (weather.get("periods") or [{}])[0]
    temp = today_period.get("temperature", "—")
    unit = today_period.get("temperatureUnit", "F")
    short = today_period.get("shortForecast", "Mixed")
    wind = today_period.get("windSpeed", "")
    mood_word = _mood_for_forecast(short)
    return {
        "writer_key": "weather",
        "spread_type": "retro_weather",
        "topic_label": "THE FORECAST",
        "headline": f"{mood_word.capitalize()} over the Boise Bench",
        "deck": f"Pete's read on today — {short.lower()}.",
        "body": (
            f"**MOOD OF THE SKY:** {mood_word.upper()}.\n\n"
            f"We are sitting on a {temp}°{unit} day with {short.lower()} and wind "
            f"{wind or 'light out of the south'}. The inversion line is where it "
            "always is this month — look up from Capitol Boulevard and you can see it, "
            "a gray fingernail sitting on top of a warmer city.\n\n"
            "If you're walking the dog: a real jacket. If you're just going to the car: "
            "cotton's fine, but bring something for the afternoon drop. The dog, for "
            "the record, does not read weather columns; she just wants to go."
        ),
        "pull_quote": f"A {temp}°{unit} day with opinions.",
        "stat": f"{temp}°{unit}",
        "source": "NWS Boise",
        "recurring_bit_content": f"MOOD OF THE SKY: {mood_word.upper()}",
    }


def _mock_history(otd: list) -> dict:
    """Wade Ostermann — Drive-By History. Chatty-neighbor voice.

    Ignores the raw OTD wire on purpose for the demo piece — Wade doesn't
    write from trivia cards; he writes from stories he heard. The hand-
    crafted story below is the reference piece. Real Claude will use the
    OTD feed as a *prompt* but will frame every piece around a landmark
    the reader can drive by today.
    """
    return {
        "writer_key": "history",
        "spread_type": "academic",
        "topic_label": "DRIVE-BY HISTORY",
        "context_line": "One story. One landmark. One thing you tell at dinner.",
        "headline": "You know that brick building on Grove Street?",
        "deck": (
            "Wade Ostermann on the Cyrus Jacobs-Uberuaga House — what it is, "
            "why it matters, and the part Helmut made me correct before I "
            "printed it."
        ),
        "body": (
            "You know that brick building on Grove Street, across from the "
            "parking structure? The one with the bright yellow door?\n\n"
            "That's the Cyrus Jacobs-Uberuaga House. Oldest brick building "
            "still standing in Boise — 1864, give or take. Cyrus Jacobs "
            "built it as a family home. But that's not the interesting part. "
            "The interesting part is what happened starting about 1910, when "
            "the Uberuaga family ran it as a boarding house for Basque "
            "sheepherders coming in off the range. Basque — those are the "
            "folks from the mountains between Spain and France. Most of them "
            "didn't speak English when they showed up in Idaho. They'd come "
            "through the door on Grove Street, get a bed, get a plate, get "
            "a map of the sheep camps, and head out.\n\n"
            "Helmut across the street — 84, retired Simplot, lived in Hyde "
            "Park since 1968 — corrected me on this. I had it as 1915. He "
            "said 1910. I checked with Arlene at the Historical Society. "
            "Arlene said Helmut was right, the first Uberuaga boarders "
            "were in by 1910.\n\n"
            "Here's the thing most people don't know. When the place opened "
            "as a museum in the '90s, they kept the original boarding-house "
            "kitchen. Same pots. Same wood stove. It's like walking into a "
            "1912 Tuesday afternoon — there's a pot on the stove that looks "
            "like somebody stepped out for a smoke.\n\n"
            "**The kicker:** the building's address today is 607 Grove "
            "Street. Drive by it. It's still there. The yellow door is the "
            "original Basque color — it's how the sheepherders who couldn't "
            "read the sign knew they'd found the right house.\n\n"
            "That's the one you tell at dinner."
        ),
        "pull_quote": "The yellow door is the original Basque color.",
        "stat": "1864",
        "stat_label": "Built. Oldest brick building in Boise still standing.",
        "source": "North End mail route · Helmut across the street · ISHS reference desk",
        "recurring_bit_content": (
            "DRIVE-BY — 607 Grove Street. Yellow door. The yellow is the "
            "part nobody tells you."
        ),
    }


def _mock_trending(reddit: list) -> dict:
    top = (reddit or [{}])[0]
    rtitle = top.get("title", "") or "What r/Boise is arguing about today"
    rscore = top.get("score", 0)
    return {
        "writer_key": "trending",
        "spread_type": "rose_stamp",
        "topic_label": "FRESH OFF THE PRESS",
        "headline": _truncate(rtitle, 10),
        "deck": "Jess Park on what Boise is talking about this morning.",
        "body": (
            f"**FRESH OFF THE PRESS** — Boise is doing that thing again where "
            "a post about parking becomes a 300-comment argument about zoning. "
            "The original gripe was about a construction cone on State Street. "
            "By page three it was a referendum on the city's entire growth plan.\n\n"
            "The posts that hit aren't the ones with the hottest takes — they're "
            "the ones that catalog something mundane: a sign that changed, a "
            "business that closed, a lane that got a curb. Boiseans are "
            "cartographers of small civic changes.\n\n"
            "This week's Treasure Valley timelapse made the rounds. "
            "Everybody's nostalgic for something that was there six months ago."
        ),
        "pull_quote": "Every Boise conversation eventually becomes the same conversation.",
        "stat": f"{rscore}",
        "source": "The Boise Pulse",
        "recurring_bit_content": (
            "• Boiseans are relitigating parking-vs-zoning (again, still)\n"
            "• Treasure Valley timelapse hit the front page — everyone's nostalgic\n"
            "• NextDoor: roundabouts (it is always roundabouts)"
        ),
    }


def _mock_real_estate(news: dict) -> dict:
    src = _first_source(news.get("real_estate"), default="Idaho Business Review")
    return {
        "writer_key": "real_estate",
        "spread_type": "big_stat",
        "topic_label": "THE MARKET",
        "headline": "Median price held. The story is what's behind it.",
        "deck": "Sal Merritt on a number that's stopped telling you what you want to know.",
        "body": (
            "The headline median is $519,000 — down a hair from March, up 2.1% "
            "year-over-year. That's the number the papers will quote. It's also "
            "a number that's mathematically interesting and economically inert: "
            "a median moves when the MIX changes, not when prices change.\n\n"
            "Inventory in the North End dropped 11%. Inventory in Meridian rose "
            "7%. You mix those two buckets together and the median barely budges, "
            "because the North End pulls the top end up while Meridian drags it "
            "down. Same median, different market.\n\n"
            "**THE COMPS:** 2019: $305k · 2022: $549k · 2023: $489k · 2024: "
            "$505k · 2025: $519k. The five-year chart looks like a hill with a "
            "plateau on top. That's not a cool market. That's a market that's "
            "finished correcting and is waiting for rates.\n\n"
            "Watch days-on-market next. If DOM climbs through 45 we're in a "
            "different conversation."
        ),
        "pull_quote": "Same median, different market.",
        "stat": "$519K",
        "stat_label": "Treasure Valley median, single-family. Down 0.2% M/M, up 2.1% Y/Y.",
        "source": src,
        "recurring_bit_content": "THE COMPS · 2019 → 2025 — the chart is the argument.",
    }


def _mock_food(news: dict) -> dict:
    src = _first_source(news.get("food"), default="Boise Weekly")
    return {
        "writer_key": "food",
        "spread_type": "rose_stamp",
        "topic_label": "THE TABLE",
        "headline": "A quiet week. Go to the one you've been meaning to.",
        "deck": "Nina Castillo on the Thursday move when nothing's new.",
        "body": (
            "Slow news week in food. No closures, no openings, no James Beard "
            "drama. That's a gift, not a problem — it means this is the week "
            "you go to the place you've been circling.\n\n"
            "Mine this week: Kibrom's on State. The tibs with a side of injera "
            "and whatever berbere she's got going. You sit near the door, you "
            "get the draft, you don't look at your phone. Forty-five minutes, "
            "one plate, one beer, you leave full.\n\n"
            "— *Nina's Table: the best new restaurant in Boise this week is one "
            "that's been open since 2012.*"
        ),
        "pull_quote": "The best new restaurant is one that's been open since 2012.",
        "stat": "$18",
        "source": src,
        "recurring_bit_content": "— Nina's Table: the best plate in Boise this week.",
    }


def _mock_arts(news: dict) -> dict:
    src = _first_source(news.get("arts"), default="Idaho Press")
    return {
        "writer_key": "arts",
        "spread_type": "midnight",
        "topic_label": "THE SCENE",
        "headline": "Three shows, one basement, one surprise",
        "deck": "Dex Dexter on the week Boise remembered it has a music scene.",
        "body": (
            "> *\"If you ain't payin' rent on a stage you ain't sayin' nothin'.\"*\n\n"
            "Dex's Drop: Shrine Social Club Friday, Neurolux Saturday, a basement "
            "in the East End Sunday that I'm not going to name because the point "
            "of a basement show is that you had to know a guy.\n\n"
            "The surprise: the touring openers are better than the headliners at "
            "two of the three. That's a telling week for the scene — national acts "
            "are working Boise harder than they were three years ago, and the "
            "locals on the opener slot are getting the ten minutes that matter."
        ),
        "pull_quote": "The point of a basement show is that you had to know a guy.",
        "stat": "3",
        "source": src,
        "recurring_bit_content": "Dex's Drop — what the jukebox heard this week.",
    }


def _mock_editorial(news: dict) -> dict:
    src = _first_source(news.get("general"), default="Multiple outlets")
    return {
        "writer_key": "editorial",
        "spread_type": "editorial",
        "topic_label": "THE WAY I SEE IT",
        "headline": "We keep measuring the wrong thing",
        "deck": "Dani Breck on the number that doesn't mean what you think it means.",
        "body": (
            "Every week somebody cites 'population growth' as if it were a "
            "verdict on Boise's policies. It isn't. Population growth is an "
            "input. The verdict is whether the people who were already here "
            "can still afford to be.\n\n"
            "Three numbers to watch instead: the share of renters paying more "
            "than 30% of income on housing (the Census tracks this). The median "
            "household-income-to-home-price ratio. The net domestic migration "
            "for residents earning under $50k. Those three together tell you if "
            "growth is building a city or replacing one.\n\n"
            "I'm not against growth. I'm against the shorthand. The shorthand "
            "is how we end up with a city council that celebrates a number that "
            "was already the wrong number to celebrate."
        ),
        "pull_quote": "Population growth is an input, not a verdict.",
        "stat": "30%",
        "source": src,
        "recurring_bit_content": "THE WAY I SEE IT — measure the thing, not the shorthand.",
    }


def _mock_editor(pool_stories: list[dict], date: datetime, issue: IssueConfig) -> dict:
    """Maggie Halstead — Today's Edition. Three paragraphs: what today is,
    read X first (by writer first name), the line to carry into the day.
    Signed '— M.H.' by the renderer.
    """
    # Lift first names from pool stories so Maggie can reference them.
    first_names: list[str] = []
    for s in pool_stories[:3]:
        wk = s.get("writer_key", "")
        persona = PERSONAS.get(wk, {})
        nm = persona.get("name", "")
        first = nm.split()[0] if nm else ""
        if first and first not in first_names:
            first_names.append(first)

    lead = first_names[0] if first_names else "the lead piece"
    second = first_names[1] if len(first_names) > 1 else None

    day = date.strftime("%A")
    slug_label = issue.get("slug", "").replace("_", " ").upper()
    dateline = f"{date.strftime('%A · %B %d, %Y').upper()} · {slug_label}"

    body = (
        f"A {day.lower()} edition that started with a question none of our writers "
        f"set out to answer: what do we actually measure when we try to measure "
        f"Boise? Every piece in the stack ended up there anyway. The writers "
        f"don't coordinate. They notice the same thing a different way.\n\n"
        f"**Read {lead} first.** It's the piece that sets the frame — the "
        f"anchor every other story is quietly playing off of"
        + (f", and {second}'s piece is where the second story is hiding."
           if second else ".")
        + "\n\n"
        f"The line to carry into the {day.lower()}: *the order is the argument.*"
    )

    return {
        "writer_key": "editor_in_chief",
        "spread_type": "todays_edition",
        "topic_label": "TODAY'S EDITION",
        "context_line": dateline,
        "headline": "",
        "deck": "",
        "body": body,
        "pull_quote": "The order is the argument.",
        "stat": "",
        "source": "The Boise Pulse · Editorial",
        "recurring_bit_content": "— M.H., Editor",
    }


def _mock_lifestyle(reddit: list) -> dict:
    """Hayley Watts — Saturday Tried It. TikTok trend filtered through
    a Meridian split-level. Short, punchy, ends with HAYLEY'S RATIO.
    """
    return {
        "writer_key": "lifestyle",
        "spread_type": "rose_stamp",
        "topic_label": "SATURDAY TRIED IT",
        "context_line": "TikTok trend · Meridian test · one verdict",
        "headline": "The peel-and-stick tile backsplash: TRIED IT.",
        "deck": (
            "@hannahdoesdiy in Nashville pushed it out in February. Here's "
            "what happens when a Meridian split-level kitchen tries it on "
            "a Saturday with a 4-year-old supervising."
        ),
        "body": (
            "The peel-and-stick subway tile video keeps showing up in my "
            "feed. @hannahdoesdiy from Nashville, posted February 9, 2.1M "
            "views. She did it in 40 minutes. Hers looked incredible. So "
            "I tried it Saturday.\n\n"
            "Bought the tile at the Meridian Target — $28 for a pack of "
            "four sheets, enough for about a 4-foot run above the coffee "
            "bar. Emmy was supposed to be napping. Emmy was not napping. "
            "Emmy was in the pantry with the goldfish.\n\n"
            "Two things the video doesn't tell you. One: the adhesive "
            "does not love a textured wall, and every Meridian split-"
            "level from 1998 has textured walls. I had to skim-coat a "
            "thin layer first, which added 30 minutes and a run to Lowe's. "
            "Two: you have to cut with a metal ruler and a real box "
            "cutter. The safety blade they sell you at Target will give "
            "up at tile number three.\n\n"
            "Owen watched the whole thing and said it looked stupid. "
            "Then I finished it. Then he said it looked fine. Kyle came "
            "home, clocked the Target bag and the Lowe's bag, asked how "
            "much. Total came in at $41. Would do again, would tell a "
            "friend, would NOT do it with a texture-walled house "
            "without the skim-coat step.\n\n"
            "**HAYLEY'S RATIO:** $41 · 120 minutes · 2/2 kids intact. "
            "Would do again."
        ),
        "pull_quote": "Emmy was supposed to be napping. Emmy was not napping.",
        "stat": "$41 / 120 / 2",
        "stat_label": "Dollars · minutes · kids-out-of-2. Would do again.",
        "source": "@hannahdoesdiy (Nashville, Feb 9) · Meridian Target · Linder Lowe's",
        "recurring_bit_content": (
            "HAYLEY'S RATIO — $41 · 120 min · 2/2 kids intact · would do again"
        ),
    }


def _mock_placeholder(slot: int, pool: list[str]) -> dict:
    """Mock-only placeholder for pool-repeat slots.

    When the issue's story_count exceeds its writer_pool size, the mock fills
    extra slots with this clearly-marked 'coming soon' card rather than
    duplicating a pool writer's piece. Real-AI output always has `count`
    distinct stories, so this is never emitted in production.
    """
    pool_label = ", ".join(pool)
    return {
        "writer_key": "editorial",
        "spread_type": "editorial",
        "topic_label": "COMING ONLINE",
        "headline": "This slot opens when the live curator runs",
        "deck": (
            "The mock generator fills the writer pool (4 writers) but the "
            "issue wants more stories than the pool. Real Claude fills "
            "every slot with a distinct piece."
        ),
        "body": (
            "**Tomorrow:** the ANTHROPIC_API_KEY flip turns this issue over to "
            "the real curator. Claude reads today's Boise wire, picks the "
            "stories that earn this cadence, and writes each in its assigned "
            f"voice (today's pool: {pool_label}).\n\n"
            "Until then, this placeholder reserves the slot so the page layout "
            "is honest about the shape: here's where a sixth voice lands on "
            "Tuesday, and here's the spread it'll claim when it does."
        ),
        "pull_quote": "Placeholder — live curator claims this slot tomorrow.",
        "stat": "",
        "source": "Mock curator",
        "recurring_bit_content": "",
    }


def _mood_for_forecast(short: str) -> str:
    s = (short or "").lower()
    if "snow" in s:
        return "brooding"
    if "rain" in s or "shower" in s:
        return "unsettled"
    if "sunny" in s or "clear" in s:
        return "bright"
    if "cloud" in s:
        return "moody"
    if "wind" in s:
        return "restless"
    return "mixed"


def _first_headline(items, default: str) -> str:
    if not items:
        return default
    for it in items:
        t = (it or {}).get("title", "").strip()
        if t:
            return t
    return default


def _first_source(items, default: str) -> str:
    if not items:
        return default
    for it in items:
        s = (it or {}).get("source", "").strip()
        if s:
            return s
    return default


def _truncate(text: str, max_words: int) -> str:
    words = re.split(r"\s+", (text or "").strip())
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(",.;:") + "…"


# ────────────────────────────────────────────────────────────
# Validation
# ────────────────────────────────────────────────────────────
REQUIRED_FIELDS = {
    "number", "writer_key", "spread_type", "topic_label",
    "headline", "deck", "body", "pull_quote", "stat", "source",
}


def _validate_and_fill(stories: list[dict], count: int = 10) -> list[dict]:
    """Ensure each story has every required field; fix numbering; cap at `count`."""
    out = []
    for i, s in enumerate(stories[:count], start=1):
        filled = dict(s)
        filled.setdefault("writer_key", "editorial")
        writer_key = filled["writer_key"]
        persona = PERSONAS.get(writer_key, PERSONAS["editorial"])

        filled["number"] = i
        filled.setdefault("spread_type", persona["spread_default"])
        filled.setdefault("topic_label", persona["section"].upper())
        filled.setdefault("headline", "Untitled")
        filled.setdefault("deck", "")
        filled.setdefault("body", "")
        filled.setdefault("pull_quote", "")
        filled.setdefault("stat", "")
        filled.setdefault("source", "")
        filled.setdefault("recurring_bit_content", persona.get("recurring_bit", ""))

        out.append(filled)

    # Pad with blank placeholders if somehow < count
    while len(out) < count:
        out.append(
            {
                "number": len(out) + 1,
                "writer_key": "editorial",
                "spread_type": "hero",
                "topic_label": "THE WAY I SEE IT",
                "headline": "Placeholder",
                "deck": "",
                "body": "",
                "pull_quote": "",
                "stat": "",
                "source": "",
                "recurring_bit_content": "",
            }
        )
    return out


# ────────────────────────────────────────────────────────────
# Real backends (stubs — activate via USE_REAL_AI=1 once keys are set)
# ────────────────────────────────────────────────────────────
def _format_locked_assignments(assignments: dict[str, dict]) -> str:
    """Format Gemini research dossiers into a locked brief for Claude.

    Replaces selection_rules when Gemini has pre-researched story angles.
    Claude receives a full fact dossier — writing is the only job left.
    The ZERO HALLUCINATION rule binds Claude to only what is in the dossier.
    """
    writer_labels = {
        "sports":      "Kelsey Rowe (The Bench)",
        "weather":     "Pete Caldwell (The Forecast)",
        "trending":    "Jess Park (Fresh Off the Press)",
        "real_estate": "Sal Merritt (The Market)",
        "history":     "Wade Ostermann (Drive-By History)",
        "food":        "Nina Castillo (The Table)",
        "arts":        "Dex Dexter (The Scene)",
        "editorial":   "Dani Breck (The Way I See It)",
        "lifestyle":   "Hayley Watts (Saturday Tried It)",
        "editor_in_chief": "Maggie Halstead (Today's Edition)",
    }

    lines = [
        "STORY ASSIGNMENTS — LOCKED BY EDITORIAL DIRECTOR (Gemini Research):",
        "Do NOT change these angles. Do NOT pick a different story.",
        "Your entire job is craft: write each in full writer voice, nail the",
        "recurring bits, hit the word-count targets, open inside the story.",
        "",
        "╔══════════════════════════════════════════════════════════════════╗",
        "║  ZERO HALLUCINATION RULE — THIS IS NON-NEGOTIABLE               ║",
        "║                                                                  ║",
        "║  Every fact, name, number, and quote you write MUST appear       ║",
        "║  in the research dossier below. If a specific detail is NOT      ║",
        "║  in the dossier, do NOT invent it.                               ║",
        "║                                                                  ║",
        "║  • NAMED PEOPLE: only use names listed in 'named_people'.        ║",
        "║    If no name is given for a role, write 'a Boise official'      ║",
        "║    or 'a team spokesperson' — never fabricate a name.            ║",
        "║                                                                  ║",
        "║  • NUMBERS & STATS: only use values in 'key_numbers' or          ║",
        "║    'key_facts'. Never round up, invent a stat, or add a          ║",
        "║    percentage not present in the dossier.                        ║",
        "║                                                                  ║",
        "║  • QUOTES: only reproduce quotes from 'direct_quotes'.           ║",
        "║    If no quote is provided, do NOT invent dialogue or            ║",
        "║    attribute words to any named person.                          ║",
        "║                                                                  ║",
        "║  • CONFIDENCE: if fact_confidence is LOW or MEDIUM, hedge        ║",
        "║    claims in prose ('reportedly', 'according to sources').       ║",
        "║    HIGH confidence = state as fact.                              ║",
        "║                                                                  ║",
        "║  • EVERYTHING ELSE (voice, structure, transitions, recurring     ║",
        "║    bits, scene-setting) is yours to craft — use writer_fuel      ║",
        "║    for texture and color.                                        ║",
        "╚══════════════════════════════════════════════════════════════════╝",
        "",
    ]

    for writer_key, assignment in assignments.items():
        label = writer_labels.get(writer_key, writer_key)
        lines.append(f"━━━ [{label}] ━━━")

        # Core assignment fields (always present)
        for field, label_str in [
            ("angle",  "Angle"),
            ("hook",   "Hook"),
            ("source", "Source"),
            ("why_local", "Why local"),
        ]:
            val = assignment.get(field, "")
            if val:
                lines.append(f"  {label_str}: {val}")

        # Rich research fields (present in upgraded dossiers)
        key_facts = assignment.get("key_facts", [])
        if key_facts:
            lines.append("  Key facts (USE ONLY THESE — do not add facts not listed):")
            for f in key_facts:
                lines.append(f"    • {f}")

        named_people = assignment.get("named_people", [])
        if named_people:
            lines.append("  Named people (ONLY these names may appear in your prose):")
            for p in named_people:
                lines.append(f"    • {p}")

        key_numbers = assignment.get("key_numbers", [])
        if key_numbers:
            lines.append("  Key numbers (ONLY these values may appear in your prose):")
            for n in key_numbers:
                lines.append(f"    • {n}")

        direct_quotes = assignment.get("direct_quotes", [])
        if direct_quotes:
            lines.append("  Direct quotes (reproduce exactly or paraphrase — never invent new ones):")
            for q in direct_quotes:
                lines.append(f"    • {q}")
        else:
            lines.append("  Direct quotes: NONE PROVIDED — do not invent any quoted speech.")

        community_reaction = assignment.get("community_reaction", "")
        if community_reaction:
            lines.append(f"  Community reaction: {community_reaction}")

        writer_fuel = assignment.get("writer_fuel", "")
        if writer_fuel:
            lines.append(f"  Writer fuel (texture/color to draw on): {writer_fuel}")

        sources_checked = assignment.get("sources_checked", [])
        if sources_checked:
            lines.append(f"  Sources checked: {', '.join(sources_checked)}")

        confidence = assignment.get("fact_confidence", "")
        if confidence:
            lines.append(f"  Fact confidence: {confidence}")

        lines.append("")

    lines += [
        "VOICE CRAFT REMINDERS (apply to every sentence):",
        "  Kelsey: short-declarative-then-longer rhythm; proper-noun hammer",
        "    (The Blue / the MW / Broncos Nation); walk-on thesis runs quietly",
        "    underneath; Tam at the Ram appears ~1-in-3, never twice in one piece.",
        "  Pete: chatty, gas-station register voice; dog or neighbor as weather",
        "    test; MOOD OF THE SKY is always one capitalized word, always first.",
        "  Wade: open with 'You know that [thing] on [street]?'; cite Arlene OR",
        "    Helmut, never both; one date, one then, one now; close with",
        "    'That's the one you tell at dinner.'",
        "  Jess: FRESH OFF THE PRESS is the literal first line of recurring_bit;",
        "    three bullets = Jess's OWN editorial takes on what Boise is talking",
        "    about (NOT raw Reddit titles or handles — describe the TOPIC in her",
        "    voice); reaction prose only in body — never paste bullets into body.",
        "  Sal: one concrete number per para; end with THE COMPS 5-year line.",
        "  Nina: close with '— Nina\u2019s Table: [one-line verdict].'",
        "  Dex: open body with Dex\u2019s Drop (a blockquote, often a lyric).",
        "  Dani: three named sources; plainspoken; not angry.",
        "  Hayley: binary verdict (TRIED IT / CALLING IT); HAYLEY\u2019S RATIO in",
        "    recurring_bit ($ / minutes / kids-out-of-2); no banned words",
        "    (babe / you guys / obsessed / iykyk).",
    ]
    return "\n".join(lines)


def _compress_news(news: dict) -> str:
    """Flatten the multi-bucket news dict into a readable bullet list."""
    if not news:
        return "(no news fetched)"
    lines = []
    for topic, items in news.items():
        if not items:
            continue
        lines.append(f"[{topic.upper()}]")
        for item in items[:4]:
            title = item.get("title", "").strip()
            source = item.get("source", "").strip()
            if title:
                lines.append(f"  • {title}" + (f" ({source})" if source else ""))
    return "\n".join(lines) if lines else "(no news fetched)"


def _compress_weather(weather: dict) -> str:
    """Format NWS forecast periods into a compact text block."""
    periods = (weather or {}).get("periods", [])
    if not periods:
        return "(no NWS forecast available)"
    lines = []
    for p in periods[:6]:
        name = p.get("name", "")
        temp = p.get("temperature", "?")
        unit = p.get("temperatureUnit", "F")
        short = p.get("shortForecast", "")
        detail = p.get("detailedForecast", "")
        wind_speed = p.get("windSpeed", "")
        wind_dir = p.get("windDirection", "")
        wind = f"{wind_dir} {wind_speed}".strip()
        lines.append(f"{name}: {temp}°{unit}, {short}" +
                     (f", wind {wind}" if wind else "") +
                     (f" — {detail[:120]}" if detail else ""))
    return "\n".join(lines)


def _compress_otd(otd: list) -> str:
    """Format Wikipedia On-This-Day items into a bullet list."""
    if not otd:
        return "(no On-This-Day data)"
    lines = []
    for item in otd[:5]:
        if isinstance(item, dict):
            year = item.get("year", "")
            text = item.get("text", "") or item.get("description", "")
            lines.append(f"  • {year}: {text[:120]}" if year else f"  • {text[:120]}")
        elif isinstance(item, str):
            lines.append(f"  • {item[:120]}")
    return "\n".join(lines) if lines else "(no On-This-Day data)"


def _compress_reddit(reddit: list) -> str:
    """Format r/Boise posts into a readable bullet list."""
    if not reddit:
        return "(no Reddit data)"
    lines = []
    for post in reddit[:8]:
        if isinstance(post, dict):
            title = post.get("title", "").strip()
            score = post.get("score", "")
            comments = post.get("num_comments", "")
            if title:
                meta = f" [{score} pts, {comments} comments]" if score else ""
                lines.append(f"  • {title}{meta}")
        elif isinstance(post, str):
            lines.append(f"  • {post[:120]}")
    return "\n".join(lines) if lines else "(no Reddit data)"


def _compress_youtube(youtube: list) -> str:
    """Format YouTube items into a readable bullet list."""
    if not youtube:
        return "(no YouTube data)"
    lines = []
    for item in youtube[:5]:
        if isinstance(item, dict):
            title = item.get("title", "").strip()
            channel = item.get("channel", "").strip()
            if title:
                lines.append(f"  • {title}" + (f" — {channel}" if channel else ""))
        elif isinstance(item, str):
            lines.append(f"  • {item[:120]}")
    return "\n".join(lines) if lines else "(no YouTube data)"


def _build_curation_prompt(raw: dict, date: datetime, issue: IssueConfig) -> str:
    """Compose the Phase-1 curation prompt. Small, focused, ~5-7k chars."""
    date_str = date.strftime("%A, %B %d, %Y")
    news_summary = _compress_news(raw.get("news", {}))
    reddit_summary = _compress_reddit(raw.get("reddit", []))
    youtube_summary = _compress_youtube(raw.get("youtube", []))
    weather_summary = _compress_weather(raw.get("weather", {}))
    otd_summary = _compress_otd(raw.get("on_this_day", []))
    story_assignments = raw.get("story_assignments", {})

    voices = all_prompt_voices()

    schema_example = json.dumps(
        [
            {
                "number": 1,
                "writer_key": "sports",
                "spread_type": "broadsheet",
                "topic_label": "THE BENCH",
                "headline": "10 words max",
                "deck": "One-sentence subtitle.",
                "body": "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3.",
                "pull_quote": "A memorable sentence.",
                "stat": "optional",
                "source": "Outlet name",
                "recurring_bit_content": "THE LEDE — one surgical sentence",
            }
        ],
        indent=2,
    )

    # Per-writer selection rules for the curator. These decide WHICH stories land
    # in each writer's slot. Writers without a bespoke rule use the default: match
    # beat + writer's voice.
    kelsey = PERSONAS["sports"]
    selection_rules = (
        "STORY SELECTION RULES (apply per writer slot):\n"
        "\n"
        f"- sports (Kelsey Rowe, 'The Bench'): audience is {kelsey['audience']} "
        f"A Kelsey story exists only when the Google News wire version is "
        "generic and there's a Boise-specific angle the wire missed — depth-chart "
        "implications, recruit detail, walk-on reps, MW scheduling quirks, "
        "coaching-room context. Do NOT rewrite the wire. If no local angle can "
        "be added, put a non-sports story in slot #1 and skip Kelsey today. "
        f"Beat scope: {', '.join(kelsey['beat_scope'])}. Thesis she returns to "
        "quietly: 'respect the walk-on' — roster health is measured from the "
        "bottom up. Use supporting character 'Tam at the Ram' (bartender, The "
        "Ram on Broad Street, watches every Saturday since 2009) roughly 1 in "
        "3 columns, never twice in one piece. Use the proper-noun hammer: 'The "
        "Blue' not 'the stadium', 'the MW' not 'the conference', name the "
        "fanbase (Broncos Nation, the Albertsons crowd) specifically.\n"
        "- weather (Pete Caldwell, 'The Forecast'): MANDATORY slot #2 every "
        "day. Build entirely from the NWS forecast above. Open with 'MOOD OF "
        "THE SKY: [one word]'.\n"
        "- history (Wade Ostermann, 'Drive-By History'): audience is transplants "
        "who want a story they can tell at dinner. Open with 'You know that "
        "[thing] on [street]?' and pick a specific physical object in Boise "
        "the reader could actually drive by — a building, a plaque, a park "
        "bench, a weird cornice, a door. No capital-H History lectures. "
        "Cite Arlene at the ISHS reference desk OR Helmut-across-the-street "
        "(not both in one piece). One concrete date; one thing it used to be; "
        "one thing it is now. Close with the exact line: 'That's the one you "
        "tell at dinner.'\n"
        "- lifestyle (Hayley Watts, 'Saturday Tried It'): appears at MOST once "
        "per week. Binary verdict — TRIED IT or CALLING IT. `recurring_bit_content` "
        "MUST contain the literal string \"HAYLEY'S RATIO\" (hard lint check) "
        "followed by: $ / minutes / kids-out-of-2 (how many of her two kids "
        "were present). Banned words: 'babe', 'you guys', 'obsessed', 'iykyk'. "
        "Kids are Owen (7) and Emmy (4). Husband Kyle. Split-level off Linder "
        "in Meridian.\n"
        "- editor_in_chief (Margaret 'Maggie' Halstead, 'Today's Edition'): "
        "see editor brief above — slot 1 only, never a writer-driven story.\n"
        "- trending (Jess Park, 'Fresh Off the Press'): built from Boise "
        "community signals — r/Boise, NextDoor, local YouTube. NEVER cite "
        "Reddit by URL or paste raw thread titles. Use these as editorial "
        "intel to identify the topic; Jess writes about the TOPIC in her "
        "own voice. `recurring_bit_content` MUST contain the literal string "
        "\"FRESH OFF THE PRESS\" as its first line — hard lint check. "
        "Then three bullet lines of Jess's own observations about what's "
        "circulating (not raw thread titles). Body is Jess's reaction prose only.\n"
        "- real_estate (Sal Merritt, 'The Market'): must have a concrete "
        "number. End with 'THE COMPS' 5-year comparison.\n"
        "- food (Nina Castillo, 'The Table'): close with '— Nina's Table: [one-"
        "line verdict]'.\n"
        "- arts (Dex Dexter, 'The Scene'): open with 'Dex's Drop' — a block-"
        "quote, often a hip-hop lyric.\n"
        "- editorial (Dani Breck, 'The Way I See It'): plainspoken, direct, "
        "not angry. Cite three sources by name when possible.\n"
    )

    format_discipline = (
        "FORMAT DISCIPLINE — enforce on every story:\n"
        "\n"
        "STAT FIELD CONTRACT — `stat` is a scannable number or short phrase, "
        "NOT a sentence. Typography renders it huge; it must fit in one line.\n"
        "  - big_stat spread: ≤15 chars. One number. Examples: \"$487K\", "
        "\"67 days\", \"39°F swing\", \"7.2 mi\". NEVER a sentence like \"82°F "
        "high → 43°F overnight: 39°F swing in under 12 hours\".\n"
        "  - broadsheet spread: ≤15 chars for the scoreboard cell. Examples: "
        "\"41 → 67 days\", \"3-1 (MW)\".\n"
        "  - retro_weather spread: ≤12 chars. Examples: \"82° / 43°\", "
        "\"HIGH 74°\". Context goes in the body.\n"
        "  - All other spreads: `stat` optional; if used, same ≤15-char rule. "
        "Prefer OMIT over a padded stat.\n"
        "\n"
        "RECURRING_BIT_CONTENT SCHEMA — the field SHAPE depends on spread:\n"
        "  - broadside (Wade): MUST be pipe-delimited \"<then>|<now>\". Each "
        "half ≤18 words. Example: \"1947 Boise Cascade mill gate, chain-link, "
        "shift whistle|2026 Whole Foods parking, chain-link still there, no "
        "whistle\". No pipe = the renderer hides the block.\n"
        "  - rose_stamp (Jess): `recurring_bit_content` MUST start with the "
        "literal text \"FRESH OFF THE PRESS\" (the lint check searches for "
        "this exact string, case-insensitive). Format: \"FRESH OFF THE PRESS\\n"
        "• [Jess's editorial take on signal 1]\\n• [signal 2]\\n• [signal 3]\". "
        "Bullets are Jess's own voice — NEVER raw thread titles or Reddit URLs. "
        "Body copy is Jess's REACTION prose; do NOT paste bullets into body.\n"
        "  - academic (Wade 'Drive-By History'): ONE finished sentence the "
        "reader sees rendered. NEVER paste the prompt instructions (\"open "
        "with...\", \"close with...\"). Example: \"You know that mural on 8th? "
        "It used to be the Falk's loading dock.\"\n"
        "  - retro_weather (Pete): MUST begin with \"MOOD OF THE SKY: "
        "<one word>\".\n"
        "  - big_stat (Sal): \"THE COMPS — <one short line>\" is fine; the "
        "5-year comp list goes in body.\n"
        "  - editorial (Dani/Dex): the writer's franchised recurring phrase.\n"
        "  - midnight/terminal: optional.\n"
        "\n"
        "WRITER ↔ SPREAD PAIRINGS (canonical — do not mix):\n"
        "  - academic → history (Wade)\n"
        "  - retro_weather → weather (Pete)\n"
        "  - todays_edition → editor_in_chief (Maggie)\n"
        "  - broadsheet → sports (Kelsey) OR real_estate (Sal). These are the "
        "only two writers paired with broadsheet.\n"
        "  - rose_stamp → trending (Jess) preferred. Only place a different "
        "writer on rose_stamp if the story IS itself a trending/reddit/"
        "youtube moment.\n"
        "  - big_stat → real_estate, weather, or editorial. Must have a real "
        "number.\n"
        "  - editorial → editorial (Dani) or arts (Dex).\n"
        "  - midnight, terminal, broadside → flexible; pick the writer whose "
        "voice fits.\n"
        "\n"
        "BODY-COPY DUPLICATION BAN:\n"
        "  - Never restate a list, box, or recurring-bit inside body copy. If "
        "the COMPS list is in `recurring_bit_content`, body talks ABOUT the "
        "market — it does NOT repeat the five comp lines.\n"
        "  - Same rule for Jess's three trending items and Wade's Then|Now "
        "pair. The reader sees them rendered.\n"
        "\n"
        "OPENER BAN — reject these throat-clearing patterns on sentence 1:\n"
        "  - \"In the world of X, ...\" / \"When it comes to X, ...\"\n"
        "  - \"Here's what <you need to know / caught my eye>...\"\n"
        "  - \"It's worth noting that ...\" / \"It's no secret that ...\"\n"
        "  - \"The strongest version of the argument is...\"\n"
        "  - \"Let's be clear,\" / \"Let's talk about ...\"\n"
        "  - \"Before we <get into it / jump in>...\"\n"
        "  - \"There's something to be said for ...\"\n"
        "  Every piece opens INSIDE the story — a specific moment, a specific "
        "object, a specific quote.\n"
        "\n"
        "ENDING BAN — no summary-restatement closers:\n"
        "  - No \"So, ...\" / \"In the end, ...\" / \"The bottom line is...\" "
        "/ \"At the end of the day...\" final sentences.\n"
        "  - Writers do NOT \"sign off\" or \"wrap up\" in body copy. The "
        "byline is the sign-off.\n"
        "  - Do NOT make the final sentence the same as the pull quote.\n"
        "  - A writer's franchised closer (Wade: \"That's the one you tell at "
        "dinner.\"; Nina's Table line; etc.) IS allowed — that's voice, not "
        "summary.\n"
        "\n"
        "SELF-REFERENCE BAN:\n"
        "  - Writers never refer to themselves by name inside their own body "
        "copy. No \"Kelsey notes...\", no \"What Sal's been tracking...\", "
        "no \"As Nina says...\". First person or no person.\n"
        "  - The byline renders the writer's name; the reader already knows.\n"
    )

    plan = issue["spread_plan"]
    total_slots = len(plan)
    has_editor = bool(plan) and plan[0] == "todays_edition"
    writer_slots = total_slots - (1 if has_editor else 0)
    pool = issue["writer_pool"]
    weather_rule = (
        "Pete Caldwell (weather) MUST appear (weekend forecasts drive reader plans)."
        if issue["weather_mandatory"]
        else "Weather is NOT mandatory today. Pete only appears if weather is genuinely newsworthy (red-flag warning, incoming storm, inversion crisis)."
    )

    editor_brief = (
        "Slot 1 is ALWAYS the editor's note ('Today's Edition') — written by "
        "Margaret 'Maggie' Halstead, Editor-in-Chief. It is NOT a writer-"
        "driven story. It frames the issue in 120-160 words across three "
        "paragraphs: (1) what today is — a theme, question, or moment; (2) "
        "'Read X first' naming one of the other writers by first name with "
        "a one-sentence reason; (3) one-sentence close — the line the "
        "reader carries into the day. Sign-off '— M.H.' is added by the "
        "renderer; do NOT include it in the body. writer_key MUST be "
        "'editor_in_chief'. spread_type MUST be 'todays_edition'.\n"
    ) if has_editor else ""

    # STRICT-writer exclusion: build a map of which writers are already claimed
    # by a locked spread. These writers MUST NOT appear on any other slot.
    # Same-writer 2x is a hard lint FAIL that blocks publish.
    strict_claimed: dict[str, str] = {}  # writer_key -> claiming spread name
    if "retro_weather" in plan:
        strict_claimed["weather"] = "retro_weather"
    if "academic" in plan:
        strict_claimed["history"] = "academic"

    _writer_names = {"weather": "Pete", "history": "Wade"}

    # Per-slot hard mapping — spread_type LOCKED by layout. Claude picks writer
    # and story only. Inline BANNED annotation on every soft slot prevents the
    # #1 duplication FAIL (weather 2x when retro_weather + hero both present).
    slot_line_list = []
    for i, s in enumerate(plan, start=1):
        line = f"  Slot {i}: spread_type MUST be \"{s}\""
        # Soft slots get an inline ban list so Claude cannot miss it
        if strict_claimed and s not in ("retro_weather", "academic", "todays_edition"):
            bans = "; ".join(
                f"{wk}/{_writer_names.get(wk, wk)} BANNED (already in {claiming})"
                for wk, claiming in strict_claimed.items()
            )
            line += f" — BANNED HERE: {bans}"
        slot_line_list.append(line)
    slot_lines = "\n".join(slot_line_list)

    # Summary exclusion block (belt-AND-suspenders — appears after the slot plan)
    exclusion_block = ""
    if strict_claimed:
        claims_str = "; ".join(
            f"{wk}/{_writer_names.get(wk, wk)} is claimed by {sp}"
            for wk, sp in strict_claimed.items()
        )
        exclusion_block = (
            f"STRICT-WRITER EXCLUSIONS (today): {claims_str}. "
            "Using any of these writers on a second slot is a hard FAIL that "
            "blocks publish. The ban is already marked inline on each slot above.\n"
        )

    issue_brief = (
        f"=== TODAY'S ISSUE TYPE: {issue['masthead_label']} ===\n"
        f"Total slots: exactly {total_slots} ({writer_slots} writer stories"
        + (" + 1 editor's note in slot 1" if has_editor else "") + ").\n"
        f"Writer pool (default): {', '.join(pool)}. Prefer these writers.\n"
        "SLOT PLAN — STRICT. Each slot's spread_type is fixed by layout; you "
        "only choose the writer and the story. Do NOT reorder. Do NOT swap "
        "templates. Do NOT repeat a spread_type.\n"
        f"{slot_lines}\n"
        f"{exclusion_block}"
        f"Tone: {issue['tone_hint']}\n"
        f"Weather rule: {weather_rule}\n"
        f"Exception lane: {issue['override_rule']}\n"
        f"{editor_brief}"
    )

    recent_block = ledger.build_recent_coverage_block()

    # When Gemini has pre-assigned story angles, Claude writes only.
    # When assignments are absent, Claude self-selects (full selection_rules).
    has_editor_slot = (
        bool(issue.get("spread_plan")) and issue["spread_plan"][0] == "todays_edition"
    )

    if story_assignments:
        editorial_block = _format_locked_assignments(story_assignments)

        # The todays_edition slot (Maggie's editor's note) is NEVER in the
        # research file — Claude must always write it. Explicitly instruct Claude
        # so it doesn't get confused by the count mismatch (5 dossiers, 6 slots).
        if has_editor_slot:
            editor_note_block = (
                "━━━ [Maggie Halstead — Today's Edition] — SLOT 1 ━━━\n"
                "  writer_key: editor_in_chief\n"
                "  spread_type: todays_edition\n"
                "  Job: Write Maggie's editor's note. She has read ALL of the locked\n"
                "  stories below. Her note: teases the must-read story first, connects\n"
                "  the issue's threads with one sharp observation, signs off warmly.\n"
                "  Body: 120-160 words. recurring_bit_content: '— M.H., Editor'\n"
                "  Pull quote: one sentence that captures the issue's throughline.\n"
            )
            editorial_block = editor_note_block + "\n" + editorial_block

        job_line = (
            "Story angles for slots 2+ are LOCKED by the editorial director — do NOT change them. "
            "Slot 1 is always Maggie Halstead's editor's note (todays_edition) — write it fresh "
            "based on the locked stories. "
            "Your only job is to write each story in the full voice of its assigned writer. "
            "No partisan political opinion pieces."
        )
    else:
        editorial_block = selection_rules
        job_line = (
            "Your job: curate exactly the number of stories specified above, each written in the "
            "full voice of one of our staff writers. No partisan political opinion pieces. "
            "No duplicate beats unless a writer EARNS two slots with clearly distinct stories."
        )

    return (
        f"You are the editor of The Boise Pulse — today's issue is for {date_str}.\n\n"
        f"{issue_brief}\n"
        f"{job_line}\n\n"
        f"{editorial_block}\n"
        f"{format_discipline}\n"
        "WRITER VOICES — each story MUST sound like its writer. Sentence-level precision:\n"
        f"{voices}\n\n"
        + (f"{recent_block}\n" if recent_block else "")
        + "TODAY'S RAW DATA:\n"
        + f"### Google News (RSS)\n{news_summary}\n\n"
        f"### NWS Forecast\n{weather_summary}\n\n"
        f"### r/Boise\n{reddit_summary}\n\n"
        f"### YouTube trending\n{youtube_summary}\n\n"
        f"### Wikipedia On-This-Day\n{otd_summary}\n\n"
        f"OUTPUT: call the `submit_issue` tool with exactly {total_slots} stories. "
        "Each story object looks like this (example):\n"
        f"{schema_example}\n\n"
        "Body length follows the tone: deep-dive day = 4-5 paragraphs of 100-140 words each; "
        "weekend-guide day = 3-4 paragraphs of 80-110 words each; quick-hits day = 2-3 "
        "paragraphs of 60-90 words each. Use the spread_type listed in the plan for each slot. "
        "Include the writer's recurring bit in `recurring_bit_content`.\n\n"
        "QUOTES INSIDE PROSE: prefer typographic smart quotes \u201c and \u201d for any "
        "quotation inside body/deck/headline/pull_quote text (it reads better in "
        "print). Apostrophes are fine as-is."
    )


def _format_corrections(fails: list) -> str:
    """Turn a list of voice_lint Finding tuples into a CORRECTIONS block
    appended to the retry prompt. Only shows FAILs (WARNs are advisory).

    Groups by slot so Claude can see "slot 2 has these 3 problems" rather
    than reading a flat list. Each Finding is (severity, writer, slot, msg).
    """
    by_slot: dict[int, list[tuple[str, str]]] = {}
    for item in fails:
        if len(item) < 4:
            continue
        _severity, writer, slot, msg = item[0], item[1], item[2], item[3]
        by_slot.setdefault(slot, []).append((writer, msg))

    lines = [
        "CORRECTIONS REQUIRED — your previous draft failed these deterministic "
        "lint checks. The checks run mechanically (no LLM-as-judge); every item "
        "below is a literal, fixable violation. Re-generate the FULL stories "
        "array with ALL of these resolved.",
        "",
    ]
    for slot in sorted(by_slot.keys()):
        issues = by_slot[slot]
        label = f"slot {slot}" if slot else "issue-level"
        lines.append(f"[{label}]")
        for writer, msg in issues:
            lines.append(f"  - ({writer}) {msg}")
        lines.append("")
    lines.append(
        "Keep everything else from the previous draft that DIDN'T fail. "
        "Fix only the flagged items. Preserve the spread_plan slot order "
        "exactly — do not rearrange."
    )
    return "\n".join(lines)


def _curate_with_claude(
    raw: dict,
    date: datetime,
    issue: IssueConfig,
    corrections: list | None = None,
) -> list[dict] | None:
    """Call Claude to curate today's issue using direct JSON text output.

    Uses plain text completion (no tool_use) to avoid double-encoding issues.
    Claude returns a raw JSON array; we extract and parse it directly.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ai_engine] ANTHROPIC_API_KEY not set — skipping Claude backend")
        return None
    try:
        from anthropic import Anthropic  # type: ignore
    except ImportError:
        print("[ai_engine] anthropic package not installed — skipping Claude backend")
        return None

    client = Anthropic(api_key=api_key)
    prompt = _build_curation_prompt(raw, date, issue)
    if corrections:
        prompt = prompt + "\n\n" + _format_corrections(corrections)

    # Explicit JSON output instruction appended to the prompt
    prompt += (
        "\n\n"
        "OUTPUT FORMAT — NON-NEGOTIABLE:\n"
        "Respond with ONLY a raw JSON array of story objects.\n"
        "No preamble. No explanation. No markdown. No code fences.\n"
        "Your entire response must start with [ and end with ].\n"
        "Use proper JSON escaping: double-quotes inside strings must be \\.\n"
    )

    try:
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        print(f"[ai_engine] Anthropic API call failed: {e}")
        return None

    stop_reason = getattr(msg, "stop_reason", "?")
    print(f"[ai_engine] stop_reason={stop_reason}")
    if stop_reason == "max_tokens":
        print("[ai_engine] FATAL: response truncated — raise max_tokens")
        return None

    # Extract text from response
    text = ""
    for block in (msg.content or []):
        if getattr(block, "type", None) == "text":
            text = block.text.strip()
            break

    if not text:
        print("[ai_engine] empty text response from Claude")
        return None

    # Strip markdown code fences if Claude added them despite instructions
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

    # Find the JSON array bounds
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        print(f"[ai_engine] no JSON array in response; first 300 chars: {text[:300]}")
        return None

    json_str = text[start:end]
    try:
        stories = json.loads(json_str)
    except Exception as e:
        print(f"[ai_engine] JSON parse failed: {e}")
        print(f"[ai_engine] first 300 chars of extracted JSON: {json_str[:300]}")
        return None

    if isinstance(stories, list) and stories and all(isinstance(s, dict) for s in stories):
        return stories

    print(f"[ai_engine] unexpected structure: {type(stories)}, len={len(stories) if isinstance(stories, list) else 'n/a'}")
    return None
