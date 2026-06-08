# Boise Pulse / Morning Edition — Improvement Analysis

**Status: analysis only. No code changes. Decision points flagged for Jon.**
Date: 2026-06-06

---

## BLUF

The uploaded notes and the live repo are **two different generations of the same
newsletter**, evolved on separate tracks ==> and the notes are partly obsolete.

- The **notes** (a March chat thread) built "The Boise Pulse" as a **single-voice**
  product (everything written by "Jon C."). They won on **utility, monetization,
  and growth strategy**.
- The **repo** ("The Boise Morning Edition") is the **multi-voice** realization:
  10 distinct journalist personas, deterministic voice-lint, an 11-spread visual
  system, Gemini-research + zero-hallucination writing, Beehiiv send. It won
  decisively on **editorial craft**.

The notes literally end (lines 459-474) with that session's Claude admitting it
*never built personas* and recommending you defer them to "month 4-12." That
advice is moot ==> the repo already has 10 personas, and they are the crown jewel.

**So the correct framing is NOT "notes = new features to bolt on."** It's: the repo
already surpassed the notes on voice. The notes still hold ground the repo never
implemented ==> **reader utility, monetization surface, and growth loops**. Mine
those three. Drop the single-voice premise entirely.

---

## Challenge to the framing (read this before the priority list)

You asked "what should I improve." The more useful question hiding underneath:
**which track is each idea on?** Three of them, and they don't compete:

1. **Editorial pipeline** (how stories get written). Already very mature. The
   notes add almost nothing here that the repo doesn't do better.
2. **Reader-utility / habit layer** (reasons to open even when busy). The repo is
   thin here. This is where the notes' best idea lives (**The Vitals**).
3. **Monetization + growth** (sponsor slots, engagement loops, social pre-CTA).
   The repo has none of this. The notes have a full strategy.

Most of the "new" value is on tracks 2 and 3, which are **render/schema/business**
work ==> NOT voice work. That matters because it means you can adopt the good
parts **without touching the persona system at all.** Low risk to the thing that's
hardest to replace.

Confidence: **high.** This is a direct read of both artifacts side by side.

---

## 1. Already built vs. genuinely new

### Already built (notes are BEHIND the repo here)

| Notes idea | Repo reality | Verdict |
|---|---|---|
| Distinct writer voices / personas | 10 full persona bibles + `all_prompt_voices()` baked into the curation prompt | Repo wins, decisively. Don't regress. |
| "On This Day in Idaho" history feature | Wade Ostermann "Drive-By History" ==> landmark drive-by test, dinner-party kicker, Helmut/Arlene sourcing | Repo wins. Wade > a generic history block. |
| Editor sign-off ("Jon C.") | Maggie Halstead "— M.H." editor's note (todays_edition spread) | Built (as Maggie). |
| 3x/week cadence | Tue deep_dive / Thu weekend_guide / Fri quick_hits in `issue_types.py` | Built. |
| Beehiiv platform | `email_sender.py` draft/send integration | Built. |
| Date-accuracy worry for history | ZERO HALLUCINATION rule + `fact_confidence` / `fact_gaps` | Repo already solved the notes' open risk. |

### Genuinely new (repo does NOT have these)

| Notes idea | New? | Track |
|---|---|---|
| **The Vitals** — outdoor decision dashboard (trails, river cfs, AQI, pollen, Bogus, sunset, advisory line, status dots) | **Yes, fully new** | Utility |
| Sponsor architecture (Together With header, Vitals sponsor, sponsored Find, "The Drop") | **Yes** | Monetization |
| Quick Hits — 5-6 scannable one-liners of "other news" | **Yes** | Utility |
| Reply nudges per section + Share line | **Yes** | Growth |
| Social teaser / pre-CTA (post tomorrow's hook the night before) | **Yes** | Growth |
| Weekend Preview as a structured day-by-day list + single "Pick of the Weekend" | **Partly** (Thu issue exists; structured listing + confident single pick does not) | Utility |
| "In today's Pulse" TOC | **Yes** (Maggie's note partly overlaps) | Utility |
| The Grumble (one-line collective gripe) | **Yes** (overlaps Jess/Dani thematically) | Voice/feature |
| 30-entry Idaho history bank | **Yes, as a content asset** | Research input for Wade |

---

## 2. What conflicts with the current pipeline

1. **Single "Jon C." voice vs. 10 personas — fundamental.** The entire notes
   architecture assumes one editor writes everything. The repo's hard constraint
   is the opposite ("Never reduce persona distinctiveness"). **Resolve in favor of
   personas.** Anything from the notes must be adapted to the multi-voice world,
   not the reverse. Confidence: high.

2. **Emoji-led register vs. literary, emoji-free persona prose.** The Vitals and
   Quick Hits in the JSX lean on emoji. The persona system is deliberately
   emoji-free and `voice_lint` polices banned tokens. Emoji are fine in
   **structured data modules** (Vitals grid, Quick Hits) but must stay **out of
   persona body copy.** This needs an explicit carve-out so lint doesn't either
   miss emoji creep in columns or wrongly flag the data modules. Confidence: high.

3. **"The Find" sponsored placement vs. persona integrity.** A paid spot "written
   in voice" collides with personas whose whole credibility is independence ==>
   Nina is "cold to corporate," "never reviews on one visit"; Dani never takes
   money-shaped positions. **A sponsored module should use a neutral/editor voice
   and a hard disclosure, never a named persona's voice.** Otherwise you erode the
   exact thing that makes the personas valuable. Confidence: high — this is the
   subtlest trap in the whole set.

4. **Render architecture mismatch.** The JSX v4 is a flat single-column React
   layout. The repo renders via `html_renderer.py` + 11 spread types. You can't
   drop the JSX in ==> the Vitals/Quick Hits/Weekend modules have to be built as
   **new render components + schema fields**, taking design cues from the JSX.
   Confidence: high.

5. **Data sourcing gap for The Vitals.** Trails (Ridge-to-Rivers), river flow
   (USGS gauge), AQI (AirNow/PurpleAir), pollen, Bogus snow ==> most are **not** in
   `data_sources.py` today (which is NWS-centric). The Vitals needs either new
   fetchers or a Gemini-research-fed manual path for the MVP. Confidence: high.

---

## 3. High-value vs. nice-to-have

**High value**
- **The Vitals.** The single best idea in the notes. It's the "open even when I'm
  in a hurry" habit hook the repo lacks, it's defensible (no national app answers
  "can I do my Boise thing outside today"), it's the most sponsorable slot, and
  crucially it's a **data module that doesn't threaten the personas.** It also
  *complements* Pete rather than competing ==> Vitals = at-a-glance data; Pete =
  the narrative read. Confidence: high.
- **Monetization architecture** (header sponsor + sponsored Find + Vitals
  sponsor). High *business* value, but it's a separate workstream (schema +
  render + disclosure rules + the integrity guardrail above) and lower urgency
  until you have subscribers. Confidence: moderate-high on value, high that it's
  decoupled from editorial.

**Medium value**
- **Quick Hits** ==> adds coverage breadth in scannable form; needs a voice owner
  (Maggie or a small "newsroom" byline), not a persona column.
- **Engagement scaffolding** (reply nudge + share line + social teaser auto-gen)
  ==> cheap in render, real upside for deliverability and organic growth.
- **Weekend Preview structure + Pick of the Weekend** ==> fits Thursday; gives the
  weekend_guide issue a backbone it currently lacks.

**Nice-to-have**
- TOC / "In today's Pulse" (low effort; partly redundant with Maggie's note).
- The Grumble (charming, but thematically overlaps Jess/Dani).
- Morning greeting one-liner (overlaps Vitals + Pete).
- History bank ==> not a feature, a **reusable research input** for Wade. Free win
  whenever you wire research.

**Out of scope for the pipeline** (strategy, not build): Naptown Scoop
benchmarking, monetization confidence math, outreach emails, faceless YouTube /
Idaho history channel, power-reader tier, companion app. Useful context, not
pipeline changes.

---

## 4. Recommended priority order

**Phase 1 — The Vitals (utility moat).**
Highest leverage, additive, low conflict, doesn't touch personas. Start with an
**MVP fed by Gemini research / manual entry** (you already run Gemini each
morning), prove the format and the daily-open habit, *then* invest in live data
fetchers (USGS river, AirNow AQI, Ridge-to-Rivers, Bogus). Build it as a new
render module + schema block, design cues from the JSX, no emoji in any persona
copy. Decide where it sits in the spread plan.

**Phase 2 — Growth scaffolding (cheap, high ROI).**
Reply nudge + share line + auto-generated social teaser + TOC. Render/schema
additions, near-zero risk to voice, direct help to deliverability and organic
acquisition. The social teaser can be a generated output artifact each run.

**Phase 3 — Utility breadth.**
Quick Hits roundup and Weekend Preview structure. Needs one decision: who owns
the non-persona scannable copy (recommend Maggie or a neutral newsroom byline).
Adds the "indispensable tool" quality the notes correctly identified.

**Phase 4 — Monetization (separate workstream).**
Sponsor schema + render + disclosure rules, built on the **persona-integrity
guardrail** (sponsored modules never wear a named persona's voice). Sequence this
when subscriber count justifies a sales motion.

**Ongoing — fold the 30-entry history bank into Wade's research inputs.**

---

## Decisions I need from you

1. **Name:** "The Boise Morning Edition" (repo) vs. "The Boise Pulse" (notes/JSX).
   You wrote "aka pulse" ==> are these one brand or two?
2. **Emoji policy:** OK in structured data modules (Vitals/Quick Hits), banned in
   persona body copy ==> confirm so I can scope the lint carve-out.
3. **Monetization timing:** build the sponsor surface now, or defer until you have
   a subscriber base?
4. **Vitals MVP path:** Gemini-fed/manual first (fast), or wait for live data
   fetchers (slower, more robust)?
