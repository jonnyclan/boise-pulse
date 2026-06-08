"""The Vitals — outdoor-decision dashboard data for The Boise Pulse.

This is the "open it even when I'm in a hurry" module: a six-cell, scannable
read on whether you can do your Boise thing outside today. It is NOT a weather
widget — Apple Weather already won "what's the temperature." The Vitals answers
"can I run / float / ski / hike right now, and what should I plan around."

Data flow (matches the Gemini-fed plan):
  • If today's research file carries a `vitals` block, use it verbatim
    (that's the live, Gemini-researched path).
  • Otherwise build a season-aware mock from whatever NWS weather was fetched,
    so `mock run` and previews still render a full, believable module.

Pure data — no HTML lives here. Rendering is html_renderer.render_vitals().

Cell schema (per cell):
    {"icon": str, "label": str, "main": str, "sub": str, "status": str}
    status ∈ {"good", "neutral", "caution", "alert"}  (drives the dot color)
Advisory schema:
    {"level": "info" | "caution" | "alert", "text": str}

The grid is a fixed shape: 2 constant anchors (Weather, Daylight) + 4 seasonal
cells. Only the four seasonal cells swap by season, so the format stays familiar
and an issue's Vitals takes minutes to fill.
"""
from __future__ import annotations

from datetime import datetime

VALID_STATUS = {"good", "neutral", "caution", "alert"}


def _season(month: int) -> str:
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "fall"


def _weather_cell(raw: dict) -> dict:
    """Anchor cell #1 — pulled from real NWS data when present."""
    periods = ((raw or {}).get("weather") or {}).get("periods") or []
    if periods:
        p = periods[0]
        t = p.get("temperature", "—")
        u = p.get("temperatureUnit", "F")
        short = (p.get("shortForecast", "") or "").strip()
        return {
            "icon": "🌡️", "label": "Weather",
            "main": f"{t}°{u}", "sub": short or "Treasure Valley",
            "status": "neutral",
        }
    # No live data (common in mock) — illustrative placeholder.
    return {
        "icon": "🌡️", "label": "Weather",
        "main": "72°F", "sub": "illustrative — live via research",
        "status": "neutral",
    }


# Anchor cell #2 + the 4 seasonal cells. Mock values are illustrative so the
# preview grid looks alive and exercises every status color; the live pipeline
# overwrites all of this with the research `vitals` block.
_DAYLIGHT = {
    "winter": {"icon": "🌅", "label": "Daylight", "main": "5:32 PM", "sub": "sunrise 7:58 AM · gaining", "status": "neutral"},
    "spring": {"icon": "🌅", "label": "Daylight", "main": "8:14 PM", "sub": "sunrise 7:02 AM", "status": "neutral"},
    "summer": {"icon": "🌅", "label": "Daylight", "main": "9:33 PM", "sub": "sunrise 6:09 AM", "status": "good"},
    "fall":   {"icon": "🌅", "label": "Daylight", "main": "6:48 PM", "sub": "sunrise 7:41 AM · shrinking", "status": "neutral"},
}

_SEASONAL: dict[str, list[dict]] = {
    "winter": [
        {"icon": "🎿", "label": "Bogus Basin", "main": "Open", "sub": "14 of 17 lifts · 4\" overnight", "status": "good"},
        {"icon": "🌫️", "label": "Inversion & Air", "main": "AQI 118", "sub": "valley socked in · sun up top", "status": "alert"},
        {"icon": "🛣️", "label": "Roads & Passes", "main": "Packed snow", "sub": "Bogus Rd chains advised", "status": "caution"},
        {"icon": "❄️", "label": "Overnight Low", "main": "21°F", "sub": "wrap the hose bib", "status": "caution"},
    ],
    "spring": [
        {"icon": "🥾", "label": "Foothills Trails", "main": "Soft", "sub": "mud below 4,000 ft", "status": "caution"},
        {"icon": "🌊", "label": "Boise River", "main": "1,140 cfs", "sub": "44°F · runoff beginning", "status": "neutral"},
        {"icon": "🤧", "label": "Pollen", "main": "Moderate", "sub": "juniper + tree season", "status": "caution"},
        {"icon": "💨", "label": "Air Quality", "main": "AQI 38", "sub": "good · clear visibility", "status": "good"},
    ],
    "summer": [
        {"icon": "💨", "label": "Air & Smoke", "main": "AQI 41", "sub": "good · no active smoke", "status": "good"},
        {"icon": "🌊", "label": "Boise River", "main": "1,890 cfs", "sub": "62°F · floatable soon", "status": "neutral"},
        {"icon": "🔥", "label": "Fire & UV", "main": "UV 9", "sub": "very high · stage 1 restrictions", "status": "caution"},
        {"icon": "🥵", "label": "Foothills Heat", "main": "94°F by 3p", "sub": "run before 9 or after 7", "status": "alert"},
    ],
    "fall": [
        {"icon": "🥾", "label": "Foothills Trails", "main": "Prime", "sub": "firm + tacky · go", "status": "good"},
        {"icon": "🍂", "label": "Cottonwoods", "main": "Peaking", "sub": "Greenbelt gold · ~1 wk left", "status": "good"},
        {"icon": "❄️", "label": "First Frost", "main": "34°F low", "sub": "cover the tomatoes tonight", "status": "caution"},
        {"icon": "💨", "label": "Air Quality", "main": "AQI 29", "sub": "good · crisp", "status": "good"},
    ],
}

_ADVISORY: dict[str, dict] = {
    "winter": {"level": "caution", "text": "Inversion's heaviest before noon — if the valley's grey and gritty, drive up to Bogus and find the sun above the murk."},
    "spring": {"level": "info", "text": "Trails firm up by midday. Give the upper foothills a morning to dry after rain before you chew them up."},
    "summer": {"level": "caution", "text": "Smoke can roll in fast this time of year — check the AQI before an afternoon run, and float the river early before the wind comes up."},
    "fall":   {"level": "info", "text": "Cottonwoods along the Greenbelt are turning — peak color is a one-week window, so don't wait for the weekend."},
}


def build_vitals(raw: dict, research: dict | None, date: datetime) -> dict | None:
    """Return a vitals dict for rendering, or None to skip the module.

    Gemini-fed `vitals` block wins. Otherwise a season-aware mock built from
    real weather where available + illustrative outdoor cells.
    """
    # 1) Live, research-fed path.
    if isinstance(research, dict):
        v = research.get("vitals")
        if isinstance(v, dict) and v.get("cells"):
            return v

    # 2) Season-aware mock.
    season = _season(date.month)
    cells = [_weather_cell(raw), *( dict(c) for c in _SEASONAL[season] ), dict(_DAYLIGHT[season])]
    return {
        "season": season,
        "cells": cells,
        "advisory": dict(_ADVISORY[season]),
        "_mock": not (isinstance(research, dict) and research.get("vitals")),
    }
