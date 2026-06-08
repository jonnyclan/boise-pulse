# Boise Morning Edition — Quality Audit
**Audit date:** 2026-04-23
**Issues reviewed:** 2026-04-23 (Thursday Weekend Guide) · 2026-04-21 (Tuesday Deep Dive)
**Benchmarks:** The Information, Axios, Stratechery, The Hustle, Morning Brew, The Economist, Puck News, The New Yorker

---

## BLUF

The Edition is closer to world-class than the scorecard suggests. Voice is the strongest asset ==> the eight writers genuinely sound like different people, recurring bits mostly land, and the local data integration is specific and timely. The two things dragging the reading experience down are both fixable without touching the personas: (1) a broken `stat` field contract that's putting full sentences into single-number slots across three spread types, and (2) a cluster of sentence-level "AI tells" in body copy (third-person self-reference, throat-clearing, ending-summaries). Fix Tier 1 and the product jumps a full tier.

**Overall weighted score: 6.4/10** — serious regional newsletter, not yet elite.

---

## Phase 2 — 8-Dimension Audit

### Dimension 1: Voice Authenticity — 7/10
The writers genuinely sound like different people. Pete opens "MOOD OF THE SKY: BORROWED." and the sky "has opinions." Wade opens "You know that stretch of Highway 55…" and closes "That's the one you tell at dinner." Dani reasons in civic ledger terms ("measuring the thing"). Dex's drops land. Nina verdicts close with her Table line. The system is working.

Where it drifts: writers refer to themselves in the third person inside their own pieces ==> "What Sal's been tracking specifically" (Sal's column), "Kelsey has the angle" (fine in Maggie's note, weak when Kelsey does it about herself). The recurring-bit content on Wade's 04-21 piece shows the prompt instructions leaking into the rendered field: the THEN VS. NOW block literally contains "Drive-By History — open with 'You know that [thing] on [street]?'; close with 'That's the one you tell at dinner.'" That is the prompt instructions appearing verbatim in the output.

### Dimension 2: Headline & Deck Quality — 7/10
Headlines earn the scroll. "That highway full of sheep isn't a traffic accident" is a Morning Brew–caliber headline. "Steelheads draw the Americans — here's what that means" is specific and promises insider analysis. "82 degrees, then the bottom falls out tonight" is exactly the right register for Pete.

Decks mostly do real work. "Thousands of runners, ACHD road closures, Boise Parks involvement — and a public accounting question nobody's formally answered" advances the argument. Weaker examples restate the headline with slightly different words ==> "A sweeping-view property near Bogus just listed. The number is one thing. What it reveals about the upper-tier Foothills market is another." That deck tells me nothing the headline didn't already imply.

### Dimension 3: Body Copy Quality — 6/10
Original observation density is high. Sal's view-premium comp ("A rancher on the Bench with the same square footage as a Foothills property with a Table Rock view will sit 22 days longer on average") is the kind of number that makes a real estate column readable. Wade's "The sheep do not know about the roundabout" is a genuinely human sentence.

What drags the score: paragraph-length discipline is inconsistent. The 04-21 broadsheet runs six paragraphs at ~110-140 words each, with the COMPS list literally duplicated inside the body (it appears in the `.lede` block AND as the final paragraph of `.columns`). The writer's own name shows up in body copy ("What Sal's been tracking specifically"). Throat-clearing openers recur ==> "Here's what a listing like this tells you about the Foothills tier right now."

### Dimension 4: Structural Discipline — 6/10
Spread counts match plan. Tuesday 04-21: 6 stories + editor = 7 spreads ✓. Thursday 04-23: 8 stories + editor = 9 spreads ✓. Issue types are producing noticeably different experiences — Tuesday feels substantive, Thursday feels event-forward.

Where structure breaks down: on 04-23, Pete Caldwell is rendered in BOTH slot 2 (hero) AND slot 5 (retro_weather) — same writer twice in one issue. The current voice-lint `_check_structure` only flags 3+ writer duplication, so 2x passes. Also on 04-23, Nina Castillo is rendered on `broadsheet`, which DESIGN.md reserves for Kelsey/The Bench. Spread-writer drift is happening without being caught.

### Dimension 5: Visual Design Fidelity — 5/10
This is the biggest visible problem in the product. The `stat` field on three spread types (big_stat, broadsheet scoreboard, retro_weather) is defined in DESIGN.md and the CSS as a single massive number — `statnum` renders at `clamp(9rem, 28vw, 24rem)` in Fraunces 200 italic; `scoreboard .num` at `clamp(3rem, 6vw, 5rem)` in Fraunces 900; `retro_weather .temp` at `clamp(8rem, 20vw, 18rem)` in Fraunces 900. The point of these spreads is visual dominance of ONE number.

The AI is filling that field with sentences:
- 04-21 big_stat: *"82°F high → 43°F overnight: 39°F swing in under 12 hours"* in the 24rem slot
- 04-21 broadsheet scoreboard: *"DOM above $1.5M in Ada County: 41 days (Q1 2024) → 67 days (Q1 2026)"*
- 04-23 broadsheet scoreboard: *"Birria quesatacos: $14 for three. Churros gone by 8pm."*
- 04-23 retro_weather `.temp`: *"Friday high 59°F · Friday night low 34°F · Wind 2–14 mph"*

Also broken: the broadside Then|Now render expects a pipe-delimited string in `recurring_bit_content`. Neither issue provided one. Result: "Now · 2026" column shows "—" and "Then" column shows prompt instruction text. Masthead and footer land with the premium feel intended.

### Dimension 6: Data Source Integration Quality — 7/10
Stories feel genuinely local and timely. Pete cites NWS specifics (50°F open, 82°F high, 43°F overnight, winds from the Owyhee gap, 9-11pm onset). Wade cites the ISHS reference desk and the BLM allotment history with a 1910 date. Jess's Fresh Off The Press names specific r/Boise usernames (u/BoiseNorthender, u/IdahoSpud420) and vote counts (138 pts / 15 comments — a high ratio that means something). Dani pulls ACHD 2024 budget hearing minutes. This is the non-generic version of local coverage.

Room to grow: Pete's 04-23 retro_weather body could cite the specific NWS forecast discussion narrative, not just numbers. Del's "On This Day" content isn't appearing in either issue because neither triggered `history` outside of Wade's piece, so this is a scarcity observation not a quality knock.

### Dimension 7: The "Too AI" Problem — 5/10
The failure modes I can catalogue from these two issues:

*Third-person self-reference in own piece* ==> "What Sal's been tracking specifically" (Sal's column); "Nina's Table:" is fine as a sign-off but would be a red flag inside the body.

*Throat-clearing openers* ==> "Here's what a listing like this tells you about the Foothills tier right now"; "The strongest version of the argument against scrutinizing Race to Robie Creek goes like this…" (this one is specifically the AI-trained rhetorical gambit of steelmanning before arguing — a tell).

*Ending-summary pattern* ==> "The view premium doubled in three years. That's a real number." The piece just said this. The restatement is the tell.

*Defensive parenthetical explanations* ==> "DOM — days on market, meaning the number of days between list date and accepted offer" (Sal is writing for locals who already know DOM; the gloss is AI over-explaining).

*Em-dash overuse* ==> Sal, Pete, and Dani all average 4+ em-dashes per piece. The dash is doing the work of real punctuation choices.

*Meta-narration* ==> "That's not a coincidence, and it's not a supporting detail — it's the whole equation." Real writers don't tell you how load-bearing a sentence is.

### Dimension 8: The "Would I Actually Read This?" Test — 7/10
Reading cold as a Boise resident: the Steelheads piece grabs (specific, insider-y, names Trent Miner's save percentage correlation). The Basque sheep piece is irresistible ("The highway is the newcomer"). The weather piece is usable ("If you have anything in a truck bed, the truck bed wants to be empty by 7pm"). The Robie Creek editorial asks a civic question I actually want answered.

What makes me scroll past: the visual stat-field bug signals "something's broken here" on first glance. The real estate body is dense and repeats itself. The broadside Then/Now showing "—" looks like a bug. The rose_stamp on 04-23 shows its FRESH OFF THE PRESS content twice.

**The single biggest thing killing the reading experience: the `stat` field sentence-in-single-number-slot bug.** It's the first thing a reader sees on three spread types and it signals amateur hour before the body gets a chance.

---

## Phase 3 — Tiered Findings

### TIER 1 — Fix These First

**T1.1 — Fix the `stat` field contract** ==> *prompt change + voice_lint*
*Files:* `src/ai_engine.py` (curation prompt), `src/voice_lint.py` (new check)
*Current state:* `stat` field receives 40-60 character sentences with multiple data points.
*Fixed state:* `stat` is a single scalar — "$2.1M" or "67 DAYS" or "39°F SWING" — max 12 characters, formatted for ~24rem display. The prompt needs a per-spread `stat` schema. voice_lint adds a `_check_stat_length` that FAILs on any stat >15 chars.

**T1.2 — Define the `recurring_bit_content` schema per spread** ==> *prompt change + renderer*
*Files:* `src/ai_engine.py`, `src/html_renderer.py`
*Current state:* `recurring_bit_content` is a free-form string. Broadside expects `Then|Now` pipe-delimited; rose_stamp expects 3-bullet FRESH OFF THE PRESS; academic (Wade) receives prompt instructions by mistake.
*Fixed state:* Per-spread content shape declared in prompt. Renderer validates and falls back cleanly. Wade's "Drive-By History — open with..." text never reaches the reader.

**T1.3 — Writer duplication FAIL, not WARN** ==> *logic change*
*File:* `src/voice_lint.py` (`_check_structure`)
*Current state:* 2x same writer passes; only 3+ fails. Pete appeared 2x on 04-23.
*Fixed state:* Any writer appearing 2+ in one issue is a FAIL (exception: editor_in_chief opener doesn't count). Override comment required to bypass.

**T1.4 — Writer/spread pairing drift (Nina on broadsheet)** ==> *prompt change*
*File:* `src/ai_engine.py` (curation prompt)
*Current state:* Prompt does not assert the DESIGN.md writer/spread pairings. Curator put Nina on Kelsey's broadsheet.
*Fixed state:* Prompt declares the canonical pairings (broadsheet=Kelsey OR Sal, big_stat=Pete OR Sal, academic=Wade, editorial=Dani, etc.) as a hard constraint. voice_lint adds a compatibility check.

**T1.5 — Body-copy list duplication (broadsheet COMPS)** ==> *prompt change*
*File:* `src/ai_engine.py`
*Current state:* The 04-21 broadsheet `.lede` contains the COMPS list AND the final `.columns` paragraph repeats it.
*Fixed state:* Prompt says "data called out in `.lede` may not appear again in body; body adds interpretation, never restates the list."

**T1.6 — Rose_stamp `recurring_bit_content` duplicated in body paragraph 1** ==> *renderer change*
*File:* `src/html_renderer.py` (`render_rose_stamp`)
*Current state:* Body opens with "FRESH OFF THE PRESS • Reddit top: …" which is the same content rendered in the `.recurring-bit` box above.
*Fixed state:* Renderer strips a body paragraph that duplicates `recurring_bit_content`. Cheaper fix than a prompt constraint and catches the failure deterministically.

**T1.7 — Third-person self-reference in own piece** ==> *prompt change + voice_lint*
*Files:* `src/personas.py`, `src/voice_lint.py`
*Current state:* Sal writes "What Sal's been tracking specifically." Several writers do this.
*Fixed state:* Per-persona VOICE RULES add: "You write in first person. Never refer to yourself by name inside your own body copy. You may sign off with your name." voice_lint adds a per-writer name-in-body check (WARN, not FAIL, to allow legitimate editor references).

---

### TIER 2 — Strong Improvements

**T2.1 — Enforce body word-count targets per issue-type** ==> *voice_lint addition*
*File:* `src/voice_lint.py`
Tuesday bodies: 100-140 words/paragraph, 4-5 paragraphs. Friday: 60-90 words, 2-3 paragraphs. Thursday: permissive. Currently only Maggie has a word-count check. WARN on drift, FAIL on 2x over budget.

**T2.2 — Throat-clearing opener ban** ==> *prompt change + voice_lint*
*Files:* `src/ai_engine.py`, `src/voice_lint.py`
Ban opening patterns: "Here's what…", "In the world of…", "It's worth noting that…", "The strongest version of the argument…". voice_lint as regex WARN. Prompt adds: "The first sentence must advance the story, not set up the frame."

**T2.3 — Ending-summary restatement pattern** ==> *prompt change*
*File:* `src/ai_engine.py`
Prompt rule: "Do not end a piece by summarizing the piece. The last sentence either turns the argument, lands a specific image, or asks the reader something concrete."

**T2.4 — Em-dash budget** ==> *voice_lint addition*
*File:* `src/voice_lint.py`
WARN any body with >3 em-dashes per paragraph on average. The dash is a crutch when it's doing the work of real sentence-level choices.

**T2.5 — Academic recurring-bit label mismatch (Wade's "THEN VS. NOW")** ==> *prompt or renderer*
*File:* `src/html_renderer.py` (`render_academic`) or prompt
"THEN VS. NOW" is the broadside label. Academic should render Wade's block as "DRIVE-BY HISTORY" or a piece-specific callout. Renderer-side default is the cleaner fix.

---

### TIER 3 — Polish

**T3.1 — SPEC.md / code drift** ==> *doc update*
*File:* `SPEC.md`
SPEC.md lists "Del Haas" as the history writer in "The Archives." `personas.py` has Wade Ostermann in "Drive-By History." Sync SPEC.md to match implementation (or decide which is canonical and migrate).

**T3.2 — Decks that restate headlines** ==> *prompt sharpener*
*File:* `src/ai_engine.py`
Prompt adds: "The deck must add information the headline doesn't. If the deck could be cut and the headline still makes sense, rewrite the deck."

**T3.3 — Generic pull quotes** ==> *prompt constraint*
*File:* `src/ai_engine.py`
"Pull quotes must be the single strongest sentence in the piece — not the most generic. If the pull quote could appear in any week's issue on any topic, rewrite it."

---

## Constraints Applied

All Tier 1–3 recommendations respect the prompt's hard constraints:
- No persona-distinctiveness reduction ==> every voice rule added makes writers *more* themselves, not less
- No visual-design simplification ==> all visual fixes restore spec, none reduce it
- No prompt-length inflation ==> additions are specific constraints, not hedge-language padding
- Body copy targets *tighter* word counts, not longer
- AI tells are replaced with voice-specific moves, not deleted

---

## Preliminary Observations Not Yet Classified
- Kelsey's 04-21 hero piece is close to elite ==> Trent Miner save percentage correlation is a genuinely reported-feeling number. Worth examining what the curator got right here and replicating the recipe.
- Maggie's editor's note on 04-21 ("Bright on the surface, something building underneath") is exactly the register intended. The closer sentence is doing real work.
