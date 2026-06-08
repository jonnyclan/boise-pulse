# The Boise Pulse — Design Briefs

Visual specifications for the 10 spread types. Typography, CSS color, gradients, and SVG only. No photos, no AI illustrations.

---

## Global Design Tokens

### Typography
- **Display:** Fraunces (variable, optical size 9–144, weight 200–900)
- **Body:** Inter (weights 300, 400, 600, 700, 900)
- **Mono:** JetBrains Mono (terminal spread only)

### Minimums
- Body copy: never below **20px**
- Line length: 55–75 chars/line on desktop
- Line height: 1.5 body, 0.95–1.1 display

### Headlines
- Range: `clamp(3rem, 6vw, 14vw)` depending on spread
- Letter-spacing: tight (`-0.02em` to `-0.04em`)
- Display weight: 900 hero, 300–400 italic subtitles

### Rules
- Every spread: `min-height: 100vh`
- Every spread: self-contained (Google Fonts only)
- Mobile below 720px: padding shrinks, columns stack, headlines scale via clamp

---

## 1. `hero` — The Cover Spread
**Feel:** New Yorker cover. Confident, restrained, premium.
**Palette:** Background `#F4EFE6` cream · Text `#1A1A1A` · Accent `#C0392B` rust (pull quote + rules only)
**Layout:**
- Two-column desktop (body left, pull quote right)
- Massive Fraunces headline fills 60–80% viewport width
- Thin 1px rust rule under headline
- Deck in italic Fraunces
- Pull quote Fraunces italic, rust, 3px left border
- Rust source-line at bottom
**Typography:** Byline Inter 900 0.22em UC 0.9rem · Headline Fraunces 900 clamp(3rem,9vw,9rem) lh0.95 · Deck Fraunces italic 400 clamp(1.4rem,2.4vw,2rem) · Pull Fraunces italic 500 clamp(1.8rem,3vw,2.8rem)
**Best for:** Lead story, spread #1.

---

## 2. `midnight` — The Dark Glow Spread
**Feel:** Late-night editorial, expensive, contemplative.
**Palette:** Background `#0B1020` → `#1A2040` radial · Text `#F5E6A8` warm gold · Accent `#FFD978` bright gold
**Layout:**
- Single-column centered, max 60rem
- CSS starfield: 40–60 absolute `<span>` dots, `animation: twinkle 4s infinite` staggered
- Headline centered, Fraunces 900 gold, text-shadow glow `0 0 30px rgba(255,217,120,0.25)`
- Pull quote centered, Fraunces italic, flanked by em-dashes
**Typography:** Headline Fraunces 900 italic clamp(3rem,7vw,7rem) · Body Inter 400 20–22px 1.8lh justified · Pull Fraunces italic 400 2.2rem centered
**Best for:** Del's history, Dani's somber editorials, Dex's reflective pieces.

---

## 3. `rose_stamp` — The Alert Stamp Spread
**Feel:** Punchy, viral, "BREAKING" energy but tasteful. Pink risograph meets zine.
**Palette:** Background `#F8D3D0` rose · Text `#2B0A0A` burgundy · Accent `#C0392B` rust
**Layout:**
- Absolute SVG circular stamp top-right — 200–280px, rotated 12°, two concentric circles, text on SVG path "ALERT · ALERT · ALERT · BOISE ·" around ring, center word "HOT"/"VIRAL"/"NOW" in Fraunces 900
- Headline stacked, left-aligned, clamp(3rem,8vw,7.5rem)
- Pull quote Fraunces italic, 6px rust left border
**Typography:** Headline Fraunces 900 tight kerning · Stamp text Inter 900 0.15em UC · Body Inter 400 20–22px
**Best for:** Jess's trending/Reddit/viral pieces.

---

## 4. `terminal` — The Tech Terminal Spread
**Feel:** Programmer's terminal at 2am. Retro CRT.
**Palette:** Background `#050807` near-black · Text `#39FF6A` green phosphor · Dim elements at 60% opacity
**Layout:**
- Terminal chrome: three macOS dots + title "boise.term — zsh"
- All text JetBrains Mono
- Prompt: `$ boise --today` then output
- Headline prefixed `>` with blinking cursor `▋` `animation: blink 1s infinite`
- CRT scanlines: `repeating-linear-gradient` overlay 3% opacity
- Pull quote as `/* ... */` block comment, dimmer green
**Typography:** Headline JetBrains Mono 700 2.5–4rem · Body JetBrains Mono 400 20px 1.7lh
**Best for:** Tech/startup stories.

---

## 5. `academic` — The Scholarly Spread
**Feel:** University press. Old Penguin paperback.
**Palette:** Background `#FAF6EE` ivory · Text `#1F1A12` dark brown · Accent `#6B4E2B` walnut (drop cap + rules)
**Layout:**
- Giant Fraunces drop-cap — 8–10 lines tall, floated left, walnut
- Body justified, Inter 400, hyphens enabled
- Header: "VOLUME I · ISSUE N · {DATE}" small-caps
- Pull quote centered Fraunces italic walnut, flanked by § symbols
- "THEN vs. NOW" comparison box at bottom (Del's recurring bit)
**Typography:** Drop cap Fraunces 900 clamp(6rem,12vw,11rem) walnut · Headline Fraunces 900 4–6rem · Body Inter 400 20–22px justified 1.8lh
**Best for:** Del's history, Dani's analytical editorials.

---

## 6. `big_stat` — The Enormous Number Spread
**Feel:** Infographic hero. One number owns the page.
**Palette:** Background `#FFFFFF` · Text `#0E0E10` · Accent `#C0392B` rust (stat only)
**Layout:**
- ONE massive stat: Fraunces 200 italic rust, `clamp(10rem,32vw,28rem)`, lh 0.85 — utterly dominant
- Legend below stat (e.g. "Median home price, Ada County, April 2026")
- Headline below in Fraunces 900, much smaller
- Body in narrow column, max 32rem
**Typography:** The Number Fraunces 200 italic rust clamp(10rem,32vw,28rem) · Headline Fraunces 900 clamp(2.5rem,5vw,5rem) · Body Inter 400 20–22px
**Best for:** Sal's real estate stats, sports scores, any dominant quantitative anchor.

---

## 7. `broadsheet` — The Sports Page Spread
**Feel:** Classic sports section above the fold. Ink, grit, headline shouting.
**Palette:** Background `#0A1428` dark navy · Text `#F4EFE6` cream · Accent `#FFB020` stadium amber
**Layout:**
- "THE BENCH" section stamp Inter 900 amber 0.3em tracking
- Headline Fraunces 900 cream MASSIVE `clamp(4rem,12vw,14vw)` lh 0.92
- Three-column body, 1px amber column rules at 40% opacity
- "THE LEDE" callout: thick amber left border, single surgical sentence
- Pull quote centered between columns, Fraunces italic amber
**Typography:** Stamp Inter 900 0.85rem 0.3em tracking · Headline Fraunces 900 clamp(4rem,12vw,14rem) · Body Inter 400 19–20px 1.7lh
**Best for:** Kelsey's sports column exclusively.

---

## 8. `retro_weather` — The 80s TV Broadcast Spread
**Feel:** Pete Caldwell's 1987 weather segment. Chroma key blue, chunky type.
**Palette:** Background `linear-gradient(135deg, #4A90E2, #1E4D8C)` · Text `#FFFFFF` · Accent `#FFD93D` broadcast yellow + `#FF6B6B` temp red
**Layout:**
- "MOOD OF THE SKY" banner + one-word mood in Fraunces italic 900
- Temperature as huge number: Fraunces 900 white with yellow outline-shadow, `clamp(8rem,20vw,18rem)`
- Flat geometric SVG sun/cloud/rain icons in corners, 60–100px
- Body with subtle yellow left border
- 3-day forecast strip at bottom: bordered cells, temperature + one-word condition per day
- Faint scanlines overlay for CRT-TV effect
**Typography:** Temperature Fraunces 900 clamp(8rem,20vw,18rem) · Headline Fraunces 900 clamp(3rem,6vw,6rem) · Body Inter 400 20–22px white 95%
**Best for:** Pete's weather column exclusively. Mandatory daily.

---

## 9. `editorial` — The Expressive Typography Spread
**Feel:** Opinionated, loud, design-forward. Type as art.
**Palette:** Background `#2B1A4E` deep aubergine + radial highlight · Text `#F4EFE6` cream · Accent `#FF6B9D` hot pink + `#FFD93D` yellow
**Layout:**
- Layered headline: main word Fraunces 900 cream `clamp(5rem,12vw,12rem)` z-index 2; second word Fraunces 900 italic pink 50% opacity same size offset +20px +30px z-index 1; optional third word yellow small rotated 90° in margin
- "THE WAY I SEE IT" stamp Inter 900 yellow 0.3em tracking
- Pull quote Fraunces italic 500 hot pink `clamp(2rem,4vw,3.5rem)`
- Optional decorative SVG ornament pink 30% opacity
**Typography:** Layer 1 Fraunces 900 cream clamp(5rem,12vw,12rem) · Layer 2 Fraunces 900 italic pink 50% · Body Inter 400 20–22px 1.75lh · Pull Fraunces italic 500 pink
**Best for:** Dani's editorial exclusively. Dex when the piece demands swagger.

---

## 10. `broadside` — The Old Newspaper Spread
**Feel:** 19th-century broadside poster. Faded paper, ornate border, historical weight.
**Palette:** Background `#EDE3CF` aged newsprint + CSS noise grain · Text `#2B1F0F` sepia ink · Accent `#8B1E1E` muted scarlet
**Layout:**
- Decorative double-rule border with SVG Victorian corner flourishes
- "EXTRA!" / "BROADSIDE" stamp small-caps scarlet at top
- Headline in stacked Fraunces: top line 900 big, middle line 400 italic smaller, bottom line 700 small-caps smallest — broadside typesetting style
- Body Inter 400 justified 20–22px
- Drop cap Fraunces 900 scarlet 6–8 lines
- SVG fleuron ❦ ornament separators between paragraphs
- "THEN vs. NOW" two-column sidebar at bottom: scarlet small-caps headers "THEN · {year}" | "NOW · 2026"
**Typography:** Stamp Inter 900 0.3em 0.85rem scarlet · Headline top Fraunces 900 clamp(3rem,7vw,6rem) · Middle Fraunces 400 italic 0.7× · Bottom Fraunces 700 small-caps 0.4× · Body Inter 400 20–22px justified
**Best for:** Del's history primarily, any archival throwback story.

---

## Spread → Writer Default Pairings

| Writer | Beat | Preferred Spread(s) |
|---|---|---|
| Pete Caldwell | Weather | `retro_weather` (always) |
| Kelsey Rowe | Sports | `broadsheet` (always) |
| Sal Merritt | Real Estate | `big_stat`, `hero` |
| Del Haas | History | `academic`, `broadside` |
| Nina Castillo | Food & Drink | `hero`, `academic` |
| Dex Dexter | Arts & Music | `editorial`, `midnight` |
| Jess Park | Trending | `rose_stamp`, `terminal` |
| Dani Breck | Editorial | `editorial`, `midnight` |

Tech stories → `terminal` regardless of writer.

---

## Recurring Bit Visual Treatments

All use `.recurring-bit` class (border 1.5px currentColor, padding 1.25rem 1.5rem):
- **Mood of the Sky** (Pete): yellow banner top of weather spread, Inter 900 label + Fraunces italic 900 one-word mood
- **Fresh Off the Press** (Jess): 3-bullet bordered box at top, Inter 900 rust label
- **The Comps** (Sal): 5-year comparison table at bottom, rust accents
- **The Lede** (Kelsey): one-sentence callout, thick amber left border
- **Then vs. Now** (Del): two-column sidebar, scarlet small-caps headers
- **Nina's Table** (Nina): single italic verdict line, `— Nina's Table: {verdict}`
- **Dex's Drop** (Dex): block-quote at top, Fraunces italic, hot-pink attribution
- **Dani's Correction Corner** (Dani, optional): "CORRECTION CORNER" yellow label, Inter 400 cheerful self-correction

---

## Masthead & Footer

**Masthead:** `#0E0E10` bg · small-caps date line gray `#9A9A9A` · Fraunces 900 white title clamp(2.4rem,8.5vw,8.5rem) · gradient rule · small-caps tagline gray · 3px rust `#C0392B` bottom border

**Footer:** Same dark bg · Fraunces italic title white · all 8 writers + section titles middot-separated · small-caps date line

---

## Archive Index Page

- Same masthead
- "The Archive" Fraunces 900 hero
- Grid of issue cards (3-col desktop, 1-col mobile): cream bg, rust top border, date small-caps, story #1 headline, "Read →" link, hover lift
- Most recent issue pinned as 2-col feature card

---

## Build Order for `src/html_renderer.py`

1. BASE_CSS, GOOGLE_FONTS, render_page(), masthead(), footer() ← foundation
2. Helper functions: esc(), body_paragraphs(), byline_html(), source_html()
3. Spread functions in complexity order:
   1. render_hero(story)
   2. render_big_stat(story)
   3. render_academic(story)
   4. render_midnight(story)
   5. render_retro_weather(story)
   6. render_broadsheet(story)
   7. render_terminal(story)
   8. render_rose_stamp(story)
   9. render_editorial(story)
   10. render_broadside(story)
4. render_spread(story) — dispatcher, falls back to hero on unknown spread_type
5. render_issue(date, stories) — calls render_page() with all spreads joined
