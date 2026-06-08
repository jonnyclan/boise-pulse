"""Email-safe renderer for The Boise Pulse.

The web renderer (html_renderer.py) is the full-CSS showpiece. Email clients
(Gmail, Outlook, Apple Mail) break modern CSS — grid, flex, clamp, CSS vars,
position, web fonts, even <style> in some cases. So this module rebuilds the
SAME content as a table-based, inline-styled, 600px, web-safe-font email that
*looks* like the brand and acts as a GATEWAY: a scannable, beautiful digest
whose job is to drive readers to the full web issue.

Design rules enforced here:
  • Layout = nested <table role="presentation">, never flex/grid.
  • Every style is inline; the one <style> block is progressive enhancement
    only (link hover + a mobile stack), never load-bearing.
  • Fonts are web-safe stacks: Georgia (serif, stands in for Fraunces),
    Arial/system (sans, for Inter), Courier New (mono labels).
  • The heartbeat SVG is web-only (Gmail strips SVG) — email uses a terracotta
    rule in its place.
  • The Vitals is a 2-col table grid with status colors as cell borders/dots.
"""
from __future__ import annotations

import html
import re
from datetime import datetime

# ── Brand palette (same hexes as the web system) ─────────────────────────────
NAVY = "#0B1E33"; NAVY2 = "#102A45"; PAPER = "#F4EFE6"; PAPER2 = "#ECE5D6"
ACCENT = "#C24A26"; GOLD = "#E0A23C"; SKY = "#6FA8D6"; INK = "#1A1A1A"; MUTE = "#5C6672"
CREAM_MUTE = "#D9CBB3"
SERIF = "Georgia, 'Times New Roman', serif"
SANS = "-apple-system, 'Segoe UI', Arial, Helvetica, sans-serif"
MONO = "'Courier New', Courier, monospace"

_CELL = {
    "good":    {"bd": "#5E9E6B", "bg": "#16301F", "tx": "#C6E7CE"},
    "neutral": {"bd": SKY,       "bg": "#10283F", "tx": "#C3DAEF"},
    "caution": {"bd": GOLD,      "bg": "#382B12", "tx": "#F1DBAB"},
    "alert":   {"bd": ACCENT,    "bg": "#3A1A10", "tx": "#F0B9A3"},
}
_ADV = {
    "info":    {"bd": SKY,    "bg": "#10283F", "tx": "#D6E8F6", "ic": "&#9432;"},
    "caution": {"bd": GOLD,   "bg": "#382B12", "tx": "#F3E2BC", "ic": "&#9650;"},
    "alert":   {"bd": ACCENT, "bg": "#3A1A10", "tx": "#F4C9B8", "ic": "&#9888;"},
}


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _strip_md(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"\1", text)
    text = re.sub(r"^>\s*", "", text)
    return text.strip()


def _excerpt(body: str, limit: int = 280) -> str:
    if not body:
        return ""
    first = next((p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()), "")
    first = _strip_md(first)
    if len(first) > limit:
        cut = first[:limit].rsplit(" ", 1)[0].rstrip(",.;:—- ")
        first = cut + "…"
    return first


def _writer(story: dict) -> tuple[str, str]:
    from .personas import PERSONAS
    p = PERSONAS.get(story.get("writer_key", ""), {})
    return p.get("name", "The Boise Pulse"), p.get("section", "")


# ── Vitals (table grid) ──────────────────────────────────────────────────────
def _vitals_email(vitals: dict | None) -> str:
    if not vitals or not vitals.get("cells"):
        return ""
    cells = vitals.get("cells", [])
    rows = ""
    for i in range(0, len(cells), 2):
        pair = cells[i:i + 2]
        tds = ""
        for c in pair:
            col = _CELL.get(c.get("status", "neutral"), _CELL["neutral"])
            tds += (
                f'<td width="50%" valign="top" style="padding:4px;">'
                f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{col["bg"]};border-left:3px solid {col["bd"]};">'
                f'<tr><td style="padding:10px 12px;">'
                f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
                f'<td style="font-family:{MONO};font-size:11px;font-weight:bold;letter-spacing:1px;text-transform:uppercase;color:{col["tx"]};">{_esc(c.get("icon",""))} {_esc(c.get("label",""))}</td>'
                f'<td align="right" style="font-family:{SANS};font-size:14px;color:{col["bd"]};line-height:1;">&#9679;</td>'
                f'</tr></table>'
                f'<div style="font-family:{SERIF};font-weight:bold;font-size:20px;color:{PAPER};margin:5px 0 2px;">{_esc(c.get("main","—"))}</div>'
                f'<div style="font-family:{MONO};font-size:11px;color:{col["tx"]};line-height:1.4;">{_esc(c.get("sub",""))}</div>'
                f'</td></tr></table></td>'
            )
        if len(pair) == 1:
            tds += '<td width="50%"></td>'
        rows += f'<tr>{tds}</tr>'

    adv = vitals.get("advisory") or {}
    adv_html = ""
    if adv.get("text"):
        a = _ADV.get(adv.get("level", "info"), _ADV["info"])
        adv_html = (
            f'<tr><td colspan="2" style="padding:4px;">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{a["bg"]};border-top:1px solid {a["bd"]};">'
            f'<tr><td style="padding:11px 14px;font-family:{SERIF};font-style:italic;font-size:14px;color:{a["tx"]};line-height:1.5;">'
            f'<span style="color:{a["bd"]};font-weight:bold;">{a["ic"]} </span>{_esc(adv.get("text",""))}'
            f'</td></tr></table></td></tr>'
        )

    return (
        f'<tr><td style="background:{NAVY};padding:16px 16px 6px;border-top:3px solid {ACCENT};">'
        f'<div style="font-family:{MONO};font-size:12px;font-weight:bold;letter-spacing:3px;text-transform:uppercase;color:{GOLD};">&#9829; THE VITALS</div>'
        f'<div style="font-family:{SERIF};font-style:italic;font-size:14px;color:{SKY};margin-top:3px;">What\'s actually happening outside</div>'
        f'</td></tr>'
        f'<tr><td style="background:{NAVY};padding:6px 12px 14px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}{adv_html}</table>'
        f'</td></tr>'
    )


# ── Story blocks ─────────────────────────────────────────────────────────────
def _editor_block(story: dict) -> str:
    body = "".join(
        f'<p style="margin:0 0 12px;font-family:{SERIF};font-size:16px;line-height:1.6;color:{INK};">{_esc(_strip_md(p))}</p>'
        for p in re.split(r"\n\s*\n", story.get("body", "")) if p.strip()
    )
    sig = _esc(story.get("recurring_bit_content", "") or "— M.H., Editor")
    return (
        f'<tr><td style="background:{PAPER};padding:26px 28px 8px;">'
        f'<div style="font-family:{MONO};font-size:11px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;color:{ACCENT};">Today&#8217;s Edition</div>'
        f'<div style="height:14px;"></div>{body}'
        f'<div style="font-family:{MONO};font-size:12px;color:{MUTE};letter-spacing:1px;">{sig}</div>'
        f'</td></tr>'
    )


def _story_block(story: dict, web_url: str) -> str:
    name, section = _writer(story)
    topic = _esc(story.get("topic_label", section))
    headline = _esc(story.get("headline", ""))
    deck = _esc(story.get("deck", ""))
    excerpt = _esc(_excerpt(story.get("body", "")))
    deck_html = f'<div style="font-family:{SERIF};font-style:italic;font-size:16px;color:#43403a;line-height:1.45;margin:6px 0 10px;">{deck}</div>' if deck else ""
    excerpt_html = f'<p style="margin:0 0 14px;font-family:{SANS};font-size:15px;line-height:1.6;color:{INK};">{excerpt}</p>' if excerpt else ""
    return (
        f'<tr><td style="background:{PAPER};padding:0 28px;"><div style="border-top:1px solid #D6CBB4;height:1px;line-height:1px;">&nbsp;</div></td></tr>'
        f'<tr><td style="background:{PAPER};padding:22px 28px 6px;">'
        f'<div style="font-family:{MONO};font-size:11px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;color:{ACCENT};">{topic}</div>'
        f'<div style="font-family:{SERIF};font-weight:bold;font-size:24px;line-height:1.15;color:{NAVY};margin:8px 0 0;">{headline}</div>'
        f'{deck_html}{excerpt_html}'
        f'<a href="{_esc(web_url)}" style="font-family:{MONO};font-size:12px;font-weight:bold;letter-spacing:1px;text-transform:uppercase;color:{ACCENT};text-decoration:none;">Read the full piece &#8594;</a>'
        f'<div style="font-family:{MONO};font-size:11px;color:{MUTE};margin-top:10px;letter-spacing:0.5px;">By {_esc(name)} &#183; {_esc(section)}</div>'
        f'</td></tr>'
    )


# ── Page ─────────────────────────────────────────────────────────────────────
def render_email_issue(date: datetime, stories: list[dict], issue: dict | None = None,
                       vitals: dict | None = None, web_url: str = "#") -> str:
    date_line = date.strftime("%A &#183; %B %d, %Y").upper()
    issue_label = (issue or {}).get("masthead_label", "")
    blocks = ""
    for s in stories:
        if s.get("writer_key") == "editor_in_chief":
            blocks += _editor_block(s)
        else:
            blocks += _story_block(s, web_url)

    stamp = (
        f'<div style="font-family:{MONO};font-size:11px;font-weight:bold;letter-spacing:3px;'
        f'text-transform:uppercase;color:{GOLD};border:1px solid {GOLD};display:inline-block;'
        f'padding:5px 12px;margin-top:14px;">{_esc(issue_label)}</div>' if issue_label else ""
    )
    cta = (
        f'<tr><td style="background:{NAVY2};padding:16px 28px;text-align:center;">'
        f'<a href="{_esc(web_url)}" style="font-family:{MONO};font-size:12px;font-weight:bold;letter-spacing:1.5px;text-transform:uppercase;color:{GOLD};text-decoration:none;">Read the full issue online &#8594;</a>'
        f'</td></tr>'
    )
    footer = (
        f'<tr><td style="background:{NAVY};padding:24px 28px;text-align:center;border-top:3px solid {ACCENT};">'
        f'<div style="font-family:{SERIF};font-style:italic;font-size:18px;color:{PAPER};">The Boise Pulse</div>'
        f'<div style="font-family:{SERIF};font-style:italic;font-size:13px;color:{CREAM_MUTE};margin-top:8px;line-height:1.5;">Reply and tell us what we missed &#8212; we read every one.</div>'
        f'<div style="font-family:{MONO};font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#6E7C8C;margin-top:14px;">{date.strftime("%Y-%m-%d")} &#183; built in Boise</div>'
        f'</td></tr>'
    )

    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="color-scheme" content="light only">'
        '<title>The Boise Pulse</title>'
        '<style>a{text-decoration:none;} @media (max-width:600px){ .col{display:block!important;width:100%!important;} }</style>'
        f'</head><body style="margin:0;padding:0;background:{NAVY};">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{NAVY};"><tr><td align="center" style="padding:0;">'
        f'<table role="presentation" width="600" cellpadding="0" cellspacing="0" align="center" style="width:600px;max-width:600px;">'
        # Masthead
        f'<tr><td style="background:{NAVY};padding:30px 28px 24px;text-align:center;border-bottom:3px solid {ACCENT};">'
        f'<div style="font-family:{MONO};font-size:11px;letter-spacing:4px;color:{SKY};">{date_line}</div>'
        f'<div style="font-family:{SERIF};font-weight:bold;font-size:42px;letter-spacing:-1px;color:{PAPER};margin-top:8px;line-height:1;">The Boise <span style="color:{ACCENT};">Pulse</span></div>'
        f'<div style="height:2px;background:{ACCENT};width:180px;margin:14px auto 0;line-height:2px;font-size:2px;">&nbsp;</div>'
        f'<div style="font-family:{SERIF};font-style:italic;font-size:15px;color:{CREAM_MUTE};margin-top:14px;line-height:1.5;">The Treasure Valley, three mornings a week &#8212; written for the people who live here.</div>'
        f'{stamp}'
        f'</td></tr>'
        f'{_vitals_email(vitals)}'
        f'{blocks}'
        f'{cta}'
        f'{footer}'
        '</table></td></tr></table></body></html>'
    )
