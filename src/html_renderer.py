"""HTML renderer for The Boise Pulse.

Pure Python, no AI. Takes a list of story dicts (see ai_engine.py schema) and
produces a self-contained HTML magazine.
"""

from __future__ import annotations

import html
import re
from datetime import datetime

# ────────────────────────────────────────────────────────────
# Tokens
# ────────────────────────────────────────────────────────────
GOOGLE_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=Fraunces:ital,opsz,wght@0,9..144,200..900;1,9..144,200..900&"
    "family=Inter:wght@300;400;600;700;900&"
    'family=JetBrains+Mono:wght@400;700&display=swap">'
)

BASE_CSS = """
:root {
  /* The Boise Pulse — dusk-over-the-foothills palette */
  --ink:    #0B1E33;  /* deep night-sky navy — chrome + dark spreads */
  --paper:  #F4EFE6;  /* sandstone / newsprint cream */
  --accent: #C24A26;  /* Boise sunset terracotta — primary accent */
  --gold:   #E0A23C;  /* golden-hour amber — featured accent */
  --sky:    #6FA8D6;  /* daytime / Basque blue — cool accent */
  --sage:   #5E7A5A;  /* foothills sage — "good" status, calm accent */
  --text:   #1A1A1A;  /* body ink on paper */
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 20px;
    line-height: 1.6;
    color: #1A1A1A;
    background: #0B1E33;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}
.fraunces { font-family: 'Fraunces', Georgia, serif; }
.inter { font-family: 'Inter', system-ui, sans-serif; }
.mono { font-family: 'JetBrains Mono', ui-monospace, monospace; }
.spread {
    min-height: 100vh;
    padding: clamp(2rem, 6vw, 6rem) clamp(1.5rem, 6vw, 6rem);
    position: relative;
    overflow: hidden;
}
.spread-inner { max-width: 1400px; margin: 0 auto; height: 100%; }
.stamp {
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.3em;
    font-size: 0.85rem;
}
.topic-label {
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.22em;
    font-size: 0.9rem;
    opacity: 0.85;
}
.byline {
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    font-size: 0.85rem;
    margin-top: 1rem;
    opacity: 0.75;
}
.source-line {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    opacity: 0.6;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid currentColor;
}
.recurring-bit {
    border: 1.5px solid currentColor;
    padding: 1.25rem 1.5rem;
    margin: 1.75rem 0;
}
.recurring-bit .label {
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.22em;
    font-size: 0.78rem;
    margin-bottom: 0.4rem;
    opacity: 0.85;
}
.recurring-bit .content {
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 500;
    font-size: clamp(1.05rem, 1.6vw, 1.3rem);
    line-height: 1.45;
}
@media (max-width: 720px) {
    body { font-size: 19px; }
    .spread { padding: 3rem 1.25rem; }
}
@keyframes twinkle { 0%,100% { opacity: 0.2 } 50% { opacity: 1 } }
@keyframes blink   { 0%,49% { opacity: 1 } 50%,100% { opacity: 0 } }
"""

# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────
def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def body_paragraphs(body: str, para_class: str = "") -> str:
    if not body:
        return ""
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    cls = f' class="{para_class}"' if para_class else ""
    return "".join(f"<p{cls}>{_inline_md(esc(p))}</p>" for p in paras)


def _inline_md(text: str) -> str:
    """Very light inline markdown: **bold** and *italic*."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<em>\1</em>", text)
    return text


def byline_html(writer_name: str, section: str) -> str:
    return f'<div class="byline">By {esc(writer_name)} · {esc(section)}</div>'


def source_html(source: str) -> str:
    if not source:
        return ""
    return f'<div class="source-line">Source · {esc(source)}</div>'


# ────────────────────────────────────────────────────────────
# Spread renderers
# ────────────────────────────────────────────────────────────
def _writer_info(story: dict) -> tuple[str, str]:
    """Return (writer_name, section) from a persona key, resilient to bad keys."""
    from .personas import PERSONAS

    persona = PERSONAS.get(story.get("writer_key", ""), {})
    return persona.get("name", "The Boise Pulse"), persona.get("section", "")


def render_hero(story: dict) -> str:
    name, section = _writer_info(story)
    return f"""
<section class="spread spread-hero" style="background:#F4EFE6;color:#1A1A1A;">
  <style>
    .spread-hero .headline {{ font-family:'Fraunces',serif; font-weight:900; font-style:italic;
        font-size: clamp(3rem, 9vw, 9rem); line-height: 0.95; letter-spacing: -0.03em; }}
    .spread-hero .deck {{ font-family:'Fraunces',serif; font-style:italic; font-weight:400;
        font-size: clamp(1.4rem, 2.4vw, 2rem); margin-top: 1.25rem; max-width: 60ch; color:#333; }}
    .spread-hero .grid {{ display:grid; grid-template-columns: 2fr 1fr; gap:4rem; margin-top:3rem; }}
    .spread-hero .pull {{ font-family:'Fraunces',serif; font-style:italic; font-weight:500;
        font-size: clamp(1.6rem, 2.6vw, 2.4rem); color:#C24A26; border-left:3px solid #C24A26;
        padding-left:1.25rem; line-height:1.3; }}
    .spread-hero .rule {{ height:1px; background:#C24A26; margin:1.5rem 0; }}
    .spread-hero p {{ margin-bottom: 1.25rem; }}
    @media (max-width: 900px) {{ .spread-hero .grid {{ grid-template-columns:1fr; }} }}
  </style>
  <div class="spread-inner">
    <div class="topic-label" style="color:#C24A26;">{esc(story.get('topic_label',''))}</div>
    <h1 class="headline">{esc(story.get('headline',''))}</h1>
    <div class="rule"></div>
    <div class="deck">{esc(story.get('deck',''))}</div>
    <div class="grid">
      <div>{body_paragraphs(story.get('body',''))}</div>
      <div>
        <div class="pull">{esc(story.get('pull_quote',''))}</div>
        {byline_html(name, section)}
      </div>
    </div>
    {source_html(story.get('source',''))}
  </div>
</section>
"""


def render_big_stat(story: dict) -> str:
    name, section = _writer_info(story)
    return f"""
<section class="spread spread-bigstat" style="background:#FFFFFF;color:#0B1E33;">
  <style>
    .spread-bigstat .statnum {{ font-family:'Fraunces',serif; font-weight:200; font-style:italic;
        font-size: clamp(9rem, 28vw, 24rem); color:#C24A26; line-height:0.85;
        letter-spacing: -0.05em; }}
    .spread-bigstat .headline {{ font-family:'Fraunces',serif; font-weight:900;
        font-size: clamp(2.4rem, 5vw, 4.4rem); line-height:1.05; margin-top:1.5rem; max-width:24ch; }}
    .spread-bigstat .legend {{ font-family:'Inter',sans-serif; font-weight:700;
        text-transform:uppercase; letter-spacing:0.22em; font-size:0.9rem; margin-top:1rem; color:#555; }}
    .spread-bigstat .body {{ max-width:32rem; margin-top:2rem; }}
    .spread-bigstat p {{ margin-bottom:1.2rem; }}
  </style>
  <div class="spread-inner">
    <div class="topic-label" style="color:#C24A26;">{esc(story.get('topic_label',''))}</div>
    <div class="statnum">{esc(story.get('stat','—'))}</div>
    <div class="legend">{esc(story.get('deck',''))}</div>
    <h2 class="headline">{esc(story.get('headline',''))}</h2>
    <div class="body">{body_paragraphs(story.get('body',''))}</div>
    {byline_html(name, section)}
    {source_html(story.get('source',''))}
  </div>
</section>
"""


def render_academic(story: dict) -> str:
    name, section = _writer_info(story)
    body = story.get("body", "")
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    first_letter = paras[0][0] if paras else ""
    first_rest = paras[0][1:] if paras else ""
    rest_paras = paras[1:] if len(paras) > 1 else []

    dropcap_html = ""
    if paras:
        dropcap_html = (
            f'<p><span class="dropcap">{esc(first_letter)}</span>'
            f'{_inline_md(esc(first_rest))}</p>'
        )
    rest_html = "".join(f"<p>{_inline_md(esc(p))}</p>" for p in rest_paras)

    return f"""
<section class="spread spread-academic" style="background:#FAF6EE;color:#1F1A12;">
  <style>
    .spread-academic .meta {{ font-family:'Inter',sans-serif; font-weight:700;
        text-transform:uppercase; letter-spacing:0.22em; font-size:0.78rem; color:#6B4E2B; }}
    .spread-academic .headline {{ font-family:'Fraunces',serif; font-weight:900;
        font-size: clamp(2.6rem, 6vw, 5rem); line-height:1.02; margin-top:1.5rem;
        letter-spacing:-0.02em; max-width:22ch; }}
    .spread-academic .dropcap {{ font-family:'Fraunces',serif; font-weight:900; color:#6B4E2B;
        float:left; font-size: clamp(5rem,12vw,10rem); line-height:0.85;
        padding:0.3rem 0.8rem 0 0; }}
    .spread-academic .body {{ margin-top:2rem; column-count: 2; column-gap: 3rem; hyphens:auto;
        text-align: justify; }}
    .spread-academic p {{ margin-bottom: 1.25rem; break-inside:avoid; }}
    .spread-academic .pull {{ font-family:'Fraunces',serif; font-style:italic;
        font-size: clamp(1.5rem,2.4vw,2.2rem); text-align:center; color:#6B4E2B; margin:3rem 0;
        max-width: 34rem; margin-left:auto; margin-right:auto; }}
    @media (max-width: 820px) {{ .spread-academic .body {{ column-count:1; }} }}
  </style>
  <div class="spread-inner">
    <div class="meta">VOLUME I · ISSUE — · {esc(story.get('topic_label',''))}</div>
    <h2 class="headline">{esc(story.get('headline',''))}</h2>
    <div class="body">{dropcap_html}{rest_html}</div>
    <div class="pull">§ {esc(story.get('pull_quote',''))} §</div>
    {_academic_recurring_bit(story, section)}
    {byline_html(name, section)}
    {source_html(story.get('source',''))}
  </div>
</section>
"""


def _academic_recurring_bit(story: dict, section: str) -> str:
    """Render the academic recurring-bit with a writer-specific label.
    Hides the block entirely if content is empty or looks like prompt leak
    (contains instructional markers like 'open with' or 'close with')."""
    content = (story.get("recurring_bit_content") or "").strip()
    if not content:
        return ""
    low = content.lower()
    if ("open with" in low and "close with" in low) or low.startswith("—"):
        # Looks like the prompt instructions leaked through; suppress the block.
        return ""
    # Per-writer label. History writer (Wade) owns the "Drive-By History"
    # franchise; fall back to the classic Then vs. Now for non-history academic.
    writer_key = (story.get("writer_key") or "").strip().lower()
    label = "DRIVE-BY HISTORY" if writer_key == "history" else "THEN VS. NOW"
    return (
        '<div class="recurring-bit">'
        f'<div class="label">{label}</div>'
        f'<div class="content">{esc(content)}</div>'
        '</div>'
    )


def render_midnight(story: dict) -> str:
    name, section = _writer_info(story)
    # Build CSS starfield
    import random
    rng = random.Random(story.get("number", 1))
    stars = "".join(
        f'<span style="top:{rng.uniform(0,100):.1f}%;left:{rng.uniform(0,100):.1f}%;'
        f'animation-delay:{rng.uniform(0,4):.1f}s;width:{rng.choice([2,3,4])}px;'
        f'height:{rng.choice([2,3,4])}px;"></span>'
        for _ in range(50)
    )
    return f"""
<section class="spread spread-midnight">
  <style>
    .spread-midnight {{ background: radial-gradient(circle at 30% 20%, #1A2040 0%, #0B1020 70%);
        color:#F5E6A8; }}
    .spread-midnight .stars span {{ position:absolute; background:#FFD978; border-radius:50%;
        opacity:0.4; animation: twinkle 4s infinite ease-in-out; }}
    .spread-midnight .headline {{ font-family:'Fraunces',serif; font-style:italic; font-weight:900;
        font-size: clamp(2.8rem, 7vw, 6.5rem); color:#FFD978; text-align:center;
        text-shadow: 0 0 30px rgba(255,217,120,0.25); max-width:22ch; margin:0 auto;
        letter-spacing:-0.02em; line-height:1.02; }}
    .spread-midnight .body {{ max-width:52rem; margin:3rem auto 0; text-align:justify;
        font-size: clamp(1.05rem,1.4vw,1.2rem); line-height:1.8; }}
    .spread-midnight p {{ margin-bottom:1.3rem; }}
    .spread-midnight .pull {{ font-family:'Fraunces',serif; font-style:italic; font-weight:400;
        font-size: clamp(1.5rem,2.4vw,2.2rem); text-align:center; margin:3rem auto;
        max-width:32rem; }}
    .spread-midnight .topic-label {{ color:#FFD978; text-align:center; }}
  </style>
  <div class="stars">{stars}</div>
  <div class="spread-inner" style="position:relative;">
    <div class="topic-label">{esc(story.get('topic_label',''))}</div>
    <h2 class="headline">{esc(story.get('headline',''))}</h2>
    <div class="body">{body_paragraphs(story.get('body',''))}</div>
    <div class="pull">— {esc(story.get('pull_quote',''))} —</div>
    <div style="text-align:center;">{byline_html(name, section)}</div>
    {source_html(story.get('source',''))}
  </div>
</section>
"""


def render_retro_weather(story: dict) -> str:
    name, section = _writer_info(story)
    mood = (story.get("recurring_bit_content") or "").replace("MOOD OF THE SKY:", "").strip()
    mood = mood or "Mixed"
    return f"""
<section class="spread spread-weather">
  <style>
    .spread-weather {{ background: linear-gradient(135deg, #4A90E2, #1E4D8C); color:#FFFFFF;
        position:relative; }}
    .spread-weather::before {{ content:''; position:absolute; inset:0; pointer-events:none;
        background: repeating-linear-gradient(0deg, rgba(0,0,0,0.08) 0px, rgba(0,0,0,0.08) 1px,
        transparent 1px, transparent 3px); }}
    .spread-weather .mood-banner {{ background:#FFD93D; color:#1A1A1A; padding:0.75rem 1.25rem;
        display:inline-flex; align-items:baseline; gap:1.25rem; }}
    .spread-weather .mood-banner .label {{ font-family:'Inter',sans-serif; font-weight:900;
        letter-spacing:0.25em; font-size:0.85rem; text-transform:uppercase; }}
    .spread-weather .mood-banner .word {{ font-family:'Fraunces',serif; font-style:italic;
        font-weight:900; font-size:1.5rem; }}
    .spread-weather .temp {{ font-family:'Fraunces',serif; font-weight:900;
        font-size: clamp(7rem, 18vw, 16rem); line-height:0.9; color:#FFFFFF;
        text-shadow: 6px 6px 0 rgba(255,217,61,0.55); letter-spacing:-0.04em; margin-top:1.5rem; }}
    .spread-weather .headline {{ font-family:'Fraunces',serif; font-weight:900; font-style:italic;
        font-size: clamp(2.8rem, 6vw, 5.5rem); line-height:1.02; margin-top:1rem; max-width:22ch; }}
    .spread-weather .body {{ max-width:44rem; margin-top:2rem; border-left:3px solid #FFD93D;
        padding-left:1.5rem; }}
    .spread-weather p {{ margin-bottom:1.2rem; color: rgba(255,255,255,0.95); }}
    .spread-weather .forecast-strip {{ display:grid; grid-template-columns:repeat(3,1fr); gap:1rem;
        margin-top:2.5rem; border:2px solid rgba(255,217,61,0.6); padding:1rem; }}
    .spread-weather .forecast-cell {{ text-align:center; border-right:1px solid rgba(255,217,61,0.3);
        padding:0.5rem 0.25rem; }}
    .spread-weather .forecast-cell:last-child {{ border-right:none; }}
    .spread-weather .sun-svg {{ position:absolute; top:3rem; right:3rem; opacity:0.7; }}
    @media (max-width:720px) {{ .spread-weather .forecast-strip {{ grid-template-columns:1fr; }} }}
  </style>
  <svg class="sun-svg" width="90" height="90" viewBox="0 0 100 100" aria-hidden="true">
    <circle cx="50" cy="50" r="22" fill="#FFD93D"/>
    <g stroke="#FFD93D" stroke-width="4" stroke-linecap="round">
      <line x1="50" y1="5"  x2="50" y2="20"/>
      <line x1="50" y1="80" x2="50" y2="95"/>
      <line x1="5"  y1="50" x2="20" y2="50"/>
      <line x1="80" y1="50" x2="95" y2="50"/>
      <line x1="15" y1="15" x2="26" y2="26"/>
      <line x1="74" y1="74" x2="85" y2="85"/>
      <line x1="15" y1="85" x2="26" y2="74"/>
      <line x1="74" y1="26" x2="85" y2="15"/>
    </g>
  </svg>
  <div class="spread-inner" style="position:relative;">
    <div class="topic-label">{esc(story.get('topic_label',''))}</div>
    <div class="mood-banner">
      <span class="label">Mood of the Sky</span>
      <span class="word">{esc(mood)}</span>
    </div>
    <div class="temp">{esc(story.get('stat','—'))}</div>
    <h2 class="headline">{esc(story.get('headline',''))}</h2>
    <div class="body">{body_paragraphs(story.get('body',''))}</div>
    <div class="forecast-strip">
      <div class="forecast-cell"><div class="stamp">TODAY</div><div style="font-family:'Fraunces';font-weight:900;font-size:2.2rem;">{esc(story.get('stat',''))}</div><div>{esc(mood)}</div></div>
      <div class="forecast-cell"><div class="stamp">TONIGHT</div><div style="font-family:'Fraunces';font-weight:900;font-size:2.2rem;">—</div><div>Cooler</div></div>
      <div class="forecast-cell"><div class="stamp">TOMORROW</div><div style="font-family:'Fraunces';font-weight:900;font-size:2.2rem;">—</div><div>Shifting</div></div>
    </div>
    {byline_html(name, section)}
    {source_html(story.get('source',''))}
  </div>
</section>
"""


def render_broadsheet(story: dict) -> str:
    name, section = _writer_info(story)
    # Split out "The Lede" from the body if it's embedded
    body = story.get("body", "")
    lede_match = re.match(r"\*\*The Lede:\*\*\s*(.+?)(?:\n\n|$)", body, re.DOTALL)
    lede_sentence = story.get("recurring_bit_content", "").replace("THE LEDE —", "").strip()
    if lede_match:
        lede_sentence = lede_sentence or lede_match.group(1).strip()
        remainder = body[lede_match.end():].lstrip()
    else:
        remainder = body

    # Sports-context line (e.g. "BSU FOOTBALL · SPRING CAMP · APRIL 17"). Optional.
    context_line = (story.get("context_line") or "").strip()

    # Score-like stat box — if the story has a short numeric `stat`, we treat it as a
    # scoreboard hook that further signals "sports". Kelsey's stat usually pairs a
    # number with a meaning; we show the number big, the meaning in small caps.
    stat = (story.get("stat") or "").strip()
    stat_label = (story.get("stat_label") or "").strip() or "TAPE"

    return f"""
<section class="spread spread-broadsheet">
  <style>
    .spread-broadsheet {{ background:#0A1428; color:#F4EFE6; }}
    .spread-broadsheet::before {{
        content:''; position:absolute; inset:0; pointer-events:none; opacity:0.6;
        background: repeating-linear-gradient(90deg,
          rgba(224,162,60,0.05) 0px, rgba(224,162,60,0.05) 1px,
          transparent 1px, transparent 120px);
    }}
    .spread-broadsheet .section-bar {{ display:flex; align-items:center;
        gap:1rem; padding-bottom:0.75rem; border-bottom:2px solid #E0A23C;
        margin-bottom:1.25rem; flex-wrap:wrap; }}
    .spread-broadsheet .stamp-amber {{ font-family:'Inter',sans-serif; font-weight:900;
        text-transform:uppercase; letter-spacing:0.3em; color:#E0A23C; font-size:0.95rem; }}
    .spread-broadsheet .context-line {{ font-family:'Inter',sans-serif; font-weight:700;
        text-transform:uppercase; letter-spacing:0.22em; color:rgba(224,162,60,0.75);
        font-size:0.78rem; padding-left:1rem; border-left:2px solid rgba(224,162,60,0.4); }}
    .spread-broadsheet .ball-svg {{ margin-left:auto; }}
    .spread-broadsheet .headline {{ font-family:'Fraunces',serif; font-weight:900;
        font-size: clamp(3.5rem, 12vw, 12rem); line-height:0.92; letter-spacing:-0.03em;
        margin-top:1rem; color:#F4EFE6; }}
    .spread-broadsheet .deck {{ font-family:'Fraunces',serif; font-style:italic; font-weight:400;
        font-size: clamp(1.3rem, 2vw, 1.8rem); margin-top:1.25rem; color:rgba(244,239,230,0.85);
        max-width:62ch; }}
    .spread-broadsheet .lede {{ border-left: 6px solid #E0A23C; padding: 0.5rem 1.5rem;
        margin: 2.5rem 0; font-family:'Fraunces',serif; font-style:italic; font-weight:500;
        font-size: clamp(1.4rem, 2.2vw, 2rem); line-height:1.3; color:#F4EFE6; }}
    .spread-broadsheet .lede .label {{ font-family:'Inter',sans-serif; font-weight:900;
        letter-spacing:0.3em; color:#E0A23C; font-size:0.8rem; display:block; margin-bottom:0.5rem; }}
    .spread-broadsheet .scoreboard {{ display:inline-grid; grid-template-columns:auto auto;
        gap:0 1.25rem; align-items:baseline; padding:1rem 1.5rem;
        border:2px solid #E0A23C; margin:1.5rem 0;
        background:rgba(224,162,60,0.05); }}
    .spread-broadsheet .scoreboard .num {{ font-family:'Fraunces',serif; font-weight:900;
        font-size: clamp(3rem,6vw,5rem); color:#E0A23C; line-height:0.95; letter-spacing:-0.03em; }}
    .spread-broadsheet .scoreboard .label {{ font-family:'Inter',sans-serif; font-weight:900;
        text-transform:uppercase; letter-spacing:0.3em; font-size:0.75rem;
        color:rgba(244,239,230,0.75); max-width:14rem; line-height:1.3; }}
    .spread-broadsheet .columns {{ column-count:3; column-gap:3rem; margin-top:2rem;
        column-rule: 1px solid rgba(224,162,60,0.4); }}
    .spread-broadsheet p {{ margin-bottom:1.2rem; break-inside:avoid; font-size:1.05rem;
        line-height:1.7; color:rgba(244,239,230,0.92); }}
    .spread-broadsheet p:first-of-type::first-letter {{ font-family:'Fraunces',serif;
        font-weight:900; font-size:4rem; line-height:0.85; float:left;
        padding:0.25rem 0.6rem 0 0; color:#E0A23C; }}
    .spread-broadsheet .pull {{ font-family:'Fraunces',serif; font-style:italic; font-weight:500;
        font-size: clamp(1.5rem, 2.5vw, 2.2rem); color:#E0A23C; text-align:center;
        max-width:36rem; margin: 2.5rem auto; line-height:1.3; }}
    @media (max-width: 980px) {{ .spread-broadsheet .columns {{ column-count:2; }} }}
    @media (max-width: 680px) {{ .spread-broadsheet .columns {{ column-count:1; }}
        .spread-broadsheet .ball-svg {{ display:none; }} }}
  </style>
  <div class="spread-inner">
    <div class="section-bar">
      <span class="stamp-amber">{esc(story.get('topic_label','THE BENCH'))}</span>
      {"<span class='context-line'>" + esc(context_line) + "</span>" if context_line else ""}
      <svg class="ball-svg" width="72" height="42" viewBox="0 0 72 42" aria-hidden="true">
        <ellipse cx="36" cy="21" rx="32" ry="16" fill="none" stroke="#E0A23C" stroke-width="2"/>
        <path d="M 4 21 Q 36 -4 68 21 Q 36 46 4 21 Z" fill="none" stroke="#E0A23C" stroke-width="2" opacity="0.5"/>
        <line x1="18" y1="21" x2="54" y2="21" stroke="#E0A23C" stroke-width="2"/>
        <line x1="24" y1="17" x2="24" y2="25" stroke="#E0A23C" stroke-width="2"/>
        <line x1="30" y1="17" x2="30" y2="25" stroke="#E0A23C" stroke-width="2"/>
        <line x1="36" y1="17" x2="36" y2="25" stroke="#E0A23C" stroke-width="2"/>
        <line x1="42" y1="17" x2="42" y2="25" stroke="#E0A23C" stroke-width="2"/>
        <line x1="48" y1="17" x2="48" y2="25" stroke="#E0A23C" stroke-width="2"/>
      </svg>
    </div>
    <h1 class="headline">{esc(story.get('headline',''))}</h1>
    <div class="deck">{esc(story.get('deck',''))}</div>
    <div class="lede">
      <span class="label">The Lede</span>
      {esc(lede_sentence or story.get('pull_quote',''))}
    </div>
    {("<div class='scoreboard'><div class='num'>" + esc(stat) + "</div><div class='label'>" + esc(stat_label) + "</div></div>") if stat else ""}
    <div class="pull">"{esc(story.get('pull_quote',''))}"</div>
    <div class="columns">{body_paragraphs(remainder)}</div>
    {byline_html(name, section)}
    {source_html(story.get('source',''))}
  </div>
</section>
"""


def render_terminal(story: dict) -> str:
    name, section = _writer_info(story)
    return f"""
<section class="spread spread-terminal">
  <style>
    .spread-terminal {{ background:#050807; color:#39FF6A; font-family:'JetBrains Mono',monospace;
        padding-top: 2rem; }}
    .spread-terminal::before {{ content:''; position:absolute; inset:0; pointer-events:none;
        background: repeating-linear-gradient(0deg, rgba(57,255,106,0.04) 0px, rgba(57,255,106,0.04) 1px,
        transparent 1px, transparent 3px); }}
    .spread-terminal .chrome {{ display:flex; gap:0.5rem; align-items:center; margin-bottom:1.5rem;
        border-bottom:1px solid rgba(57,255,106,0.2); padding-bottom:1rem; }}
    .spread-terminal .dot {{ width:12px; height:12px; border-radius:50%; }}
    .spread-terminal .title {{ color:rgba(57,255,106,0.6); margin-left:1rem; font-size:0.9rem; }}
    .spread-terminal .prompt {{ color:rgba(57,255,106,0.6); margin-bottom:0.75rem; }}
    .spread-terminal .headline {{ font-family:'JetBrains Mono',monospace; font-weight:700;
        font-size: clamp(1.6rem, 3.4vw, 3.2rem); line-height:1.2; margin: 1rem 0 1.5rem; }}
    .spread-terminal .cursor {{ display:inline-block; width:0.6em; background:#39FF6A; color:#050807;
        margin-left:0.2em; animation: blink 1s infinite step-end; }}
    .spread-terminal .body {{ font-size:1rem; line-height:1.7; max-width:68ch; }}
    .spread-terminal p {{ margin-bottom:1rem; }}
    .spread-terminal .comment {{ color:rgba(57,255,106,0.55); border-left:2px solid rgba(57,255,106,0.3);
        padding-left:1rem; margin:2rem 0; }}
  </style>
  <div class="spread-inner" style="position:relative;">
    <div class="chrome">
      <span class="dot" style="background:#FF5F57"></span>
      <span class="dot" style="background:#FEBC2E"></span>
      <span class="dot" style="background:#28C840"></span>
      <span class="title">boise.term — zsh — 120×40</span>
    </div>
    <div class="prompt">$ boise --today --topic={esc(story.get('topic_label','').lower())}</div>
    <h2 class="headline">&gt; {esc(story.get('headline',''))}<span class="cursor">&nbsp;</span></h2>
    <div class="body">{body_paragraphs(story.get('body',''))}</div>
    <div class="comment">/* {esc(story.get('pull_quote',''))} */</div>
    {byline_html(name, section)}
    {source_html(story.get('source',''))}
  </div>
</section>
"""


def render_rose_stamp(story: dict) -> str:
    name, section = _writer_info(story)
    stamp_word = "HOT"
    if "trending" in (story.get("topic_label", "") or "").lower():
        stamp_word = "NOW"
    # T1.6: FRESH OFF THE PRESS box shows recurring_bit_content; dedupe body
    # paragraphs that are substantially the same as the recurring bit so the
    # reader never sees the same quote twice.
    rbit = (story.get("recurring_bit_content") or "").strip()
    body_raw = story.get("body", "") or ""
    if rbit:
        paras = [p.strip() for p in re.split(r"\n\s*\n", body_raw) if p.strip()]
        kept = []
        rbit_head = re.sub(r"\s+", " ", rbit[:80]).lower()
        for p in paras:
            p_head = re.sub(r"\s+", " ", p[:80]).lower()
            # Drop any paragraph whose first 40 chars overlap heavily with the
            # recurring bit (>= 32 chars shared from the start).
            if rbit_head and p_head and p_head.startswith(rbit_head[:32]):
                continue
            if rbit_head and rbit_head.startswith(p_head[:32]) and len(p_head) >= 32:
                continue
            kept.append(p)
        body_raw = "\n\n".join(kept)
    return f"""
<section class="spread spread-rose">
  <style>
    .spread-rose {{ background:#F8D3D0; color:#2B0A0A; position:relative; }}
    .spread-rose .stamp-svg {{ position:absolute; top:2rem; right:2rem; transform: rotate(12deg);
        opacity:0.95; }}
    .spread-rose .headline {{ font-family:'Fraunces',serif; font-weight:900;
        font-size: clamp(3rem, 8vw, 7rem); line-height:0.92; letter-spacing:-0.035em;
        max-width:18ch; margin-top:1rem; }}
    .spread-rose .deck {{ font-family:'Fraunces',serif; font-style:italic; font-weight:400;
        font-size: clamp(1.3rem, 2vw, 1.8rem); margin-top:1rem; max-width:60ch; color:#4a1414; }}
    .spread-rose .body {{ max-width:42rem; margin-top:2rem; font-size:1.05rem; line-height:1.65; }}
    .spread-rose p {{ margin-bottom:1.1rem; }}
    .spread-rose .pull {{ font-family:'Fraunces',serif; font-style:italic; font-weight:500;
        font-size: clamp(1.4rem, 2.4vw, 2.1rem); color:#C24A26; border-left:6px solid #C24A26;
        padding-left:1.25rem; margin:2rem 0; max-width:42rem; line-height:1.3; }}
    .spread-rose .recurring-bit {{ background:rgba(194,74,38,0.08); max-width:48rem; }}
    @media (max-width:720px) {{ .spread-rose .stamp-svg {{ width:140px; height:140px; top:1rem; right:1rem; }} }}
  </style>
  <svg class="stamp-svg" width="240" height="240" viewBox="0 0 240 240" aria-hidden="true">
    <circle cx="120" cy="120" r="110" fill="none" stroke="#C24A26" stroke-width="2"/>
    <circle cx="120" cy="120" r="92" fill="none" stroke="#C24A26" stroke-width="2"/>
    <defs><path id="ringpath" d="M 120,120 m -101,0 a 101,101 0 1,1 202,0 a 101,101 0 1,1 -202,0"/></defs>
    <text fill="#C24A26" font-family="Inter, sans-serif" font-weight="900"
          font-size="13" letter-spacing="3">
      <textPath href="#ringpath">ALERT · ALERT · ALERT · BOISE · ALERT · ALERT · ALERT · BOISE · </textPath>
    </text>
    <text x="120" y="135" text-anchor="middle" fill="#2B0A0A"
          font-family="Fraunces, serif" font-weight="900" font-size="42" letter-spacing="-1">{stamp_word}</text>
  </svg>
  <div class="spread-inner">
    <div class="topic-label" style="color:#C24A26;">{esc(story.get('topic_label',''))}</div>
    <div class="recurring-bit">
      <div class="label" style="color:#C24A26;">FRESH OFF THE PRESS</div>
      <div class="content">{body_paragraphs(story.get('recurring_bit_content',''))}</div>
    </div>
    <h2 class="headline">{esc(story.get('headline',''))}</h2>
    <div class="deck">{esc(story.get('deck',''))}</div>
    <div class="pull">{esc(story.get('pull_quote',''))}</div>
    <div class="body">{body_paragraphs(body_raw)}</div>
    {byline_html(name, section)}
    {source_html(story.get('source',''))}
  </div>
</section>
"""


def render_editorial(story: dict) -> str:
    name, section = _writer_info(story)
    # Split headline into two-word layers when possible
    headline = story.get("headline", "")
    words = headline.split()
    if len(words) >= 2:
        mid = len(words) // 2
        layer1 = " ".join(words[:mid])
        layer2 = " ".join(words[mid:])
    else:
        layer1 = headline
        layer2 = ""

    return f"""
<section class="spread spread-editorial">
  <style>
    .spread-editorial {{ background: radial-gradient(circle at 70% 30%, #3A2468 0%, #2B1A4E 70%);
        color:#F4EFE6; position:relative; overflow:hidden; }}
    .spread-editorial .stamp-yellow {{ font-family:'Inter',sans-serif; font-weight:900;
        text-transform:uppercase; letter-spacing:0.3em; color:#FFD93D; font-size:0.9rem; }}
    .spread-editorial .headline-stack {{ position:relative; margin-top:2rem; }}
    .spread-editorial .layer1 {{ font-family:'Fraunces',serif; font-weight:900; color:#F4EFE6;
        font-size: clamp(4.5rem, 12vw, 11rem); line-height:0.92; letter-spacing:-0.04em;
        position:relative; z-index:2; }}
    .spread-editorial .layer2 {{ font-family:'Fraunces',serif; font-weight:900; font-style:italic;
        color:#FF6B9D; opacity:0.55; font-size: clamp(4.5rem, 12vw, 11rem); line-height:0.92;
        letter-spacing:-0.04em; transform: translate(20px, -30px); z-index:1; position:relative; }}
    .spread-editorial .deck {{ font-family:'Fraunces',serif; font-style:italic; font-weight:400;
        font-size: clamp(1.3rem, 2vw, 1.8rem); margin-top:2rem; max-width:60ch; color:#e3d6ea; }}
    .spread-editorial .body {{ max-width:48rem; margin-top:2rem; font-size:1.1rem; line-height:1.75; }}
    .spread-editorial p {{ margin-bottom:1.2rem; }}
    .spread-editorial .pull {{ font-family:'Fraunces',serif; font-style:italic; font-weight:500;
        font-size: clamp(1.8rem, 3.5vw, 3.2rem); color:#FF6B9D; margin:3rem 0; max-width:34ch;
        line-height:1.2; }}
  </style>
  <div class="spread-inner">
    <div class="stamp-yellow">{esc(story.get('topic_label',''))}</div>
    <div class="headline-stack">
      <div class="layer1">{esc(layer1)}</div>
      <div class="layer2">{esc(layer2) if layer2 else '&nbsp;'}</div>
    </div>
    <div class="deck">{esc(story.get('deck',''))}</div>
    <div class="body">{body_paragraphs(story.get('body',''))}</div>
    <div class="pull">{esc(story.get('pull_quote',''))}</div>
    {byline_html(name, section)}
    {source_html(story.get('source',''))}
  </div>
</section>
"""


def render_broadside(story: dict) -> str:
    name, section = _writer_info(story)
    body = story.get("body", "")
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    first_letter = paras[0][0] if paras else ""
    first_rest = paras[0][1:] if paras else ""
    rest_paras = paras[1:] if len(paras) > 1 else []
    fleuron = ' <span style="color:#8B1E1E;">❦</span> '
    body_html = ""
    if paras:
        body_html = (
            f'<p><span class="dropcap">{esc(first_letter)}</span>'
            f'{_inline_md(esc(first_rest))}</p>'
        )
        for i, p in enumerate(rest_paras):
            if i > 0:
                body_html += f'<div style="text-align:center;margin:1rem 0;">{fleuron}</div>'
            body_html += f'<p>{_inline_md(esc(p))}</p>'

    # T1.2: Then|Now only renders when the AI supplied a pipe-delimited pair.
    # No pipe → suppress the whole block (better empty than "—").
    rbit_raw = (story.get("recurring_bit_content") or "").strip()
    thennow_html = ""
    if "|" in rbit_raw:
        then_half, now_half = rbit_raw.split("|", 1)
        then_half = then_half.strip()
        now_half = now_half.strip()
        if then_half and now_half:
            thennow_html = (
                '<div class="thennow">'
                f'<div><h4>Then</h4><div>{esc(then_half)}</div></div>'
                f'<div><h4>Now · 2026</h4><div>{esc(now_half)}</div></div>'
                '</div>'
            )

    return f"""
<section class="spread spread-broadside">
  <style>
    .spread-broadside {{ background:#EDE3CF; color:#2B1F0F; position:relative;
        background-image: radial-gradient(rgba(43,31,15,0.04) 1px, transparent 1px);
        background-size: 3px 3px; }}
    .spread-broadside .frame {{ border:4px double #2B1F0F; padding: clamp(1.5rem, 4vw, 3rem);
        position:relative; }}
    .spread-broadside .stamp-s {{ font-family:'Inter',sans-serif; font-weight:900;
        text-transform:uppercase; letter-spacing:0.35em; color:#8B1E1E; font-size:0.85rem;
        text-align:center; margin-bottom:1.5rem; }}
    .spread-broadside .headline-top {{ font-family:'Fraunces',serif; font-weight:900;
        font-size: clamp(3rem, 7vw, 5.5rem); line-height:0.95; text-align:center;
        letter-spacing:-0.02em; }}
    .spread-broadside .headline-mid {{ font-family:'Fraunces',serif; font-style:italic;
        font-weight:400; font-size: clamp(1.8rem, 4vw, 3rem); text-align:center; margin:0.5rem 0; }}
    .spread-broadside .headline-bot {{ font-family:'Fraunces',serif; font-weight:700;
        font-variant: small-caps; letter-spacing:0.1em; font-size: clamp(1.2rem, 2vw, 1.6rem);
        text-align:center; color:#8B1E1E; }}
    .spread-broadside .dropcap {{ font-family:'Fraunces',serif; font-weight:900; color:#8B1E1E;
        float:left; font-size: clamp(4rem, 8vw, 6rem); line-height:0.85;
        padding:0.3rem 0.8rem 0 0; }}
    .spread-broadside .body {{ margin-top:2rem; column-count:2; column-gap:3rem; text-align:justify;
        hyphens:auto; }}
    .spread-broadside p {{ margin-bottom:1.1rem; break-inside:avoid; }}
    .spread-broadside .thennow {{ display:grid; grid-template-columns:1fr 1fr; gap:2rem;
        margin-top:2rem; border-top:2px solid #8B1E1E; padding-top:1.25rem; }}
    .spread-broadside .thennow h4 {{ font-family:'Inter',sans-serif; font-weight:900;
        text-transform:uppercase; letter-spacing:0.25em; color:#8B1E1E; font-size:0.85rem;
        margin-bottom:0.5rem; }}
    .spread-broadside .editor-colophon {{ font-family:'Fraunces',serif; font-style:italic;
        font-weight:400; font-size:0.95rem; color:#6A4F28; text-align:center;
        margin-top:2rem; padding-top:1.25rem; border-top:1px dashed rgba(43,31,15,0.35);
        letter-spacing:0.02em; }}
    .spread-broadside .editor-colophon strong {{ font-weight:700; color:#8B1E1E; font-style:normal;
        letter-spacing:0.12em; text-transform:uppercase; font-size:0.72rem;
        font-family:'Inter',sans-serif; }}
    @media (max-width:820px) {{ .spread-broadside .body {{ column-count:1; }} }}
  </style>
  <div class="spread-inner">
    <div class="frame">
      <div class="stamp-s">Extra! · Broadside · {esc(story.get('topic_label',''))}</div>
      <div class="headline-top">{esc(story.get('headline',''))}</div>
      <div class="headline-mid">{esc(story.get('deck',''))}</div>
      <div class="headline-bot">— A dispatch from the archives —</div>
      <div class="body">{body_html}</div>
      {thennow_html}
      {byline_html(name, section)}
      {source_html(story.get('source',''))}
      <div class="editor-colophon">— Margaret Halstead, <strong>Editor-in-Chief</strong></div>
    </div>
  </div>
</section>
"""


def render_todays_edition(story: dict) -> str:
    """Maggie Halstead's editor's opener. Positioned first in every issue.
    A quieter, letter-from-the-editor panel above the hero — stamped "Today's
    Edition", signed "— M.H." / "Margaret Halstead, Editor". Half-height
    (min-height auto) so it reads as a preamble, not a headline spread.
    """
    body = story.get("body", "")
    body_paras = body_paragraphs(body)
    dateline = story.get("context_line", "")
    closer = story.get("pull_quote", "")
    return f"""
<section class="spread spread-todays-edition">
  <style>
    .spread-todays-edition {{ background:#F7F2E8; color:#1A1A1A;
        min-height:auto; padding: clamp(2.5rem,6vw,5rem) clamp(1.5rem,6vw,6rem);
        border-bottom: 2px solid rgba(139,30,30,0.12); }}
    .spread-todays-edition .panel {{ max-width: 62ch; margin: 0 auto;
        border-top: 1px solid #8B1E1E; border-bottom: 1px solid #8B1E1E;
        padding: 2.5rem 0 1.75rem; position:relative; }}
    .spread-todays-edition .stamp {{ font-family:'Inter',sans-serif; font-weight:900;
        text-transform:uppercase; letter-spacing:0.35em; color:#8B1E1E; font-size:0.78rem;
        text-align:center; margin-bottom:0.55rem; }}
    .spread-todays-edition .dateline {{ font-family:'Inter',sans-serif; font-weight:700;
        text-transform:uppercase; letter-spacing:0.22em; color:#6A6A6A; font-size:0.74rem;
        text-align:center; margin-bottom:2rem; }}
    .spread-todays-edition .body {{ font-family:'Fraunces',serif; font-weight:400;
        font-size: clamp(1.08rem, 1.6vw, 1.28rem); line-height:1.6; }}
    .spread-todays-edition .body p {{ margin-bottom:1.1rem; }}
    .spread-todays-edition .body strong {{ font-weight:700; color:#8B1E1E; }}
    .spread-todays-edition .body em {{ font-style:italic; color:#2B1F0F; }}
    .spread-todays-edition .closer {{ font-family:'Fraunces',serif; font-style:italic;
        font-weight:400; font-size: clamp(1.2rem, 1.9vw, 1.5rem); line-height:1.4;
        text-align:center; margin:1.75rem 0 1.25rem; color:#2B1F0F;
        border-top: 1px solid rgba(139,30,30,0.2); padding-top: 1.5rem; }}
    .spread-todays-edition .sig {{ font-family:'Fraunces',serif; font-style:italic;
        font-weight:700; font-size: 1.35rem; text-align:right; color:#8B1E1E;
        margin-top:1rem; letter-spacing:0.02em; }}
    .spread-todays-edition .sig-meta {{ font-family:'Inter',sans-serif; font-weight:700;
        text-transform:uppercase; letter-spacing:0.22em; color:#6A6A6A; font-size:0.72rem;
        text-align:right; margin-top:0.35rem; }}
  </style>
  <div class="spread-inner">
    <div class="panel">
      <div class="stamp">Today's Edition</div>
      {f'<div class="dateline">{esc(dateline)}</div>' if dateline else ''}
      <div class="body">{body_paras}</div>
      {f'<div class="closer">{esc(closer)}</div>' if closer else ''}
      <div class="sig">— M.H.</div>
      <div class="sig-meta">Margaret Halstead, Editor</div>
    </div>
  </div>
</section>
"""


# ────────────────────────────────────────────────────────────
# Dispatcher
# ────────────────────────────────────────────────────────────
SPREAD_RENDERERS = {
    "todays_edition": render_todays_edition,
    "hero": render_hero,
    "big_stat": render_big_stat,
    "academic": render_academic,
    "midnight": render_midnight,
    "retro_weather": render_retro_weather,
    "broadsheet": render_broadsheet,
    "terminal": render_terminal,
    "rose_stamp": render_rose_stamp,
    "editorial": render_editorial,
    "broadside": render_broadside,
}


def render_spread(story: dict) -> str:
    fn = SPREAD_RENDERERS.get(story.get("spread_type", "hero"), render_hero)
    return fn(story)


# ────────────────────────────────────────────────────────────
# Page wrapper — masthead, footer, issue
# ────────────────────────────────────────────────────────────
def masthead(date: datetime, issue_label: str | None = None) -> str:
    date_line = date.strftime("%A · %B %d, %Y")
    issue_stamp = (
        f'<div class="issue-stamp">{esc(issue_label)}</div>' if issue_label else ""
    )
    return f"""
<header class="masthead">
  <style>
    .masthead {{ background:#0B1E33; color:#F4EFE6; padding: clamp(2.25rem,4vw,4.25rem)
        clamp(1.5rem,6vw,6rem); border-bottom:3px solid #C24A26; text-align:center;
        position:relative; overflow:hidden; }}
    .masthead::before {{ content:""; position:absolute; inset:0; opacity:0.05; pointer-events:none;
        background:repeating-linear-gradient(0deg, transparent 0 17px, #6FA8D6 17px 18px); }}
    .masthead .dateline {{ font-family:'JetBrains Mono',ui-monospace,monospace; font-weight:700;
        letter-spacing:0.32em; text-transform:uppercase; color:#6FA8D6; font-size:0.74rem;
        position:relative; }}
    .masthead .title {{ font-family:'Fraunces',serif; font-weight:900;
        font-size: clamp(2.6rem, 9vw, 7.5rem); line-height:0.92; margin-top:0.85rem;
        letter-spacing:-0.035em; position:relative; }}
    .masthead .title .accent {{ color:#C24A26; }}
    .masthead .pulse-line {{ display:block; width:min(440px,82%); height:auto; margin:0.55rem auto 0;
        position:relative; }}
    .masthead .tagline {{ font-family:'Fraunces',serif; font-style:italic; font-weight:400;
        color:#D9CBB3; font-size:clamp(0.98rem,1.7vw,1.2rem); max-width:48ch; margin:1.35rem auto 0;
        line-height:1.5; position:relative; }}
    .masthead .issue-stamp {{ font-family:'JetBrains Mono',ui-monospace,monospace; font-weight:700;
        letter-spacing:0.3em; text-transform:uppercase; color:#E0A23C; font-size:0.7rem;
        margin-top:1.35rem; padding:0.4rem 1.05rem; border:1px solid rgba(224,162,60,0.5);
        display:inline-block; position:relative; }}
  </style>
  <div class="dateline">{date_line}</div>
  <h1 class="title">The Boise <span class="accent">Pulse</span></h1>
  <svg class="pulse-line" viewBox="0 0 600 36" fill="none" aria-hidden="true">
    <polyline points="0,18 250,18 262,18 272,10 283,26 293,3 303,31 313,18 326,18 600,18"
      stroke="#C24A26" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
  <div class="tagline">The Treasure Valley, three mornings a week — written for the people who live here.</div>
  {issue_stamp}
</header>
"""


def footer(date: datetime) -> str:
    from .personas import PERSONAS

    writers = " · ".join(f"{p['name']} ({p['section']})" for p in PERSONAS.values())
    return f"""
<footer class="footer">
  <style>
    .footer {{ background:#0B1E33; color:#F4EFE6; padding: clamp(2rem,4vw,4rem)
        clamp(1.5rem,6vw,6rem); text-align:center; border-top:3px solid #C24A26; }}
    .footer .title {{ font-family:'Fraunces',serif; font-style:italic; font-weight:400;
        font-size: clamp(1.8rem, 4vw, 3rem); }}
    .footer .staff {{ font-family:'Inter',sans-serif; font-size:0.85rem; color:#9A9A9A;
        margin-top:1.5rem; max-width:80ch; margin-left:auto; margin-right:auto;
        line-height:1.8; letter-spacing:0.05em; }}
    .footer .colophon {{ font-family:'Inter',sans-serif; font-size:0.72rem; color:#6A6A6A;
        margin-top:2rem; text-transform:uppercase; letter-spacing:0.3em; }}
  </style>
  <div class="title">The Boise Pulse</div>
  <div class="staff">Staff writers: {esc(writers)}</div>
  <div class="colophon">{date.strftime("%Y-%m-%d")} · built in Boise · © The Boise Pulse</div>
</footer>
"""


def render_page(date: datetime, body_html: str, issue_label: str | None = None, vitals: dict | None = None) -> str:
    date_iso = date.strftime("%Y-%m-%d")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Boise Pulse — {date_iso}</title>
<meta name="description" content="An editorial magazine for Boise, Idaho — curated Tue / Thu / Fri.">
{GOOGLE_FONTS}
<style>{BASE_CSS}</style>
</head>
<body>
{masthead(date, issue_label=issue_label)}
{render_vitals(vitals)}
<main>
{body_html}
</main>
{footer(date)}
</body>
</html>
"""


def render_issue(date: datetime, stories: list[dict], issue: dict | None = None, vitals: dict | None = None) -> str:
    body = "\n".join(render_spread(s) for s in stories)
    label = (issue or {}).get("masthead_label")
    return render_page(date, body, issue_label=label, vitals=vitals)


# ────────────────────────────────────────────────────────────
# Archive index page
# ────────────────────────────────────────────────────────────
def render_archive_index(date: datetime, issues: list[dict]) -> str:
    """issues: list of {date: 'YYYY-MM-DD', lead_headline: str, filename: str} — newest first."""
    cards = ""
    for i, it in enumerate(issues):
        featured = i == 0
        card_style = (
            "grid-column: span 2;" if featured else ""
        )
        cards += f"""
        <a class="card{' featured' if featured else ''}" href="{esc(it['filename'])}" style="{card_style}">
          <div class="card-date">{esc(it['date'])}</div>
          <div class="card-headline">{esc(it['lead_headline'])}</div>
          <div class="card-cta">Read →</div>
        </a>
        """

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Boise Pulse — The Archive</title>
{GOOGLE_FONTS}
<style>{BASE_CSS}
.archive {{ background:#F4EFE6; min-height:100vh; padding: clamp(3rem,6vw,6rem) clamp(1.5rem,6vw,6rem); }}
.archive h2 {{ font-family:'Fraunces',serif; font-weight:900;
    font-size: clamp(3rem, 9vw, 8rem); color:#1A1A1A; letter-spacing:-0.03em; line-height:0.95; }}
.archive-grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem; margin-top:3rem; }}
.card {{ background:#FFFFFF; color:#1A1A1A; padding:1.75rem; text-decoration:none;
    border-top:4px solid #C24A26; transition: transform 0.2s, box-shadow 0.2s;
    display:flex; flex-direction:column; gap:0.75rem; min-height:220px; }}
.card:hover {{ transform: translateY(-4px); box-shadow: 0 14px 34px rgba(0,0,0,0.1); }}
.card.featured {{ min-height:300px; background:#0B1E33; color:#F4EFE6; border-top-color:#E0A23C; }}
.card-date {{ font-family:'Inter',sans-serif; font-weight:900; text-transform:uppercase;
    letter-spacing:0.25em; font-size:0.78rem; color:#C24A26; }}
.card.featured .card-date {{ color:#E0A23C; }}
.card-headline {{ font-family:'Fraunces',serif; font-weight:900;
    font-size: clamp(1.5rem,2.4vw,2.2rem); line-height:1.1; flex:1; }}
.card-cta {{ font-family:'Inter',sans-serif; font-weight:700; letter-spacing:0.15em;
    text-transform:uppercase; font-size:0.8rem; color:#C24A26; }}
.card.featured .card-cta {{ color:#E0A23C; }}
</style>
</head>
<body>
{masthead(date)}
<section class="archive">
  <div class="archive-grid">{cards or '<div style="font-family:Fraunces;font-style:italic;">No issues yet.</div>'}</div>
</section>
{footer(date)}
</body>
</html>
""" 

# ────────────────────────────────────────────────────────────
# The Vitals — standing outdoor-decision dashboard (under masthead)
# ────────────────────────────────────────────────────────────
def render_vitals(vitals: dict | None = None) -> str:
    """Scannable 6-cell outdoor dashboard + advisory. Empty/None -> nothing."""
    if not vitals or not vitals.get("cells"):
        return ""
    cell_colors = {
        "good":    ("#16301F", "#5E9E6B", "#C6E7CE"),
        "neutral": ("#10283F", "#6FA8D6", "#C3DAEF"),
        "caution": ("#382B12", "#E0A23C", "#F1DBAB"),
        "alert":   ("#3A1A10", "#C24A26", "#F0B9A3"),
    }
    cells_html = ""
    for c in vitals.get("cells", []):
        bg, acc, txt = cell_colors.get(c.get("status", "neutral"), cell_colors["neutral"])
        cells_html += (
            f'<div class="v-cell" style="background:{bg};border-left:3px solid {acc};">'
            f'<div class="v-top">'
            f'<span class="v-ic">{esc(c.get("icon",""))}</span>'
            f'<span class="v-lab" style="color:{txt};">{esc(c.get("label",""))}</span>'
            f'<span class="v-dot" style="background:{acc};"></span>'
            f'</div>'
            f'<div class="v-main">{esc(c.get("main","—"))}</div>'
            f'<div class="v-sub" style="color:{txt};">{esc(c.get("sub",""))}</div>'
            f'</div>'
        )
    adv = vitals.get("advisory") or {}
    adv_html = ""
    if adv.get("text"):
        adv_styles = {
            "info":    ("#10283F", "#6FA8D6", "#D6E8F6", "ⓘ"),
            "caution": ("#382B12", "#E0A23C", "#F3E2BC", "▲"),
            "alert":   ("#3A1A10", "#C24A26", "#F4C9B8", "⚠"),
        }
        ab, abrd, atx, ai = adv_styles.get(adv.get("level", "info"), adv_styles["info"])
        adv_html = (
            f'<div class="v-advisory" style="background:{ab};border-top:1px solid {abrd};">'
            f'<span class="v-adv-ic" style="color:{abrd};">{ai}</span>'
            f'<span class="v-adv-tx" style="color:{atx};">{esc(adv.get("text",""))}</span>'
            f'</div>'
        )
    style = """<style>
.vitals { background:#0B1E33; border-bottom:3px solid #C24A26; }
.vitals .v-head { display:flex; align-items:center; justify-content:space-between;
    gap:1rem; padding: clamp(1.1rem,2.2vw,1.6rem) clamp(1.25rem,5vw,4rem) 0.85rem; }
.vitals .v-head-l { display:flex; align-items:center; gap:0.7rem; }
.vitals .v-heart { color:#C24A26; font-size:1.35rem; line-height:1; }
.vitals .v-title { font-family:'JetBrains Mono',ui-monospace,monospace; font-weight:700;
    text-transform:uppercase; letter-spacing:0.26em; font-size:0.82rem; color:#E0A23C; }
.vitals .v-tag { font-family:'Fraunces',serif; font-style:italic; color:#9FBEDA;
    font-size:0.92rem; margin-top:0.15rem; }
.vitals .v-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr));
    gap:0.7rem; padding: 0 clamp(1.25rem,5vw,4rem) clamp(1.1rem,2.2vw,1.5rem); }
.vitals .v-cell { padding:0.85rem 1rem 0.95rem; }
.vitals .v-top { display:flex; align-items:center; gap:0.5rem; margin-bottom:0.45rem; }
.vitals .v-ic { font-size:1.05rem; line-height:1; }
.vitals .v-lab { font-family:'JetBrains Mono',ui-monospace,monospace; font-weight:700;
    text-transform:uppercase; letter-spacing:0.12em; font-size:0.72rem; opacity:0.92; }
.vitals .v-dot { width:9px; height:9px; border-radius:50%; margin-left:auto; flex-shrink:0; }
.vitals .v-main { font-family:'Fraunces',serif; font-weight:700; color:#F4EFE6;
    font-size:1.45rem; line-height:1.05; letter-spacing:-0.01em; }
.vitals .v-sub { font-family:'JetBrains Mono',ui-monospace,monospace; font-size:0.74rem;
    line-height:1.35; margin-top:0.3rem; opacity:0.92; }
.vitals .v-advisory { display:flex; gap:0.7rem; align-items:flex-start;
    padding: 0.9rem clamp(1.25rem,5vw,4rem); }
.vitals .v-adv-ic { font-size:1.05rem; font-weight:700; line-height:1.3; flex-shrink:0; }
.vitals .v-adv-tx { font-family:'Fraunces',serif; font-style:italic; font-size:1rem; line-height:1.5; }
@media (max-width:520px){ .vitals .v-grid { grid-template-columns:repeat(2,1fr); } }
</style>"""
    return (
        '<section class="vitals">' + style +
        '<div class="v-head"><div class="v-head-l">'
        '<span class="v-heart">♥</span>'
        '<div><div class="v-title">The Vitals</div>'
        '<div class="v-tag">What\'s actually happening outside</div></div>'
        '</div></div>'
        f'<div class="v-grid">{cells_html}</div>'
        f'{adv_html}'
        '</section>'
    )
