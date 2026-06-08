# The Boise Pulse — project guide for Claude

This repo is a 3-day-a-week local newsletter generator. Tuesday = deep_dive,
Thursday = weekend_guide, Friday = quick_hits. The pipeline curates stories
with Claude Sonnet 4.6 (`USE_REAL_AI=1`) and renders to HTML in `magazines/`.

## Morning workflow — Gemini Deep Research + Claude pipeline

**This is the standard 3x-a-week morning sequence.** Jon runs Gemini Deep
Research first (manually, in the Gemini web app), then hands the output to
Claude, who saves the research file and runs the pipeline.

### Step 1 — Jon runs the Gemini Deep Research prompt
Open `GEMINI_DEEPRESEARCH_FRIDAY.txt` (or TUESDAY / THURSDAY). Update
TODAY's date at the top. Paste into Gemini → Deep Research. Wait for full
output (~2–5 min). Copy everything Gemini returns.

### Step 2 — Jon says a trigger phrase to Claude (see below)
Claude will immediately ask: **"Paste your Gemini Deep Research output and
I'll take it from there."** Jon pastes the raw Gemini text. Claude then:

1. Parses the Gemini output into the rich research JSON schema — including the
   **Vitals** block (`vitals`) alongside the per-beat `assignments`
2. Saves it to `research/YYYY-MM-DD.json` (overwriting if exists)
3. Runs the full pipeline via bash (`python pre_publish_check.py --preview`)
4. Reports GO / NO-GO, writer assignments, and lint results

If Jon has no Gemini output (skipped research, ran out of time), Claude can
run without it — just say "skip gemini" or "no research today" and Claude
will run `pre_publish_check.py --preview` directly (Claude self-selects).

### Story swap (human-in-the-loop override)
Before running the pipeline, Jon can say: **"swap [beat] to [topic/story]"**
and Claude will update that assignment in the research JSON before writing.
Example: "swap lifestyle to Zoo Boise World Penguin Day" ==> Claude updates
the lifestyle assignment and runs as normal.

### Research JSON schema (what Claude saves to `research/YYYY-MM-DD.json`)
Each beat maps to a key (`trending`, `sports`, `editorial`, `weather`,
`lifestyle`, `food`, `arts`, `history`, `real_estate`) and contains:
- `angle` — the specific story angle Gemini selected
- `hook` — opening hook for the writer
- `key_facts` — list of verified facts the writer must use
- `named_people` — full names and roles (ONLY these names may appear in copy)
- `key_numbers` — specific stats/figures with units
- `direct_quotes` — verbatim quotes with attribution
- `community_reaction` — local sentiment / Reddit / Nextdoor flavor
- `writer_fuel` — texture, color, anecdote for voice
- `sources_checked` — list of sources Gemini verified against
- `fact_confidence` — HIGH / MEDIUM / LOW
- `fact_gaps` — items Gemini could not verify (writer must hedge)

**File wrapper:** the saved `research/YYYY-MM-DD.json` wraps the per-beat dossiers
under an `assignments` key, with a sibling `vitals` key:
`{"_meta": {...}, "assignments": {"sports": {...}, ...}, "vitals": {...}}`.
The pipeline reads `research["assignments"]` for story angles and
`research["vitals"]` for The Vitals dashboard.

**The Vitals block** (`research["vitals"]`) powers the outdoor-decision dashboard
rendered under the masthead. Shape: `cells` (exactly 6 — two anchors Weather +
Daylight, plus four seasonal: spring = Foothills Trails / Boise River / Pollen /
Air Quality; summer = Air & Smoke / Boise River / Fire & UV / Foothills Heat; fall
= Foothills Trails / Cottonwoods / First Frost / Air Quality; winter = Bogus Basin
/ Inversion & Air / Roads & Passes / Overnight Low). Each cell is
`{icon, label, main, sub, status}`, status ∈ good|neutral|caution|alert. Plus
`advisory` = `{level: info|caution|alert, text}` — one plain-language decision line.
If `vitals` is absent, the pipeline renders a season-aware mock from NWS weather
(`src/vitals.py`).

**ZERO HALLUCINATION RULE** (enforced in `ai_engine._format_locked_assignments()`):
Claude may only use names from `named_people`, numbers from `key_numbers`,
and quotes from `direct_quotes`. Anything not in the dossier gets hedged or
omitted — never invented.

---

## Quick commands (trigger phrases)

If Jon says any of these, run the matching one-liner from the repo root:

**"run friday"** (or "run tuesday" / "run thursday" / "run the newsletter" /
"today's issue" / "ship it" / "publish today")
==> Claude asks for Gemini output first, then runs:
`python pre_publish_check.py --preview`

That script runs the full pipeline (curate + render), then prints:
- voice-lint FAIL/WARN counts
- writer-assignment table (slot / spread / writer / headline)
- writer-duplication check (hard FAIL)
- signature-line check (MOOD OF THE SKY, Nina's Table, Dex's Drop, FRESH OFF THE PRESS, Arlene/DRIVE-BY)
- GO / NO-GO verdict

Exit 0 = GO. Exit 1 = NO-GO with the offending problem printed. On GO with
`--preview`, the rendered HTML opens in the default browser.

**"proof the email"** ==> `python pre_publish_check.py --preview --draft`
  On GO, posts the issue to Beehiiv as a draft so you can review it in
  the Beehiiv editor before sending. Nothing goes to subscribers yet.
  Requires BEEHIIV_API_KEY + BEEHIIV_PUBLICATION_ID in .env.

**"send the newsletter"** (or send it / email it / deliver it)
==> `python pre_publish_check.py --preview --send`
  On GO, sends immediately to all Beehiiv subscribers.

**"just generate, no check"** ==> `python generate_magazine.py`

**"mock run"** (no Claude, for debugging render/lint changes) ==> `USE_REAL_AI=0 python generate_magazine.py`

## Architecture at a glance

- `generate_magazine.py` ==> orchestrator (fetch ==> curate ==> lint ==> render)
- `src/ai_engine.py` ==> curate prompt + Claude call + retry loop
- `src/voice_lint.py` ==> deterministic lint (no LLM-as-judge)
- `src/render.py` ==> HTML output
- `src/writers.py` ==> 10 persona definitions (Pete weather, Nina food, Dex arts, etc.)
- `src/spreads.py` ==> 11 visual spread types + strict/soft writer pairings
- `src/email_sender.py` ==> Beehiiv API integration (draft_issue / send_issue)
- `.env` ==> ANTHROPIC_API_KEY, USE_REAL_AI, RETRY_ON_FAIL, VOICE_LINT_STRICT, BEEHIIV_API_KEY, BEEHIIV_PUBLICATION_ID

## Guardrails wired (do not remove without asking Jon)

1. **STRICT-WRITER EXCLUSIONS** block in `ai_engine._build_curation_prompt()`
   ==> when `retro_weather` or `academic` is in the plan, tells Claude not to
   re-use that writer on hero/other soft slots (prevents weather-2x FAIL).
2. **Retry-on-FAIL** in `ai_engine.curate_stories()` ==> if voice_lint finds
   any FAIL, re-prompts Claude once with the specific FAILs injected.
   Toggle with `RETRY_ON_FAIL=0`.
3. **VOICE_LINT_STRICT=1** ==> lint FAILs abort publish. Set to 0 only for
   emergency publishes.

## Jon's hard constraints

- Never reduce persona distinctiveness (each writer has a strong voice — keep it)
- Never simplify the visual spread system (11 spreads is the point)
- Prompt improvements must ADD specificity, not length
- Spell "Starlite" (never "Starlight")
- Use "==>" connector, not "-" or "--"
- Never refer to personas as "Speaker 1/2/3"

## When something breaks

- `[NO-GO]` with writer duplication ==> check `ai_engine.py` line ~955 for
  the STRICT-WRITER EXCLUSIONS block; confirm it's still in the built prompt
- `[NO-GO]` with signature miss ==> a persona dropped its signature line;
  check the persona in `src/writers.py` for the signature instruction
- Claude call hangs ==> check `.env` has a non-empty `ANTHROPIC_API_KEY`
