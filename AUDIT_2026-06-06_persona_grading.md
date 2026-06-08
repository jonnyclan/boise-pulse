# Editorial Persona Audit — The Boise Pulse

**Issue:** 2026-06-06 · THE DEEP DIVE · TUESDAY cadence (ran Saturday via the non-publish-day fallback)
**Auditor:** Editorial Director / Master Persona Auditor
**Source of truth:** `src/personas.py` (voice rules, never_writes, signature_move, running_thesis) + `src/issue_types.py` (cadence config)
**Audit confidence:** High — graded against the committed persona spec, not impression.

---

## 1. Newsletter Format Alignment Checklist

**Cadence type:** Tuesday Deep Dive — `story_count: 6` (+1 editor's note = 7 rendered spreads).

| Constraint | Spec | Draft | Status |
|---|---|---|---|
| Total spreads | 7 (1 editor + 6 stories) | 7 | ✅ Pass |
| Spread plan order | `todays_edition → hero → academic → broadsheet → big_stat → editorial → broadside` | Exact match, in order | ✅ Pass |
| Pool writers present | sports, history, editorial, real_estate | All 4 present (Kelsey, Wade, Dani, Sal) | ✅ Pass |
| Non-pool exception budget | **One** override slot max, and only for "would-lead-a-national-Boise-story" news | **Two** non-pool writers used: arts (Dex) **and** weather (Pete) | ⚠️ **Over budget** |
| Override news bar | National-significance hook required | "Three shows this week" and "47°F clear day" — neither clears the bar | ⚠️ **Fail** |
| Weather mandatory? | False on Tuesday | Pete included anyway as broadside kicker | ⚠️ Discretionary — counts against the override budget |
| Spread ↔ writer defaults | Each writer to a fitting spread | Kelsey→broadsheet, Wade→academic, Sal→big_stat, Dex→editorial all on-default; Dani→hero (lead slot, fine); Pete→broadside (retro_weather not in Tuesday plan, acceptable sub) | ✅ Pass |
| `stat` field discipline | Short text/number only | All short and clean (`30%`, `1864`, `37`, `$519K`, `3`, `47°F`) | ✅ Pass |
| Signature lines present | Per-writer recurring bit | THE LEDE, DRIVE-BY, THE COMPS, MOOD OF THE SKY, Dex's Drop, THE WAY I SEE IT all present | ✅ Pass |

**Format verdict:** Structurally clean except the **override budget**. Tuesday grants one non-pool exception; this issue spends two (Dex + Pete) and neither story meets the substance bar Tuesday demands. The clean fix is to drop or swap **Dex** (he is simultaneously the weakest-scoring piece *and* the clearer overreach — a three-show roundup is a Thursday Weekend Guide story, not Tuesday substance). Keeping Pete as the kicker is defensible; keeping both is not.

---

## 2. Writer Persona Audits & Grading

**Scoreboard:** Wade 96 · Kelsey 94 · Sal 91 · Maggie 91 · Pete 90 · **Dani 81** · **Dex 63**

---

### Margaret "Maggie" Halstead — Today's Edition
* **Cadence Slot & Spread Type:** Slot 1 | todays_edition
* **Score:** 91/100
* **Pillar Breakdown:**
  * Structural Discipline: 22/25
  * Sourcing & Local Anchors: 22/25
  * Cadence & Tone: 23/25
  * Running Thesis Execution: 24/25
* **The Good:** The lead-the-reader move is textbook — "**Read Dani first.** It's the piece that sets the frame" points the reader at one piece and says *why*, the exact thing an aggregator can't do. The close lands the thesis cleanly: "*the order is the argument.*"
* **The AI Tells & Critical Alignment Gaps:** Lowercase "saturday" appears three times — a polish miss in the one voice that stitches the whole issue. Opener runs ~110 words against her 120–160 spec, so the "serious middle" is thin. The Saturday framing also fights the "DEEP DIVE · TUESDAY" masthead — if the run date is going to surface in copy, the masthead should agree with it.

---

### Dani Breck — The Way I See It
* **Cadence Slot & Spread Type:** Slot 2 | hero
* **Score:** 81/100
* **Pillar Breakdown:**
  * Structural Discipline: 23/25
  * Sourcing & Local Anchors: 13/25
  * Cadence & Tone: 21/25
  * Running Thesis Execution: 24/25
* **The Good:** Opens *inside* the argument with no throat-clearing — "Every week somebody cites 'population growth' as if it were a verdict… It isn't." The required closer is present and strong: three concrete numbers to watch instead. Plainspoken, not angry — she stays out of the trap.
* **The AI Tells & Critical Alignment Gaps:** This reads like a generic op-ed, not Dani's civic-ledger column, because her **proper-noun hammer is missing**. Her spec demands elected officials by name, agencies by acronym + full name, bill/ordinance numbers, and meeting dates — the draft has *none*. "A city council that celebrates a number" is exactly the generic she never writes. Her three-source rule is unmet (one gesture at "the Census"). And her signature steelman ("state the opposing view in its strongest form **first**") is inverted — "I'm not against growth" arrives last and weak. The thesis is perfect; the sourcing scaffolding that makes her *Dani* is absent.

---

### Wade Ostermann — Drive-By History
* **Cadence Slot & Spread Type:** Slot 3 | academic
* **Score:** 96/100
* **Pillar Breakdown:**
  * Structural Discipline: 25/25
  * Sourcing & Local Anchors: 25/25
  * Cadence & Tone: 23/25
  * Running Thesis Execution: 23/25
* **The Good:** This is the reference implementation. Opens with the bookend question — "You know that brick building on Grove Street?" — explains Basque in one clean civilian line, rounds the date ("1864, give or take"), drives the reader to **607 Grove Street**, and signs off "That's the one you tell at dinner." Helmut delivers the 1910 correction and **Arlene at the Historical Society** confirms it — the "I heard this, I didn't discover it" thesis executed inside the prose, not announced.
* **The AI Tells & Critical Alignment Gaps:** Nearly none on voice. One fact-confidence flag for the desk (not a voice deduction): the "yellow door is the original Basque color so non-readers knew the house" kicker is the kind of charming claim that should carry an Arlene/ISHS sign-off before print, since it's the line readers will repeat.

---

### Kelsey Rowe — The Bench
* **Cadence Slot & Spread Type:** Slot 4 | broadsheet
* **Score:** 94/100
* **Pillar Breakdown:**
  * Structural Discipline: 23/25
  * Sourcing & Local Anchors: 25/25
  * Cadence & Tone: 23/25
  * Running Thesis Execution: 23/25
* **The Good:** The proper-noun hammer is relentless and correct — **The Blue**, **the MW**, **Broncos Nation**, **Tam at the Ram on Broad Street** (used as barometer, not quote source), Eagle High, the Famous Idaho Potato Bowl. The walk-on thesis is fully earned: she lands on **Cole Aguiar** by name, ties in her own ACL backstory late and quietly, and closes "Somebody will beat me to it by the spring game. Good." Catchphrase "Numbers don't argue." used once.
* **The AI Tells & Critical Alignment Gaps:** The `recurring_bit_content` repeats the body's two-sentence Lede **verbatim** — that's a duplication the voice-lint can flag and it wastes the callout. The bit should compress or vary, not echo word-for-word.

---

### Sal Merritt — The Market
* **Cadence Slot & Spread Type:** Slot 5 | big_stat
* **Score:** 91/100
* **Pillar Breakdown:**
  * Structural Discipline: 24/25
  * Sourcing & Local Anchors: 22/25
  * Cadence & Tone: 24/25
  * Running Thesis Execution: 25/25
* **The Good:** Numbers-first open, and the un-averaging thesis is the whole spine: "Inventory in the North End dropped 11%. Inventory in Meridian rose 7%… Same median, different market." THE COMPS closes it. Skeptical of both happy-talk and doom-talk — "mathematically interesting and economically inert" is pure Sal.
* **The AI Tells & Critical Alignment Gaps:** His **signature move is missing** — the single-sentence "street + year + last price + today's price" hammer (e.g., "2312 N 17th sold in 2019 for $319K…"). No specific street, subdivision (Harris Ranch, Avimor), or developer (CBH, Brighton) appears, so the anchors stay at city-name altitude. THE COMPS is also not strictly *annual* — it skips 2020 and 2021 (2019 → 2022 → 2023…), a minor deviation from the "2019→2025 annual" spec.

---

### Dex Dexter — The Scene
* **Cadence Slot & Spread Type:** Slot 6 | editorial
* **Score:** 63/100
* **Pillar Breakdown:**
  * Structural Discipline: 18/25
  * Sourcing & Local Anchors: 12/25
  * Cadence & Tone: 17/25
  * Running Thesis Execution: 16/25
* **The Good:** Opens with a block-quoted Drop and names two real venues (Shrine Social Club, Neurolux). "The point of a basement show is that you had to know a guy" is a genuine Dex line.
* **The AI Tells & Critical Alignment Gaps:** Four real misses. (1) **The Drop never closes the loop** — his core mechanic is that the lyric and the night end *in dialogue*; here the lyric floats decoratively, exactly what `never_writes` forbids ("earned not decorative"). (2) **No band names, no set times, no labels** — a music writer with zero bands fails the proper-noun hammer outright. (3) **Labor goes unnamed** — no promoter, bartender, sound engineer, no Coop; the spec says scene pieces honor labor. (4) The `source` field reads **"Boise State University"** — a placeholder that has nothing to do with three club shows. He also leans on "the scene" as filler. The thesis is gestured at (openers better than headliners) but never *executed* — he claims the openers won without naming a single one.

---

### Pete Caldwell — The Forecast
* **Cadence Slot & Spread Type:** Slot 7 | broadside (retro_weather not in the Tuesday plan)
* **Score:** 90/100
* **Pillar Breakdown:**
  * Structural Discipline: 23/25
  * Sourcing & Local Anchors: 22/25
  * Cadence & Tone: 23/25
  * Running Thesis Execution: 22/25
* **The Good:** MOOD OF THE SKY: BRIGHT — one word, correct. Anchors the inversion line off **Capitol Boulevard** and the **Bench**, and closes on a real decision: "If you're walking the dog: a real jacket." The homey aside lands — "The dog… does not read weather columns; she just wants to go." Pull-quote echoes "the sky has opinions."
* **The AI Tells & Critical Alignment Gaps:** Voice is clean; the problem is **placement, not prose** — Pete is a non-pool writer on a substance day with no weather emergency, so he is spending the issue's second (over-budget) exception slot for a routine clear-sky forecast. Could lean harder on the hammer (Table Rock, Bogus) but that's polish, not a fault.

---

## 3. The 93+ Remediation Path

Two writers land below the 93 line and need surgical fixes. Dex is the mandatory case (sub-80); Dani is the high-value near-miss.

* **Dex Dexter — Action Items (63 → 93+):**
  * **Fix the Drop (close the loop):** the lyric must answer the night. After "If you ain't payin' rent on a stage you ain't sayin' nothin'," end the piece by paying it off — e.g., "The opener at Shrine was paying rent on that stage. The headliner was paying a publicist." The Drop and the night must end in dialogue.
  * **Fix the proper-noun vacuum (name the openers):** his whole thesis is naming the opener before the headliner. Replace "the touring openers are better than the headliners at two of the three" with named acts and set times: "[Opener band] went on at 9:40 at Shrine and buried [Headliner]; same story Saturday at Neurolux when [Opener] took the 10 o'clock slot." (Pull real names from the research dossier — do not invent.)
  * **Fix the labor omission:** add a named scene-worker per spec — "Coop at the Neurolux door called the Saturday bill before doors: 'openers eat tonight.'"
  * **Fix the `source` field:** "Boise State University" is wrong. Set `source` to the venues/promoter actually referenced (e.g., "Shrine Social Club · Neurolux · attended") — never a placeholder.
  * **Fix the placement:** if no act named clears the Tuesday substance bar, this piece moves to Thursday's Weekend Guide and a pool writer takes the editorial slot.

* **Dani Breck — Action Items (81 → 93+):**
  * **Fix the missing hammer (name the civic actors):** replace "a city council that celebrates a number" with the actual process — "When the Council voted 5–1 on [ordinance #] June 2, Mayor McLean's office led with population growth." Name officials, agency (ACHD / Ada County Highway District on first use), bill/ordinance numbers, meeting dates. This is the single change that moves her from op-ed to Dani.
  * **Fix the sourcing floor:** satisfy the three-source rule on the page — pair the Census line with two more named anchors (e.g., "COMPASS migration data" + "Gayle at the Clerk's office pulled the 2019 ordinance"). One gesture at "the Census" is below her own bar.
  * **Fix the inverted steelman:** move the strongest opposing case to the **front**. Change the late "I'm not against growth" to a lead steelman: "The case for celebrating growth is real — more rooftops mean more tax base, and a stalled city is its own failure. Here's why the number still misleads:" then dismantle with the same data.

---

**Bottom line:** Five of seven writers are at or near publish-grade (90–96), with **Wade as the model**. The issue's two liabilities are (1) the **over-budget override** — drop or reschedule Dex — and (2) **Dani's missing civic hammer**, the highest-leverage single fix in the issue. Apply the prescriptions above and every retained piece clears 93.

> **Update — Dani fix applied (2026-06-06 issue).** The hero piece has been rewritten in both `magazines/2026-06-06.stories.json` and `magazines/2026-06-06.html`: steelman moved to the front, named-official/ordinance/agency anchors added (COMPASS spelled out, Gayle at the Clerk), source line corrected to `U.S. Census · COMPASS · Boise City Clerk`. Three specifics are held as bracketed placeholders — `[Mayor McLean's office]`, `[June __ Council meeting]`, `[ordinance #___]`, `[year]` — pending fact confirmation (see §5 for the durable fix). Do not publish until those four brackets are filled or cut.

---

## 4. Defensibility / Moat Audit — All 10 Personas

**Key finding (high confidence):** The moat is *designed* correctly. Every persona in `personas.py` carries the three layers a defensible hyper-local brand needs — an **anti-aggregation filter** (an explicit rule to refuse the wire), a set of **proprietary regional-authority nodes** (named human relationships and physical places a competitor cannot scrape or an AI cannot fabricate), and a **voice fingerprint** (a hard mechanic plus a banned-word list the deterministic `voice_lint` can enforce). The brand is not at risk from the spec. It is at risk at **runtime**, in exactly one failure mode: **when the Gemini dossier is thin or empty, the fact-dependent writers fall back to generic essay/roundup — which is the precise AI-aggregation tell the brand sells against.** The 2026-06-06 issue proves it: the two weakest pieces (Dex 63, Dani 81) both leaked on the authority layer, and both leaks trace to the empty `research/2026-06-06.json`, not to the personas.

### The moat map

Each writer's "proprietary nodes" are the unreplicable IP — relationships and places that cannot be aggregated, only earned and maintained.

| Writer | Anti-aggregation filter | Proprietary regional-authority nodes (the IP) | Voice fingerprint (mechanic · banned tells) |
|---|---|---|---|
| **Kelsey** (sports) | Writes only when the wire *missed* a Boise angle; never rewrites AP | Tam at the Ram booth 4 · The Blue end-zone · ICA press row §112 · her own walk-on/ACL POV | "The Lede" · tiny-number→plain-cost · "Numbers don't argue" · never *gritty/grinder/blue-collar* |
| **Pete** (weather) | NWS/BLM is the story; never files without a *decision* | Backyard weather station · Dottie · Gordo's knees at Gordo's Hardware on Vista · Marla at NWS desk | "MOOD OF THE SKY:" + one word · number→life-advice · "weather guy" never *meteorologist* |
| **Sal** (real estate) | Un-averages the average; reads building permits, not press releases | Marla's permit spreadsheets · the Wednesday crew at Big City Coffee · Jen at Whittier | numbers-first · THE COMPS · street+year+price in one sentence · never *luxury/desirable/affordable* |
| **Wade** (history) | Dinner-party test + drive-by test; "I heard it, didn't discover it" | 27-yr North End mail route · Helmut across the street · Arlene at ISHS · the postcard binders · Deb | "You know that ___ on ___?" · address-as-hammer · "That's the one you tell at dinner." |
| **Nina** (food) | Two visits minimum; never reviews a chain unless it's closing | Tito's taqueria on 11th (reference plate) · Chef K at Kibrom's · Auntie Lu · Oskar at Juniper | sensory-first · exact dish + price-to-the-dollar · "— Nina's Table:" · never *elevated/curated/artisanal* |
| **Dex** (arts) | Was-in-the-room only; no press releases | Coop at the Neurolux door · Sasha (16, generational check) · the Egyptian crew · the unnamed 14th-St basement | "Dex's Drop" lyric-in-dialogue · opener-before-headliner · italic asides · never *underrated/hidden gem* |
| **Jess** (trending) | One specific post over threshold; names the pattern, never "the internet" | the Discord (40 transplants) · Marco the NextDoor bridge · the r/Boise mods · Gyoza | FRESH OFF THE PRESS 3-bullet *editorial* box (never links) · "it's always zoning" · community-as-character |
| **Hayley** (lifestyle) | Tried-it-or-calling-it binary; the group-chat screenshot test | Shelby at the Eagle Rd Joann (saves remnant bolts) · Owen/Emmy/Kyle · the Meridian split-level filming island | HAYLEY'S RATIO ($ / min / kids-out-of-2) · origin-attribution · never *babe/obsessed/influencer* |
| **Dani** (editorial) | Three named sources or kill the column; reads the minutes | Council seat 4 (held one term) · Gayle at City Clerk · Ron · McLean CoS on background | steelman-first · named officials + bill/ordinance numbers · three-numbers closer · never *common sense/silent majority* |
| **Maggie** (editor) | Picks *order and frame*, not stories | the room itself (writers by first name) · Carol the native skeptic · Jordan the civilian test · Lola | "Read X first" + why · "— M.H." · "the issue is the argument" |

### Where the moat held vs. leaked on 2026-06-06

**Held (the brand showed up):** Wade is the reference — Helmut's 1910 correction, Arlene's confirmation, and 607 Grove Street are textbook unreplicable IP; no aggregator produces that paragraph. Kelsey (Tam at the Ram, The Blue, Cole Aguiar the wire missed) and Sal (un-averaging North End vs. Meridian) both held their filter and fingerprint.

**Leaked (the brand slipped toward generic):** Two failures, both on the authority layer, both traceable to the empty dossier.

First, **Dex's `source` field read "Boise State University"** for a piece about three club shows — a placeholder mismatch that is itself the aggregation tell: a beat-disconnected institutional source is what a scraper emits, not what a scene writer files. He also named zero bands, which is the opposite of his proprietary node (he *is* the guy who names the opener). Second, **Dani ran with zero named officials, zero bill numbers, one gesture at "the Census"** — her entire moat is the civic proper-noun hammer, and without the dossier she defaulted to an op-ed any model could write. (Now fixed; see §3 and the §3 update note.)

The pattern is the headline: **the writers whose authority lives *inside* them (Wade's route, Kelsey's POV, Maggie's room) are moat-stable even on a slow data day; the writers whose authority lives in *fresh external facts* (Dani's votes, Dex's lineups, Sal's monthly comps) are moat-fragile and degrade straight into aggregation when the dossier is thin.** Protecting the brand means protecting *those* writers' data supply.

---

## 5. Systemic Recommendations — Convert the Moat From "Hope" to "Enforced"

Two changes turn the defensibility from a style guide the model may ignore into a guarantee the pipeline enforces.

### A. Gemini "Fact Ledger" upgrade (the durable fix you flagged)

The Tuesday/Thursday/Friday `GEMINI_DEEPRESEARCH_*.txt` prompts already demand named officials, vote tables, and a "COULD NOT VERIFY" checklist — but the output is prose Claude re-parses, and nothing forces a *per-fact* verification status that the zero-hallucination locker can key on. Add this block to the REQUIRED DELIVERABLES of each beat (it maps 1:1 onto the dossier's `named_people` / `key_numbers` / `direct_quotes` / `fact_confidence` / `fact_gaps`):

> **FACT LEDGER (required, per beat).** Build a table of EVERY proper noun, date, number, dollar figure, and direct quote you used in this beat. Columns: *Item · Value as written · Status (✓ VERIFIED / ⚠ UNVERIFIED) · Source URL*. The writer may print ONLY ✓-tagged items. Any ⚠ item must be hedged or cut — never asserted. If an item is not in this ledger, it may not appear in the beat narrative.

This is the systemic answer to the Dani placeholders: with a Fact Ledger, the `[Mayor McLean's office]` / `[ordinance #___]` brackets arrive pre-verified from Gemini instead of being hand-confirmed after the fact. (Note: the rich-JSON `GEMINI_PROMPT_FRIDAY.txt` already does most of this via its dossier fields — standardizing Tuesday/Thursday onto that JSON format, per the open decision in `GEMINI_CLAUDE_VETTING.md`, would make the ledger native rather than bolted on. Confidence: high that this closes the runtime leak.)

### B. Two new deterministic `voice_lint` guardrails

The lint already catches signature lines and writer duplication. Add two checks that would have caught *both* of this issue's leaks automatically:

First, a **source-beat mismatch check** — FAIL any piece whose `source` field is a generic institution unrelated to the writer's beat (Dex's "Boise State University" for a music column). Maintain a small per-beat allowed/disallowed source heuristic; a music piece sourced solely to a university is a hard FAIL.

Second, a **proper-noun floor** — the anti-aggregation enforcement. Each fact-dependent writer must clear a minimum count of their required proper-noun class, or the piece WARNs/FAILs: Dani ≥ 1 named official **or** bill/ordinance number; Sal ≥ 1 named street, subdivision, or developer; Dex ≥ 1 named band or act; Nina ≥ 1 named dish + price; Jess ≥ 1 named pattern/topic. A fact-writer who files with zero proper nouns of their class has, by definition, filed aggregation — and the lint should stop it before GO.

Together these make the moat *testable on every run* rather than dependent on model compliance — which is exactly the property an investor diligencing "defensible IP" will want to see: the distinctiveness is mechanically guaranteed, not vibes.

**Confidence summary:** Moat design — high (the three layers are present for all 10). Runtime-leak diagnosis — high (both 06-06 leaks reproduce the empty-dossier failure mode). Recommended fixes — moderate-to-high (the Fact Ledger and source-mismatch lint are low-risk; the proper-noun floor needs tuning so it WARNs before it FAILs, to avoid false positives on legitimately short kickers like Pete's broadside).
