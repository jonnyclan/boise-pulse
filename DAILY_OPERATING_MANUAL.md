# The Boise Pulse — 7-Day Operating Manual

**How to use this:** This is your every-morning script. Publish days (Tue / Thu / Fri) run the full **Master Sequence** below. Non-publish days (Mon / Wed / Sat / Sun) run a short prep/maintenance routine. Steps in **bold-quotes** are exactly what you type to Claude. `Monospace` is a file or command. Anything in `[brackets]` in your draft copy is an unverified fact that must be filled or cut before send.

Cadence: **Tuesday** = The Deep Dive (6 stories) · **Thursday** = The Weekend Guide (8 stories) · **Friday** = Quick Hits (5 stories).

---

## The week at a glance

| Day | Type | What you do (≈ time) |
|---|---|---|
| **Mon** | Prep | Review last week's numbers; pre-stage Tuesday's Gemini research the night before (10 min) |
| **Tue** | PUBLISH | Master Sequence — Deep Dive (20–30 min) |
| **Wed** | Prep | Post-Tuesday check; gather **weekend events** for Thursday (10–15 min) |
| **Thu** | PUBLISH | Master Sequence — Weekend Guide (20–30 min) |
| **Fri** | PUBLISH | Master Sequence — Quick Hits (15–20 min) |
| **Sat** | Rest | Optional idea-capture only |
| **Sun** | Retro | Weekly retro + plan the week + backup (15–20 min) |

---

## THE MASTER SEQUENCE (Tue / Thu / Fri)

Run these in order. Same nine steps every publish day; only the Gemini file changes.

### Step 1 — Run Gemini Deep Research
Open today's prompt file:
- Tuesday → `GEMINI_DEEPRESEARCH_TUESDAY.txt`
- Thursday → `GEMINI_DEEPRESEARCH_THURSDAY.txt`
- Friday → `GEMINI_DEEPRESEARCH_FRIDAY.txt`

Update the date on the `TODAY:` line at the top. Select all, copy. Open Gemini → switch to **Deep Research** mode → paste → run. Wait ~2–5 minutes for the full result.

### Step 2 — Copy everything Gemini returns
Copy the **entire** output, including the per-beat **Fact Ledger** and **Editor's Checklist** at the bottom of each beat. Those tables are what let Claude print only verified names, dates, and numbers — don't trim them off.

### Step 3 — Trigger Claude
In Claude (Cowork), type: **"run tuesday"** (or **"run thursday"** / **"run friday"**). Claude will reply: *"Paste your Gemini Deep Research output and I'll take it from there."*

### Step 4 — Paste the Gemini output
Paste it in. Claude then: parses it into `research/YYYY-MM-DD.json` (story assignments + The Vitals), runs `python pre_publish_check.py --preview`, and reports **GO / NO-GO**, the writer-assignment table, and the voice-lint results. The rendered preview opens in your browser.

### Step 5 — (Optional) Swap a story *before* it writes
If an angle is wrong, say: **"swap [beat] to [topic]"** (e.g. *"swap lifestyle to Zoo Boise World Penguin Day"*). Claude updates that assignment and re-runs. Do this now, not after.

### Step 6 — Resolve the verdict
- **GO** → continue.
- **NO-GO** → Claude prints the offending FAIL. Fix it (or tell Claude to) and re-run. The four FAIL causes and their fixes are in the troubleshooting table below.
- **Scan the WARNs.** The proper-noun-floor WARNs are your aggregation-drift alarm: *"Dani: civic floor"*, *"Sal: place floor"*, *"Dex: named-act floor"*, *"Nina: price floor"* each mean a writer went generic. If you see one, say **"enrich [writer] — they're missing their proper-noun hammer"** before shipping. WARNs don't block, but they're the difference between unique and wire-grade.

### Step 7 — The bracket sweep (do not skip)
Read the preview and search for any `[ ]` brackets. Those are facts Gemini could **not** verify (from the Fact Ledger). For each one: confirm it against Gemini's Fact Ledger VERIFIED rows and tell Claude to fill it, or say **"cut the unverified bracket in [writer]'s piece."** **Never send an issue containing brackets.**

### Step 8 — Proof the email
Say **"proof the email."** Claude posts it to Beehiiv as a **draft** (nothing goes out). Open it in Beehiiv and check the inbox render, the **subject line**, and the **preview text** — ideally on your phone, since most readers are on mobile.

### Step 9 — Send, archive, log
- Send: **"send it"** (or *"send the newsletter"*) → goes to all subscribers.
- Archive the web copy: **"upload today's issue to GitHub"** (until auto-publish is wired, the live site only updates when the HTML lands in the repo).
- Log it: **"capture this session"** → files the edition to your second brain for the record and for next week's retro.

---

## Day-specific notes

**Tuesday — Deep Dive.** Substance day. Pool is sports / history / editorial / real-estate. Bodies run long (100–140 words). At most **one** non-pool writer (weather/food/arts/etc.) may appear, and only for genuinely big news. If Claude's draft has two non-pool writers, that's an over-budget override — tell Claude to drop the weaker one.

**Thursday — Weekend Guide.** Event-forward, 8 stories. This is the one Gemini is weakest on if local events aren't well-indexed, so lean on the **events shortlist you gathered Wednesday** (Step W below) and swap them in at Step 5. Weather is mandatory and gets early placement because it changes weekend plans.

**Friday — Quick Hits.** Short and fast (60–90 word bodies), aimed at the commute. Sports = previews not recaps. Weather is mandatory. The closer (broadside) should send readers into the weekend with something quotable. If news broke after Thursday's send, Friday is its home.

---

## Non-publish-day routines

**Monday (prep Tuesday).**
1. Open Beehiiv analytics. Note last week's three sends: open rate, click rate, which stories got clicks. Carry the winners' *type* into this week's selection.
2. Decide any Tuesday angles/swaps in advance.
3. **Monday evening:** pre-run the Tuesday Gemini Deep Research and save the output in a note. Tuesday morning then becomes paste-and-go — this is the single biggest reliability upgrade, because it removes the "ran out of time → skip gemini → thin issue" failure mode.
4. Confirm `.env` keys are live (ANTHROPIC, BEEHIIV). If a key died, you want to know Monday, not 6 a.m. Tuesday.

**Wednesday (prep Thursday — the events step, "Step W").**
1. Did Tuesday land? Skim any reader replies (reply-gold feeds local flavor).
2. Build a **weekend events shortlist** (5–10 items): shows, markets, games, festivals, openings, First Thursday. Sources: venue calendars, Boise Weekly, Visit Boise, BoiseDev, the venues your writers already cover. Keep it in a note to swap into Thursday's issue.
3. Wednesday evening: pre-run Thursday's Gemini research.

**Saturday (rest).** No publish, no prep required. Optional only: jot any story idea you stumble on into a running ideas note.

**Sunday (weekly retro + plan).**
1. **Lint-trend retro:** ask Claude **"show me the recurring voice-lint WARNs across this week's three issues."** A writer who trips the same proper-noun-floor WARN every issue is drifting toward generic — that's your signal to tune their persona.
2. **Performance retro:** which stories/writers drove opens and clicks this week? Plan next week to do more of that.
3. **Plan the week:** any themes, features, or known events (holidays, BSU schedule, council agendas).
4. **Back up:** make sure the week's issues are pushed to GitHub.
5. **"capture this session"** to close the loop.

---

## Pre-SEND quality gate (the 6 checks before "send it")

Run this every publish day before Step 9. If any fails, fix before sending.

1. **Verdict is GO** (0 FAIL).
2. **No brackets** anywhere in the copy (Step 7 done).
3. **Every writer's signature line is present** — MOOD OF THE SKY (Pete), Nina's Table, Dex's Drop, THE LEDE (Kelsey), THE COMPS (Sal), DRIVE-BY + "tell at dinner" (Wade), FRESH OFF THE PRESS (Jess), HAYLEY'S RATIO (Hayley), measure-the-thing close (Dani).
4. **No proper-noun-floor WARN left unaddressed** on a fact writer (Dani / Sal / Dex / Nina).
5. **The Vitals dashboard makes sense** for today's actual season and weather (glance at it).
6. **Subject + preview text** are intentional and specific — not a generic restatement of the masthead.

---

## NO-GO troubleshooting (quick reference)

| The pipeline says… | What it means | Your move |
|---|---|---|
| **source-beat mismatch FAIL** | A writer is sourced only to a foreign-beat / placeholder institution (e.g. a music piece sourced to "Boise State University") | **"fix [writer]'s source — it's a placeholder"**; give the real venue/agency, or pull the correct Fact-Ledger source |
| **writer duplication FAIL** | Same writer used twice in one issue | **"swap one of the duplicate [writer] slots to a pool writer"** |
| **signature miss** | A persona dropped its signature line | **"[writer] is missing their signature line — add it back"** |
| **wordcount > 2x budget FAIL** | A paragraph ran way over the day's length target | **"tighten [writer]'s long paragraph to the [day] target"** |
| **proper-noun floor WARN** | A fact writer went generic (no official/place/act/price) | **"enrich [writer] — they're missing their proper-noun hammer"** |
| **over-budget override** (2 non-pool writers on Tuesday) | Too many off-pool writers earned a slot | **"drop the weaker non-pool writer and backfill with a pool writer"** |

> **No Gemini today / out of time?** Say **"skip gemini"** and Claude self-selects from the live wire. It ships, but richness drops and the Fact Ledger protection is gone — treat it as the emergency option, not the norm. (This is exactly what pre-staging research the night before prevents.)

---

## Recommended upgrades you may not have considered

These are the habits that turn "it goes out 3x a week" into "readers can't get it anywhere else."

1. **Pre-stage research the night before.** Biggest single reliability win. Removes the morning time-crunch and the thin "skip gemini" fallback.
2. **Hold a consistent send time.** Pick one window (e.g. 6:30 a.m. MT) and keep it. Readers build a habit and deliverability improves with predictable volume.
3. **Treat floor-WARNs as a feature, not noise.** They're your early-warning system that a writer is sliding toward AI-aggregation — the thing the whole brand sells against.
4. **Keep a story ledger** (which landmark Wade used, which player Kelsey featured, which subdivision Sal covered). Prevents repeats and keeps each edition genuinely unique across the month. Ask Claude to maintain it.
5. **Build a 2-piece evergreen buffer.** Pre-research one Wade drive-by and one Sal comp piece you can drop in on a dead-news day, so you never ship thin.
6. **Mine reader replies.** Replies to the newsletter are pure local authority — feed them into Jess's community flavor or Maggie's editor's note.
7. **Craft subject + preview deliberately.** The inbox line decides the open. It should promise the single most specific, local thing in the issue.
8. **Mobile-proof every send** (Step 8). Most reads happen on a phone.
9. **Weekly persona-drift check** (Sunday retro #1). Catches a voice going stale before readers do.
10. **Back up weekly.** A `git push` of the week's issues keeps the archive and the live site honest.

---

*Last updated for the Fact-Ledger + voice-lint guardrail release. The source-beat and proper-noun-floor checks now run automatically inside `pre_publish_check.py`; you don't invoke them — they surface in the GO/NO-GO report.*
