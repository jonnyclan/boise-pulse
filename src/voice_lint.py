"""Deterministic voice-drift checks for generated stories.

Runs after curation, before rendering. Catches the 80% of voice drift that's
mechanically detectable: banned words, missing signature lines, wrong
spread_type, wrong writer_key, structural problems, stat-field contract
violations, third-person self-reference, throat-clearing openers, and
issue-type-specific word-count drift.

Two severities:
  - FAIL: loud, blocks the issue by default (e.g. Hayley used "babe").
    Set VOICE_LINT_STRICT=0 to downgrade to a warning for emergency publishes.
  - WARN: prints, doesn't block. Voice drift that's worth noticing but not
    catastrophic (e.g. Kelsey skipped the proper-noun hammer).

Design note: we do NOT call Claude to judge Claude. The LLM-as-judge pattern
is nice but expensive, slow, and itself prone to drift. Deterministic checks
run in milliseconds, cost zero, and never change behavior between deploys.
"""

from __future__ import annotations

import os
import re
from typing import Callable


# A finding is a (severity, writer_key, slot, message) tuple.
# severity: "FAIL" | "WARN"
Finding = tuple[str, str, int, str]


# ────────────────────────────────────────────────────────────
# Per-writer checks
# Each check takes the story dict and returns a list of (severity, message).

Check = Callable[[dict], list[tuple[str, str]]]


def _body(story: dict) -> str:
    return story.get("body", "") or ""


def _all_text(story: dict) -> str:
    return " ".join(
        str(story.get(k, "") or "")
        for k in ("headline", "deck", "body", "pull_quote", "recurring_bit_content")
    )


def _word_boundary_search(text: str, word: str) -> bool:
    pattern = r"\b" + re.escape(word) + r"\b"
    return bool(re.search(pattern, text, re.IGNORECASE))


def _check_lifestyle(story: dict) -> list[tuple[str, str]]:
    """Hayley: banned words + required verdict + required HAYLEY'S RATIO."""
    out: list[tuple[str, str]] = []
    text = _all_text(story)
    banned = ["babe", "you guys", "obsessed", "iykyk"]
    for w in banned:
        if _word_boundary_search(text, w):
            out.append(("FAIL", f"Hayley used banned word: '{w}'"))
    if not ("TRIED IT" in text or "CALLING IT" in text):
        out.append(("FAIL", "Hayley missing binary verdict (TRIED IT / CALLING IT)"))
    if "HAYLEY'S RATIO" not in text.upper().replace("&#X27;", "'"):
        out.append(("FAIL", "Hayley missing HAYLEY'S RATIO line ($ / minutes / kids-out-of-2)"))
    return out


def _check_history(story: dict) -> list[tuple[str, str]]:
    """Wade: must close with the exact dinner line; must open with 'You know that'."""
    out: list[tuple[str, str]] = []
    body = _body(story).rstrip()
    # Exact closer — case-sensitive, allowing for trailing whitespace/markdown.
    # Strip trailing *italics* or quotes that might wrap it.
    tail = body[-120:]
    if "That's the one you tell at dinner." not in tail:
        out.append(("FAIL", "Wade missing closer: \"That's the one you tell at dinner.\""))
    head = body[:200].lower()
    if "you know that" not in head:
        out.append(("WARN", "Wade didn't open with 'You know that [thing] on [street]?'"))
    return out


def _check_weather(story: dict) -> list[tuple[str, str]]:
    """Pete: must contain 'MOOD OF THE SKY:' somewhere near the top."""
    out: list[tuple[str, str]] = []
    top = (_body(story)[:200] + " " + story.get("deck", "")).upper()
    if "MOOD OF THE SKY" not in top:
        out.append(("FAIL", "Pete missing 'MOOD OF THE SKY: [word]' opener"))
    return out


def _check_food(story: dict) -> list[tuple[str, str]]:
    """Nina: body must close with '— Nina's Table:' verdict."""
    out: list[tuple[str, str]] = []
    tail = _body(story).rstrip()[-200:]
    if "Nina's Table:" not in tail and "Nina's Table —" not in tail:
        out.append(("FAIL", "Nina missing closing '— Nina's Table: [verdict]' line"))
    # T3.2 — price floor. Nina's signature pairs the exact dish with the exact
    # price to the dollar; a food piece with no price reads like a press release.
    if not re.search(r"\$\d", _body(story)):
        out.append(("WARN", "Nina: price floor — no exact dish price ($N) in the piece"))
    return out


# Title-Case tokens that are NOT band/act names — venues, cities, weekdays,
# and Dex's own signature words. Lets the named-act floor fire only when a
# lineup is discussed but no actual act is named.
_ARTS_NONACT_TOKENS: set[str] = {
    "Dex", "Drop", "Boise", "Treasure", "Valley", "East", "West", "North",
    "South", "End", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
    "Saturday", "Sunday", "Shrine", "Social", "Club", "Neurolux", "Knitting",
    "Factory", "Olympic", "Record", "Exchange", "Egyptian", "Theatre",
    "Morrison", "Center", "Shredder", "Ming", "Studios", "Treefort", "The",
    "Coop", "Sasha",
}


def _check_arts(story: dict) -> list[tuple[str, str]]:
    """Dex: 'Dex's Drop' opener (FAIL) + named-act floor (WARN)."""
    out: list[tuple[str, str]] = []
    text = _all_text(story)
    if "Dex's Drop" not in text and "Dex\u2019s Drop" not in text:
        out.append(("FAIL", "Dex missing 'Dex’s Drop' opener"))
    # T3.2 — named-act floor. If the piece discusses a lineup but names no
    # actual act, it's the aggregation tell: Dex IS the writer who names the
    # opener before the headliner.
    body = _body(story)
    if re.search(r"\b(opener|headliner|band|set|act|show)s?\b", body, re.IGNORECASE):
        # Collect Title-Case tokens but DROP the sentence-initial one of each
        # sentence — "That's", "The", etc. are noise, not act names.
        caps: set[str] = set()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", body):
            toks = re.findall(r"\b([A-Z][a-zA-Z]{2,}(?:['’][a-zA-Z]+)?)\b", sentence)
            caps.update(toks[1:])
        if not (caps - _ARTS_NONACT_TOKENS):
            out.append(("WARN", "Dex: named-act floor — discusses a lineup but names no specific band/act"))
    return out


# Treasure Valley place / subdivision / developer / street tokens — Sal's
# proper-noun hammer. Presence of any one clears the floor.
_REALESTATE_PLACE_RE = re.compile(
    r"\bNorth End\b|\bMeridian\b|\bEagle\b|\bKuna\b|\bNampa\b|\bStar\b"
    r"|\bGarden City\b|\bthe Bench\b|\bHarris Ranch\b|\bHidden Springs\b"
    r"|\bAvimor\b|\bBanbury\b|\bCBH\b|\bBrighton\b|\bTrilogy\b|\bSilvercreek\b"
    r"|\bKeller Williams\b|\b\d{2,4}\s+[NSEW]\b"
    r"|\b(?:Street|Ave|Avenue|Road|Rd|Blvd|Boulevard|Lane|Drive)\b",
)


def _check_real_estate(story: dict) -> list[tuple[str, str]]:
    """Sal: concrete number (WARN) + named place/developer floor (WARN)."""
    out: list[tuple[str, str]] = []
    body = _body(story)
    if not re.search(r"\$\d|\d{3,}", body):
        out.append(("WARN", "Sal missing a concrete number ($ or 3+ digit figure)"))
    # T3.2 — place floor. A median with no neighbourhood, subdivision,
    # developer, or street named is the averaged number Sal exists to un-average.
    if not _REALESTATE_PLACE_RE.search(body):
        out.append(("WARN", "Sal: place floor — no named neighbourhood, subdivision, developer, or street"))
    return out


# Dani's civic proper-noun hammer: a named official/title, an agency acronym,
# or a bill/ordinance number. Any one clears the floor.
_EDITORIAL_CIVIC_RE = re.compile(
    r"\b(?:Mayor|Council(?:man|woman|member)?|Commissioner|Senator|Representative|Clerk|Director|Governor)\b"
    r"|\b(?:ACHD|COMPASS|CCDC|CDH)\b"
    r"|\b(?:House Bill|Senate Bill|HB|SB|Ordinance|Resolution)\s*#?\s*\d+"
    r"|\bordinance\b[^.]*\d",
    re.IGNORECASE,
)


def _check_editorial(story: dict) -> list[tuple[str, str]]:
    """Dani: proper-noun density (WARN) + civic proper-noun floor (WARN)."""
    out: list[tuple[str, str]] = []
    body = _body(story)
    # Count Capitalized Words that aren't sentence-initial. Rough proxy for
    # proper-noun density; no strict threshold — just warn if suspiciously bare.
    caps = re.findall(r"(?<=[\.\s\-\,])([A-Z][a-zA-Z]{2,})", body)
    if len(set(caps)) < 3:
        out.append(("WARN", "Dani: fewer than 3 distinct proper-noun citations"))
    # T3.2 — civic floor. Dani's whole moat is the named official, the agency,
    # the bill number. Without one the piece is a generic op-ed. Bracketed
    # placeholders like '[Mayor McLean...]' satisfy this — the slot is filled,
    # pending fact verification by the Fact Ledger.
    if not _EDITORIAL_CIVIC_RE.search(body):
        out.append(("WARN", "Dani: civic floor — no named official/agency or bill/ordinance number"))
    return out


def _check_trending(story: dict) -> list[tuple[str, str]]:
    """Jess: should have a 3-bullet FRESH OFF THE PRESS block OR named thread."""
    out: list[tuple[str, str]] = []
    text = _all_text(story).upper()
    if "FRESH OFF THE PRESS" not in text:
        out.append(("FAIL", "Jess missing 'FRESH OFF THE PRESS' 3-bullet box"))
    return out


def _check_sports(story: dict) -> list[tuple[str, str]]:
    """Kelsey: should name-drop the proper-noun hammer (The Blue, Broncos, MW)."""
    out: list[tuple[str, str]] = []
    text = _all_text(story)
    hammers = ["The Blue", "Broncos", "Steelheads", "MW ", "Mountain West", "Albertsons"]
    if not any(h in text for h in hammers):
        out.append(("WARN", "Kelsey missing proper-noun hammer (Blue/Broncos/MW/etc.)"))
    return out


def _check_editor_in_chief(story: dict) -> list[tuple[str, str]]:
    """Maggie: 3 paragraphs, 100-180 words, sign-off NOT in body."""
    out: list[tuple[str, str]] = []
    body = _body(story)
    paras = [p for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
    if len(paras) != 3:
        out.append(("WARN", f"Maggie: expected 3 paragraphs, got {len(paras)}"))
    words = len(body.split())
    if not (100 <= words <= 180):
        out.append(("WARN", f"Maggie: body {words} words, target 120-160 (hard bound 100-180)"))
    if "M.H." in body or "Margaret Halstead" in body:
        out.append(("FAIL", "Maggie: sign-off ('— M.H.') must NOT be in body (renderer adds it)"))
    return out


CHECKS: dict[str, Check] = {
    "lifestyle": _check_lifestyle,
    "history": _check_history,
    "weather": _check_weather,
    "food": _check_food,
    "arts": _check_arts,
    "real_estate": _check_real_estate,
    "editorial": _check_editorial,
    "trending": _check_trending,
    "sports": _check_sports,
    "editor_in_chief": _check_editor_in_chief,
}


# ────────────────────────────────────────────────────────────
# Writer first-name table for the third-person self-reference check (T1.7).
# Use first names only — writers can legitimately reference each other by
# last name, and the editor's note references pool writers by first name on
# purpose, so we only flag a writer using their OWN first name in body.
_WRITER_FIRST_NAMES: dict[str, str] = {
    "sports": "Kelsey",
    "weather": "Pete",
    "real_estate": "Sal",
    "history": "Wade",
    "food": "Nina",
    "arts": "Dex",
    "trending": "Jess",
    "editorial": "Dani",
    "lifestyle": "Hayley",
    # editor_in_chief (Maggie) is already covered by the "M.H./Margaret
    # Halstead must not appear in body" rule in _check_editor_in_chief.
}


# ────────────────────────────────────────────────────────────
# Stat-field schema per spread (T1.1)
# Keys are spread_type; value is (max_chars, human description). Spread types
# not listed here have no stat-length enforcement — the field is optional or
# decorative only.
_STAT_SCHEMA: dict[str, tuple[int, str]] = {
    "big_stat":      (15, "one massive scalar — '$519K', '82°F', '39° SWING'"),
    "broadsheet":    (15, "scoreboard number — '37', '$2.1M', '67 DAYS'"),
    "retro_weather": (12, "single temperature or compound — '82°F', '82/43°F'"),
}


# ────────────────────────────────────────────────────────────
# Writer/spread canonical pairings (T1.4)
# The design of a spread is often tied to a writer's beat — render_broadsheet
# has a football-shaped SVG baked in; render_academic has Wade's chatty-
# neighbor chrome; retro_weather is Pete's home. If a story arrives on the
# wrong spread, the render is wrong in ways no amount of voice polish fixes.
#
# STRICT: spread_type MUST pair with one of these writers (FAIL on violation).
# SOFT:   spread_type PREFERS these writers (WARN on violation).
_SPREAD_STRICT: dict[str, set[str]] = {
    "academic":        {"history"},              # Wade-only: chatty-neighbor chrome
    "retro_weather":   {"weather"},              # Pete-only: weather visual grammar
    "todays_edition":  {"editor_in_chief"},      # Maggie-only: editor panel
    "broadsheet":      {"sports", "real_estate"},  # football SVG fits both beats
}
_SPREAD_SOFT: dict[str, set[str]] = {
    "big_stat":    {"real_estate", "weather", "sports"},
    "editorial":   {"editorial", "arts"},
    "midnight":    {"arts", "editorial"},
    "rose_stamp":  {"trending", "food", "lifestyle", "arts"},
    "terminal":    {"trending"},
    "broadside":   {"trending", "history"},
    # hero is intentionally unrestricted — it's the marquee slot.
}


# ────────────────────────────────────────────────────────────
# Throat-clearing opener patterns (T2.2)
# These are the AI-tell openers that make copy feel like a generator. Caught
# at sentence start, case-insensitive. Each pattern catches the gambit, not
# the exact wording — generators paraphrase.
_THROAT_CLEARING_PATTERNS: list[tuple[str, str]] = [
    (r"^here'?s what",                                "Throat-clearing: 'Here's what…'"),
    (r"^in the world of",                             "Throat-clearing: 'In the world of…'"),
    (r"^it'?s worth noting that",                     "Throat-clearing: 'It's worth noting that…'"),
    (r"^the strongest version of the argument",       "Throat-clearing: 'The strongest version of the argument…'"),
    (r"^let'?s (?:be clear|talk about|start with)",   "Throat-clearing: 'Let's be clear / talk about / start with…'"),
    (r"^before (?:we|you) ",                          "Throat-clearing: 'Before we/you…'"),
    (r"^there'?s something to be said",               "Throat-clearing: 'There's something to be said…'"),
]


# ────────────────────────────────────────────────────────────
# Word-count targets per issue-type (T2.1)
# Tuesday is deep-dive — paragraphs earn length. Friday is quick-hits —
# paragraphs are lean. Thursday (weekend guide) is permissive: listings and
# picks vary in shape too much for a single target.
#
# Tuple: (words_per_para_min, words_per_para_max, paras_min, paras_max)
_WORDCOUNT_TARGETS: dict[str, tuple[int, int, int, int]] = {
    "deep_dive":      (100, 140, 4, 5),
    "quick_hits":     (60, 90, 2, 3),
    # weekend_guide is intentionally absent — no target.
}

# Writers exempt from word-count enforcement even on strict days. Maggie has
# her own explicit budget. Jess's FRESH OFF THE PRESS block is a bullet list,
# not a paragraph — the check would fire incorrectly on it.
_WORDCOUNT_EXEMPT: set[str] = {"editor_in_chief", "trending"}


# ------------------------------------------------------------
# Source / beat ownership (T3.1 — source-beat mismatch)
# Certain sources are bound to a beat: "Athletics" is Kelsey's, "NWS" is
# Pete's, "MLS"/"Regional Realtors" is Sal's. When a story's ONLY recognised
# source(s) belong to a foreign beat, it's almost always a placeholder or
# aggregation tell (e.g. a music column sourced solely to "Boise State
# University"). Neutral sources — a venue, a person, KTVB, a trade journal —
# own no beat and never trip this check.
_SOURCE_OWNERS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bathletics\b", re.I), "sports"),
    (re.compile(r"\bbroncos?\b", re.I), "sports"),
    (re.compile(r"\bmountain west\b|\bMW\b", re.I), "sports"),
    (re.compile(r"\bboise state university\b", re.I), "sports"),
    (re.compile(r"national weather|\bNWS\b", re.I), "weather"),
    (re.compile(r"intermountain mls|regional realtors|\bMLS\b|county assessor", re.I), "real_estate"),
    (re.compile(r"historical society|\bISHS\b", re.I), "history"),
    (re.compile(r"city council|city clerk|\bACHD\b|legislature|\bCOMPASS\b|\bCCDC\b|\bCDH\b", re.I), "editorial"),
    (re.compile(r"\br/boise\b|\br/idaho\b|nextdoor|reddit", re.I), "trending"),
]

# A writer may lean on a neighbouring beat's institution (real-estate and
# editorial both touch zoning; history leans on civic records). Each writer's
# OWN beat is always acceptable.
_ACCEPTABLE_SOURCE_BEATS: dict[str, set[str]] = {
    "sports":      {"sports"},
    "weather":     {"weather"},
    "real_estate": {"real_estate", "editorial"},
    "editorial":   {"editorial", "real_estate"},
    "history":     {"history", "editorial"},
    "food":        {"food"},
    "arts":        {"arts"},
    "trending":    {"trending"},
    "lifestyle":   {"lifestyle"},
}

# Split a source line into its parts on common separators (middot, pipe,
# semicolon, slash, spaced em-dash, comma-space).
_SOURCE_SPLIT = re.compile(r"\s*[·|;/]\s*|\s+—\s+|,\s+")


# ────────────────────────────────────────────────────────────
# Per-story, non-writer-specific checks
# These run on EVERY story regardless of writer_key.

def _check_stat_length(story: dict) -> list[tuple[str, str]]:
    """T1.1 — spread-specific stat length contract.
    big_stat/broadsheet/retro_weather render `stat` as ONE massive scalar.
    A sentence dropped in there explodes the layout and signals amateur hour.
    """
    out: list[tuple[str, str]] = []
    spread = (story.get("spread_type") or "").strip()
    schema = _STAT_SCHEMA.get(spread)
    if not schema:
        return out
    max_chars, example = schema
    stat = (story.get("stat") or "").strip()
    if not stat or stat == "—":
        # Missing stat on a stat-heavy spread is WARN (renderer shows em-dash).
        out.append(("WARN", f"spread '{spread}' renders a big stat; `stat` is empty"))
        return out
    # Count visible chars ignoring simple degree/currency decoration.
    if len(stat) > max_chars:
        out.append((
            "FAIL",
            f"spread '{spread}' needs a scalar stat ({example}) — got {len(stat)} chars: {stat!r}",
        ))
    # Sentence-shaped stats almost always have a period or multiple spaces.
    if re.search(r"[a-zA-Z][\.·][ ]", stat) or stat.count(" ") > 2:
        out.append((
            "FAIL",
            f"spread '{spread}' stat looks like a sentence, not a scalar: {stat!r}",
        ))
    return out


def _check_throat_clearing(story: dict) -> list[tuple[str, str]]:
    """T2.2 — ban AI-tell opener patterns."""
    out: list[tuple[str, str]] = []
    body = _body(story).lstrip()
    # Skip markdown bold/italic wrappers at the head ("**The Lede:**").
    first_sentence = re.split(r"[\.\!\?\n]", body, maxsplit=1)[0].strip()
    # Strip leading markdown-style labels, block markers, and quotes.
    first_sentence = re.sub(r"^[\*\>\-\s`]+", "", first_sentence).strip()
    # If the first line is a label like "The Lede:" or "MOOD OF THE SKY:",
    # skip past it to the actual first sentence.
    if ":" in first_sentence[:40]:
        parts = first_sentence.split(":", 1)
        if len(parts) == 2 and parts[1].strip():
            first_sentence = parts[1].strip()
    for pattern, msg in _THROAT_CLEARING_PATTERNS:
        if re.search(pattern, first_sentence, re.IGNORECASE):
            out.append(("WARN", msg))
            break
    return out


def _check_em_dash_budget(story: dict) -> list[tuple[str, str]]:
    """T2.4 — WARN if em-dash usage averages >3 per paragraph."""
    out: list[tuple[str, str]] = []
    body = _body(story)
    if not body:
        return out
    paras = [p for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
    if not paras:
        return out
    # Count both em-dashes (—) and double-hyphens (--) as em-dash proxies.
    dash_total = sum(p.count("\u2014") + p.count("--") for p in paras)
    avg = dash_total / len(paras)
    if avg > 3.0:
        out.append((
            "WARN",
            f"em-dash budget: avg {avg:.1f}/para ({dash_total} total across {len(paras)} paras) — the dash is doing real punctuation's job",
        ))
    return out


def _check_third_person_self_reference(story: dict) -> list[tuple[str, str]]:
    """T1.7 — writer referring to themselves by first name in body.
    Sign-offs are handled by renderers ('— Nina's Table:' is fine as a closer
    line, but 'Nina thinks' inside body paragraph 2 is the tell). We only flag
    the possessive and verb forms that can only be self-reference.
    """
    out: list[tuple[str, str]] = []
    writer = (story.get("writer_key") or "").strip()
    first_name = _WRITER_FIRST_NAMES.get(writer)
    if not first_name:
        return out
    body = _body(story)
    if not body:
        return out
    # Legitimate signature lines like "— Nina's Table:" or "HAYLEY'S RATIO"
    # pass. Flag: "Name's been", "Name thinks", "Name has been", "Name notes",
    # "Name writes", "Name would", "What Name", where Name is the writer's
    # first name and it's clearly self-referential narration.
    patterns = [
        rf"\bWhat {first_name}(?:'s|\u2019s)?\s+(?:been|has|did|found)",
        rf"\b{first_name}(?:'s|\u2019s)\s+been\s",
        rf"\b{first_name}\s+(?:thinks|notes|writes|argues|has been|would|reckons)\b",
    ]
    hits: list[str] = []
    for pat in patterns:
        for m in re.finditer(pat, body):
            hits.append(m.group(0))
    # Drop hits that are clearly inside a signature line (e.g. "— Nina's
    # Table: …" which Nina SHOULD write — but that exact phrase is caught by
    # _check_food and has 'Table' not a verb after it).
    hits = [h for h in hits if "Table:" not in h and "Ratio" not in h]
    if hits:
        sample = hits[0]
        out.append((
            "WARN",
            f"{first_name}: third-person self-reference in own piece — {sample!r}",
        ))
    return out


def _check_ending_summary(story: dict) -> list[tuple[str, str]]:
    """T2.3 — ending-summary restatement pattern.
    A last paragraph that begins with 'That's the whole story', 'In the end',
    'The bottom line', 'So there it is', etc. is the AI-tell summary move.
    Wade's canonical closer ('That's the one you tell at dinner.') is fine —
    it's a voice move, not a summary. We only flag the generic ones.
    """
    out: list[tuple[str, str]] = []
    body = _body(story).rstrip()
    if not body:
        return out
    paras = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
    if not paras:
        return out
    last = paras[-1].strip().lower()
    last_first = re.sub(r"^[\*\>\-\s`]+", "", last)[:80]
    endings = [
        r"^in the end",
        r"^the bottom line",
        r"^so there it is",
        r"^that'?s the whole story",
        r"^at the end of the day",
        r"^when all is said and done",
        r"^to sum (?:up|it up)",
        r"^in summary",
    ]
    for pat in endings:
        if re.search(pat, last_first, re.IGNORECASE):
            out.append(("WARN", f"Ending-summary pattern in final paragraph: {last_first[:50]!r}"))
            break
    return out


def _check_wordcount(story: dict, issue_slug: str | None) -> list[tuple[str, str]]:
    """T2.1 — per-issue word-count targets.
    Tuesday: 100-140 words/para, 4-5 paras. Friday: 60-90, 2-3. Thursday: no
    target. WARN on drift; FAIL when a paragraph is >2x the upper bound
    (that's a serious editorial miss, not a minor overrun).
    """
    out: list[tuple[str, str]] = []
    if not issue_slug:
        return out
    target = _WORDCOUNT_TARGETS.get(issue_slug)
    if not target:
        return out
    writer = (story.get("writer_key") or "").strip()
    if writer in _WORDCOUNT_EXEMPT:
        return out
    body = _body(story).strip()
    if not body:
        return out
    w_min, w_max, p_min, p_max = target
    paras = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
    n_paras = len(paras)
    if n_paras < p_min or n_paras > p_max:
        out.append((
            "WARN",
            f"wordcount: {n_paras} paras, target {p_min}-{p_max} for {issue_slug}",
        ))
    worst_over = 0
    drifters = 0
    for p in paras:
        wc = len(p.split())
        if wc < w_min or wc > w_max:
            drifters += 1
        if wc > w_max * 2:
            worst_over = max(worst_over, wc)
    if drifters:
        out.append((
            "WARN",
            f"wordcount: {drifters}/{n_paras} paras outside target {w_min}-{w_max}w",
        ))
    if worst_over:
        out.append((
            "FAIL",
            f"wordcount: paragraph hit {worst_over} words — over 2x budget ({w_max})",
        ))
    return out


def _check_source_beat_match(story: dict) -> list[tuple[str, str]]:
    """T3.1 — source/beat mismatch.
    FAIL when EVERY recognised source belongs to a beat the writer doesn't own
    (e.g. Dex's music column sourced solely to "Boise State University").
    Neutral sources own no beat and pass silently; this fires only on a clear
    cross-beat institutional source with no native source to balance it.
    """
    out: list[tuple[str, str]] = []
    writer = (story.get("writer_key") or "").strip()
    if writer in ("editor_in_chief", ""):
        return out
    source = (story.get("source") or "").strip()
    if not source:
        return out
    parts = [p for p in _SOURCE_SPLIT.split(source) if p and p.strip()]
    recognised: list[str] = []
    for part in parts:
        for pat, beat in _SOURCE_OWNERS:
            if pat.search(part):
                recognised.append(beat)
                break
    if not recognised:
        return out
    allowed = _ACCEPTABLE_SOURCE_BEATS.get(writer, {writer})
    if any(b in allowed for b in recognised):
        return out
    foreign = sorted(set(recognised))
    out.append((
        "FAIL",
        f"source-beat mismatch: '{writer}' sourced solely to {foreign} "
        f"institution(s) — reads like a placeholder/aggregation source: {source!r}",
    ))
    return out


# ------------------------------------------------------------
# Cross-story / structural checks

def _check_structure(stories: list[dict], spread_plan: list[str]) -> list[Finding]:
    """Wrong spread_type, wrong count, duplicate writers, writer/spread drift."""
    out: list[Finding] = []
    if len(stories) != len(spread_plan):
        out.append(("FAIL", "_structure", 0,
                    f"Got {len(stories)} stories, expected {len(spread_plan)}"))
    for i, (story, planned) in enumerate(zip(stories, spread_plan), start=1):
        actual = story.get("spread_type", "")
        if actual != planned:
            out.append(("FAIL", story.get("writer_key", "?"), i,
                        f"Spread mismatch in slot {i}: got '{actual}', plan says '{planned}'"))

    for i, story in enumerate(stories, start=1):
        spread = (story.get("spread_type") or "").strip()
        writer = (story.get("writer_key") or "").strip()
        if not spread or not writer:
            continue
        if (story.get("source") or "").strip().lower() == "mock curator":
            continue
        strict_set = _SPREAD_STRICT.get(spread)
        soft_set = _SPREAD_SOFT.get(spread)
        if strict_set and writer not in strict_set:
            out.append((
                "FAIL", writer, i,
                f"Spread '{spread}' is reserved for writer(s) {sorted(strict_set)} — got '{writer}'",
            ))
        elif soft_set and writer not in soft_set:
            out.append((
                "WARN", writer, i,
                f"Spread '{spread}' prefers writer(s) {sorted(soft_set)} — got '{writer}'",
            ))

    from collections import Counter
    writers = Counter(
        (s.get("writer_key") or "?") for s in stories
        if (s.get("source") or "").strip().lower() != "mock curator"
    )
    for w, c in writers.items():
        if w == "editor_in_chief":
            if c > 1:
                out.append(("FAIL", w, 0, f"Editor-in-chief appears {c}x in one issue"))
            continue
        if c >= 2:
            out.append((
                "FAIL", w, 0,
                f"Writer '{w}' appears {c}x in one issue (same-writer duplication is a bug; "
                f"if genuinely intentional, split across issues)",
            ))
    return out


# ------------------------------------------------------------
# Public entry point

def lint(
    stories: list[dict],
    spread_plan: list[str],
    issue_slug: str | None = None,
) -> list[Finding]:
    """Return all findings. Empty list = clean.

    `issue_slug` (optional) enables issue-type-specific word-count checks
    (T2.1). When omitted, word-count checks are skipped.
    """
    out: list[Finding] = []
    out.extend(_check_structure(stories, spread_plan))
    for i, story in enumerate(stories, start=1):
        writer = (story.get("writer_key") or "").strip()
        if (story.get("source") or "").strip().lower() == "mock curator":
            continue

        check = CHECKS.get(writer)
        if check:
            for severity, msg in check(story):
                out.append((severity, writer, i, msg))

        for severity, msg in _check_stat_length(story):
            out.append((severity, writer, i, msg))
        for severity, msg in _check_throat_clearing(story):
            out.append((severity, writer, i, msg))
        for severity, msg in _check_em_dash_budget(story):
            out.append((severity, writer, i, msg))
        for severity, msg in _check_third_person_self_reference(story):
            out.append((severity, writer, i, msg))
        for severity, msg in _check_ending_summary(story):
            out.append((severity, writer, i, msg))
        for severity, msg in _check_wordcount(story, issue_slug):
            out.append((severity, writer, i, msg))
        for severity, msg in _check_source_beat_match(story):
            out.append((severity, writer, i, msg))
    return out


def report(findings: list[Finding]) -> None:
    """Pretty-print findings to stdout. No side effects beyond printing."""
    if not findings:
        print("[voice-lint] clean")
        return
    fails = [f for f in findings if f[0] == "FAIL"]
    warns = [f for f in findings if f[0] == "WARN"]
    print(f"[voice-lint] {len(fails)} FAIL / {len(warns)} WARN")
    for sev, writer, slot, msg in findings:
        marker = "X" if sev == "FAIL" else "-"
        slot_str = f"slot {slot}" if slot else "issue"
        print(f"  {marker} {sev} [{writer}@{slot_str}] {msg}")


def enforce(findings: list[Finding]) -> None:
    """Raise if any FAIL finding exists. VOICE_LINT_STRICT=0 disables."""
    strict = os.getenv("VOICE_LINT_STRICT", "1").strip() != "0"
    fails = [f for f in findings if f[0] == "FAIL"]
    if fails and strict:
        raise VoiceLintError(
            f"{len(fails)} voice-lint failure(s) — set VOICE_LINT_STRICT=0 to bypass"
        )


class VoiceLintError(RuntimeError):
    pass
