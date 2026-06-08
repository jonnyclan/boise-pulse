# The Boise Pulse — Build Spec

**Status:** spec for a fresh build. Reference `src/personas.py` and `DESIGN.md` for details.

---

## 1. Vision

A daily editorial magazine for Boise, Idaho — autonomously written, automatically published, designed to feel like a premium print publication on the web.

The newsletter's differentiator is **tonal authenticity through character**. Instead of one anonymous AI voice, it's a newsroom of 8 fully developed writer personas, each with a name, backstory, voice rules, catchphrases, and recurring bits. Readers come back for the writers as much as for the news.

## 2. Core Value Proposition

Every morning at 7am MT, an automated pipeline:
1. **Surveys what Boise is actually talking about** across the web — local news, Reddit r/Boise hot posts, YouTube trending Boise videos, NWS weather, Wikipedia "on this day"
2. **Curates the 10 most relevant stories** for a broad Boise reader (skipping partisan political opinion)
3. **Rewrites each story in the voice of the appropriate writer persona** with full editorial voice, pull quotes, and recurring bits
4. **Renders it as a typography-driven HTML magazine** with 10 visually distinct spreads
5. **Publishes it to a live URL** via GitHub Actions → Vercel

The reader's experience: "This newsletter always seems to know what's happening in Boise before I do, and it's written by people I like reading."

## 3. Target Audience

Broad Boise / Treasure Valley residents, ages roughly 28–65.
- Mix of natives and transplants
- Different sections appeal to different subsets; the whole issue has something for everyone
- Audience tone: smart adults who want substance + personality, not clickbait

## 4. Brand

- **Name:** The Boise Pulse
- **Tagline:** *Curated daily from the Treasure Valley's web · Rewritten for the people who live here.*
- **Core identity:** Editorial magazine aesthetic, print-inspired, typography-first
- **Publishing URL:** `boise-morning-edition.vercel.app` (Vercel subdomain, custom domain later)

## 5. The Writers (See `src/personas.py` for full bibles)

| Key | Writer | Beat | Section |
|---|---|---|---|
| `sports` | Kelsey Rowe, 29 | Sports | The Bench |
| `weather` | Pete Caldwell, 58 | Weather | The Forecast |
| `real_estate` | Sal Merritt, 54 | Real Estate | The Market |
| `history` | Del Haas, 67 | History & Lore | The Archives |
| `food` | Nina Castillo, 37 | Food & Drink | The Table |
| `arts` | Dex Dexter, 44 | Music & Arts | The Scene |
| `trending` | Jess Park, 26 | Trending | Fresh Off the Press |
| `editorial` | Dani Breck, 47 | Editorial | The Way I See It |

Each writer has: name + age + backstory + voice rules + catchphrase + recurring bit + "never writes" rules + signature move + "their Boise" (specific neighborhood/places). The full `prompt_voice` string for each is **baked into the AI curation prompt** so every story sounds like that writer consistently.

## 6. Section Structure & Recurring Bits

Every issue contains 10 spreads. Topic distribution is AI-curated each day based on the news, but **weather must always appear** (it's Pete's daily column).

**Recurring bits (required elements):**
- **"Mood of the Sky"** — Pete's weather column always opens with one-word/phrase mood
- **"Fresh Off the Press"** — Jess's trending column always opens with a 3-bullet box showing YouTube trending + Reddit top + one other signal
- **"The Comps"** — Sal's real estate stories end with a 5-year comparison sidebar
- **"The Lede"** — Kelsey's sports column opens with one surgical sentence
- **"Then vs. Now"** — Del's history pieces end with one sharp historical comparison
- **"Nina's Table"** — Nina's food stories close with a one-line verdict
- **"Dex's Drop"** — Dex's music/arts pieces open with a quote (often a hip-hop lyric)
- **"Dani's Correction Corner"** — Dani's editorial sometimes opens with a cheerful self-correction of a previous column

## 7. Visual Design System

**Typography-only aesthetic** — NO photos, NO AI illustrations. Everything is typography, color, CSS gradients, SVG, CSS-art. Inspired by New Yorker covers and minimalist zines.

- **Display font:** Fraunces (variable, optical-size)
- **Body font:** Inter (weights 300, 400, 600, 700, 900)
- **Mono font:** JetBrains Mono (for terminal spread)
- All from Google Fonts

**10 distinct spread types** — see `DESIGN.md` for each:
1. `hero` — cream, massive Fraunces headline, two-column, rust pull-quote
2. `midnight` — dark bg, glowing gold text, starfield CSS
3. `rose_stamp` — pink, circular ALERT stamp SVG
4. `terminal` — black, green monospace, blinking cursor
5. `academic` — ivory, giant drop-cap, scholarly justified text
6. `big_stat` — white, one enormous number dominates
7. `broadsheet` — dark navy, sports-section reversed type
8. `retro_weather` — blue gradient, 80s TV broadcast aesthetic
9. `editorial` — deep purple, expressive layered typography
10. `broadside` — aged paper, decorative border, old newspaper

**Rules:**
- Minimum body font size: 20px. Headlines go 6vw–14vw.
- Every spread is `min-height: 100vh`
- Self-contained HTML: inline `<style>` block + Google Fonts link only
- Mobile responsive: spreads collapse gracefully below 720px

## 8. Data Sources

### Always-on (no auth required)
- **Google News RSS** — 6 queries (general, sports, weather, arts, real estate, tech) × 6 stories = ~36 headlines
- **NWS Weather API** — Boise forecast, next 3 days
- **Wikipedia On-This-Day** — 5 historical events for today's date

### Keyed (with free-tier fallbacks)
- **Reddit r/Boise** — OAuth if `REDDIT_CLIENT_ID`+`REDDIT_CLIENT_SECRET` set, else unauthenticated `.json` endpoint. Top 12 hot posts.
- **YouTube Data API v3** — requires `YOUTUBE_API_KEY`. Trending Boise videos from last 48 hours by view count.

All fetchers in `src/data_sources.py` return safe defaults on failure (never raise).

## 9. AI Engine

**Two-phase architecture:**

**Phase 1: Curation** (one small API call)
- Input: compressed data (titles + short blurbs, ~5-7k chars)
- Prompt includes: date, priorities, voice rules for each writer, JSON schema
- Output: JSON array of exactly 10 story objects with editorial content written in each writer's voice
- Model priority: Claude Sonnet 4.6 (SDK) → Claude CLI (in session) → Gemini 2.0 Flash

**Phase 2: Render** (pure Python, no API)
- Input: the 10-story JSON
- Output: self-contained HTML file using the 10 spread templates
- Guarantees consistent visual output regardless of AI

This split is **critical**: it avoids large AI response streams, keeps each call fast, and makes the HTML quality independent of AI randomness.

### Story JSON Schema

```json
{
  "number": 1,
  "writer_key": "weather",
  "spread_type": "retro_weather",
  "topic_label": "WEATHER",
  "headline": "10 words max, punchy",
  "deck": "One-sentence subtitle.",
  "body": "Paragraph 1 (80-120 words)\n\nParagraph 2 (80-120 words)\n\nParagraph 3 (80-120 words)",
  "pull_quote": "A memorable sentence from the piece.",
  "stat": "58°F",
  "source": "NWS Boise · April 17",
  "recurring_bit_content": "MOOD OF THE SKY: Dramatic."
}
```

## 10. Technical Architecture

### File/Directory Structure

```
/
├── SPEC.md
├── DESIGN.md
├── generate_magazine.py             # lean orchestrator (~80 lines)
├── requirements.txt
├── .env.example
├── vercel.json
├── src/
│   ├── __init__.py
│   ├── personas.py                  # 8 writer bibles + prompt_voice strings
│   ├── data_sources.py
│   ├── ai_engine.py
│   └── html_renderer.py             # 10 spread templates + page wrapper
├── magazines/
│   ├── index.html
│   └── YYYY-MM-DD.html
└── .github/
    └── workflows/
        └── morning-edition.yml      # daily cron at 14:00 UTC (7am MT)
```

### Data Flow

```
[cron 7am MT] → fetch all sources → build compressed prompt
             → AI curate (returns JSON) → validate + fill defaults
             → render HTML via Python templates → write magazines/YYYY-MM-DD.html
             → regenerate magazines/index.html → git commit + push
             → Vercel webhook → new deploy live in ~30s
```

### Error Handling — Graceful Degrade

Critical rule: **never miss a morning.** If any data source fails:
- Flag it in the payload
- Continue with whatever data succeeded
- Issue publishes anyway

Only abort if AI curation fails all three backends. In that case, serve yesterday's issue at the root URL.

## 11. Editorial/Legal Stance — Transformative Rewrite + Citation

Every story is transformatively rewritten in a writer's voice, not a summary of the source. Facts are cited. Phrasing is ours. Every story has a `source` field displayed on the spread.

## 12. Deployment

- **GitHub Actions:** `0 14 * * *` (7:00 AM MT) — checkout → Python → install → run → commit + push
- **Vercel:** auto-deploys on push to main, pure static hosting
- **Secrets required:** `ANTHROPIC_API_KEY`, `YOUTUBE_API_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`

## 13. Build Order (for a fresh session)

1. Read SPEC.md + DESIGN.md + src/personas.py
2. Build src/data_sources.py
3. Build src/ai_engine.py
4. Build src/html_renderer.py — base first, then spreads one at a time
5. Build generate_magazine.py
6. Build archive index generator
7. Build config files: requirements.txt, .env.example, vercel.json
8. Build .github/workflows/morning-edition.yml
9. Test locally end-to-end
10. Commit, push, verify Vercel deploys

## 14. What Done Looks Like

- `python3 generate_magazine.py` → `magazines/YYYY-MM-DD.html`
- 10 visually distinct spreads, all 8 writer voices
- GitHub Actions runs at 7am MT, Vercel deploys it
- `boise-morning-edition.vercel.app` always shows today's issue
- Survives one or two source failures per day without missing an issue
