# The Boise Morning Edition — Quality Audit Prompt

## HOW TO USE THIS PROMPT

**Use this in a Claude Code session** — either open a new terminal in the `morning-edition/` project folder and run `claude`, or paste it into an existing Claude Code session where this project is already loaded. Do NOT use this in a regular Claude chat — Claude Code can read all the files, run the pipeline, and edit the source directly.

**Quick start:**
```bash
cd ~/path/to/morning-edition
claude
# then paste everything below the divider
```

---
---

## THE PROMPT (paste everything below this line)

You are acting as an editorial quality director with deep expertise in world-class newsletter and digital magazine production. Your task is to audit the Boise Morning Edition against the standards of the best newsletters and editorial publications in the world, identify specific improvements, collaborate with me to prioritize them, and then implement all agreed changes directly in the codebase.

---

### PHASE 1 — INGEST THE PROJECT

Read these files in full before doing anything else:
- `SPEC.md`
- `DESIGN.md`
- `src/personas.py`
- `src/ai_engine.py`
- `src/html_renderer.py`
- `src/issue_types.py`
- `src/voice_lint.py`
- `magazines/2026-04-23.html` (or the most recent issue)
- `magazines/2026-04-21.html` (second most recent, for pattern comparison)

Do not summarize what you read. Just confirm you've read them and move to Phase 2.

---

### PHASE 2 — AUDIT AGAINST WORLD-CLASS STANDARDS

Evaluate the current output across the following 8 dimensions. For each, score it 1–10 and write 2–4 sentences of honest diagnosis. Use specific quotes or examples from the actual HTML output where possible.

Compare against the editorial standard of publications like: The Information, Axios, Stratechery, The Hustle, Morning Brew, The Economist, Puck News, and The New Yorker — depending on which is most relevant to each dimension.

**Dimension 1: Voice Authenticity**
- Do the 8 writers genuinely sound like different people?
- Do any writers sound like AI wrote them (hedging language, over-explaining, unearned enthusiasm, over-using the writer's own name or phrases like "as Kelsey often says")?
- Are recurring bits (The Lede, Dex's Drop, Nina's Table, etc.) actually appearing and landing well?

**Dimension 2: Headline & Deck Quality**
- Are headlines specific, surprising, and free of jargon?
- Do decks do real work (add information) rather than just restating the headline?
- Compare against Morning Brew / The Hustle standard: punchy, human, earns the click.

**Dimension 3: Body Copy Quality**
- Paragraph length discipline: are bodies too long, too short, or just right?
- Is the writing transformative (editorial voice, original observation, real point of view) or does it feel like a press release summary?
- Overuse of writer names in body copy (e.g., "Kelsey notes that..." — this is a red flag)
- Sentence-level AI tells: passive voice, vague superlatives ("significant," "notable," "exciting"), throat-clearing intros ("In the world of Boise real estate...")

**Dimension 4: Structural Discipline**
- Does each spread have a clear job (inform / amuse / provoke / anchor)?
- Is the 10-spread sequence well-paced, or does it feel like 10 separate unconnected pieces?
- Are the issue types (Deep Dive vs. Weekend Guide vs. Quick Hits) actually producing noticeably different reading experiences?

**Dimension 5: Visual Design Fidelity**
- Are the 10 spread types rendering per spec? Check: correct fonts, correct palette, correct typographic hierarchy.
- Are there any renders that feel underdeveloped, broken at certain viewport widths, or missing key design elements from DESIGN.md?
- Is the masthead and footer landing with the premium feel intended?

**Dimension 6: Data Source Integration Quality**
- Do the stories feel genuinely local and timely, or generic?
- Is Reddit r/Boise voice/flavor making it into the trending pieces?
- Does Pete's weather column actually reflect the specific Boise forecast data, or does it feel generic?
- Does Del's "On This Day" content feel legitimately surprising and well-chosen?

**Dimension 7: The "Too AI" Problem**
- Identify every specific pattern that makes the content feel AI-generated rather than human-written. Examples to look for:
  - Referring to the writer in the third person within their own piece
  - Sentences that begin with "It's worth noting that..."
  - Endings that summarize what was just said
  - Fake enthusiasm ("This is a big deal for Boise!")
  - Any writer "signing off" or "wrapping up"
  - Overuse of em-dashes as a crutch
  - Pull quotes that are just the most generic sentence in the piece

**Dimension 8: The "Would I Actually Read This?" Test**
- Read the two issues cold, as a Boise resident who doesn't know how this was made. What grabs you? What makes you want to scroll past?
- What's the single biggest thing killing the reading experience?

---

### PHASE 3 — PRESENT FINDINGS

Present your findings as a prioritized list of improvements, grouped by:

**TIER 1 — Fix These First** (highest impact, should be done now)
**TIER 2 — Strong Improvements** (meaningful quality lift)
**TIER 3 — Polish** (nice to have, lower effort)

For each item, specify:
- Which file(s) need to change
- Whether it's a **prompt change** (fix to the AI curation prompt in `ai_engine.py`), a **persona change** (fix to `personas.py`), a **renderer change** (fix to `html_renderer.py`), or a **logic change** (elsewhere)
- A concrete example of what "fixed" looks like vs. the current state

---

### PHASE 4 — COLLABORATE BEFORE CODING

Before making any changes, ask me the following as a structured question:

> "Here are the improvements I've identified. Please tell me which ones to implement:
> 
> [Show the tiered list]
> 
> Would you like me to: (a) implement all Tier 1 items now, (b) implement specific items you choose, or (c) walk through each one so you can decide? Also — are there any findings you disagree with or want to approach differently?"

Wait for my response before writing any code.

---

### PHASE 5 — IMPLEMENT

Once I confirm what to implement:

1. Make all agreed changes to the relevant source files.
2. After changes, run `python3 generate_magazine.py` with mock mode (set `USE_REAL_AI=false` in `.env` temporarily if needed) to generate a test issue.
3. Show me a diff summary of every file changed.
4. Point out one or two specific before/after examples in the output where you can demonstrate the quality improvement concretely.

Then ask: "Want me to also tackle the Tier 2 items, or run this with real AI first to see how it lands?"

---

### IMPORTANT CONSTRAINTS

- Never reduce the distinctiveness of the writer personas to make them "safer" — bolder is better.
- Never simplify the visual design — if something is broken, fix it to spec, don't reduce it.
- Prompt improvements should ADD specificity and constraint, not add more length.
- All body copy improvements should aim for a tighter word count, not longer. The target is "every sentence earns its place."
- When fixing "AI tells," replace them with the specific voice move that character would make — don't just delete.
