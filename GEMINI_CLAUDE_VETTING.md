# Gemini + Claude Pipeline — Vetting & Vitals Wiring

Date: 2026-06-06. Scope: wire the live Vitals path end-to-end and vet every
Gemini/Claude moving part (manual + automated) for consistency.

## What's now wired for The Vitals (live path complete)

The Vitals data flows from research → render through one consistent schema:
`research["vitals"] = {cells:[{icon,label,main,sub,status}…6], advisory:{level,text}}`.

- **`src/vitals.py`** — Gemini-fed when present, else a season-aware mock from
  NWS weather. Verified: passthrough, summer + winter mocks (6 cells), all
  statuses valid.
- **`render_vitals()`** + orchestrator wiring — verified the research block
  overrides the mock end-to-end (sentinel test passed).
- **Manual prompts** — Vitals research added to **all four**: the rich
  `GEMINI_PROMPT_FRIDAY.txt` (JSON `vitals` block + BEAT 6 instructions) and the
  prose `GEMINI_DEEPRESEARCH_{FRIDAY,TUESDAY,THURSDAY}.txt` (BEAT 0 section).
- **Automated path** (`run_gemini.py`) — now writes a `vitals` block to the
  research file (season mock for now — see decision #2).
- **`CLAUDE.md`** — documents the **real** file schema (`assignments` wrapper +
  `vitals` + `gemini_news`) and the Vitals block shape; the morning-workflow
  parse step now calls out saving Vitals.

Full pipeline compiles and imports clean.

## Drift found & fixed

1. **Schema doc vs. reality.** CLAUDE.md described per-beat keys at the top level,
   but the pipeline actually reads `research["assignments"]` (+ `gemini_news`).
   Fixed — CLAUDE.md now documents the real wrapper. (Confidence: high.)
2. **Vitals had no source.** The dashboard existed but nothing fed it on the live
   path. Fixed — every prompt now researches it and the parse/runner save it.

## Decisions for you (these I did NOT decide unilaterally)

1. **Two prompt generations exist.** The older prose `GEMINI_DEEPRESEARCH_*.txt`
   (all 3 days, what CLAUDE.md tells you to open) **and** the newer, far more
   rigorous `GEMINI_PROMPT_FRIDAY.txt` (raw-JSON output, zero-hallucination
   fields that map 1:1 to the writer dossiers). Right now only **Friday** has the
   rich JSON version. **Recommendation (moderate-high):** standardize on the rich
   JSON approach and create `GEMINI_PROMPT_TUESDAY/THURSDAY.txt`, then point
   CLAUDE.md at them. It removes the lossy "Claude re-parses prose into JSON" step.
   I added Vitals to *both* generations so nothing's stranded until you choose.

2. **Automated Vitals is a mock, not live.** `run_gemini.py` writes a season-mock
   Vitals because `gemini_fetcher.py` doesn't yet fetch trail/river/AQI/Bogus.
   The **manual** path gets real numbers (the prompt asks for them). Building live
   fetchers (USGS river gauge, AirNow AQI, Ridge-to-Rivers, Bogus) into
   `gemini_fetcher` is the remaining hardening step — matches the plan's "live
   data fetchers later."

3. **Stray test file.** I created `research/2026-06-06.json` to verify the live
   path; the sandbox can't delete files in your folder, so I neutralized it to
   `{}` (behaves like "no file"). **You can delete it** — or leave it; it's inert.

## Vet scope (honest)

Verified by execution: `vitals.py`, `render_vitals`, orchestrator wiring, all
module compiles/imports, the research→render override. Reviewed at integration
points: `gemini_fetcher.py` automated assign path (its live-Vitals fetch is the
known gap in #2). Everything needed for the **manual** morning workflow + the web
render is ready and consistent.
