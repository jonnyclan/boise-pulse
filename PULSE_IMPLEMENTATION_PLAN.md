# The Boise Pulse — Phased Implementation Plan

**Status: plan for approval. No code written yet.**
Date: 2026-06-06

## Locked decisions

1. **Name ==> "The Boise Pulse."** Recommendation accepted. Heartbeat logo ties in,
   passes the conversational shorthand test ("did you read the Pulse?"), avoids the
   NPR "Morning Edition" collision, no false daily-cadence promise.
2. **Emoji policy ==> Claude's call, decided:** emoji ALLOWED in structured data
   modules (The Vitals, Quick Hits); BANNED in persona body copy. `voice_lint`
   gets a carve-out so it polices columns but not the data modules.
3. **Monetization ==> deferred** until there's a subscriber base. Documented in
   Phase 4, not built.
4. **The Vitals MVP ==> Gemini-fed / manual first.** Live data fetchers are a
   later hardening step, not a launch blocker.
5. **Heartbeat SVG ==> yes**, under the masthead (lift the JSX `<polyline>`).
6. **Quick Hits voice ==> Maggie (EIC).** Confirmed.
7. **Vitals seasonal cells + placement ==> Claude's expert call** (see Phase 1).
8. **Tagline ==> proposed, pending pick:** lead candidate "Boise's vital signs,
   three mornings a week" (ties Pulse + Vitals + cadence). Alternates: "The pulse
   of the Treasure Valley" / "Boise, three mornings a week."

## Delivery & hosting (locked)

**Architecture: Vercel web showcase + Beehiiv email gateway.**

- **The web issue is the showpiece.** The pipeline already emits full standalone
  HTML to `magazines/` ==> host it on Vercel (devops-deploy skill + Vercel
  connector). Full modern CSS, no inbox constraints. This is where the "UI/UX
  expert" wow lives.
- **The email is the gateway, not the canvas.** Email clients (Gmail/Outlook/Apple
  Mail) cap email design regardless of platform, and Beehiiv additionally does NOT
  send 100% custom HTML (its Send API mirrors the block builder). So the email is
  built email-safe + scannable, and its job is to be a beautiful invitation that
  drives readers to the full web issue.
- **Beehiiv stays** for list management, deliverability, subscribe forms, and
  growth/referral tooling ==> the genuinely hard-to-DIY parts. No ESP switch
  pre-audience.
- **Deferred:** revisit a pipeline-native ESP (Resend / Postmark) only if/when
  audience + design standards justify owning the full sending stack.

## Design & UX bar (cross-cutting — the WOW requirement)

Readers must feel a UI/UX expert built this: easy on the eyes, enjoyable,
instantly scannable, sticky. Non-negotiables for every phase:

- **Two render targets, different jobs (see Delivery & hosting).** Web showcase =
  full modern CSS, the wow canvas. Email = email-safe, table-based, inline-styled,
  mobile-first gateway that *looks* like the brand and drives to the web issue.
  Design once, implement twice ==> rich web + email-safe gateway.
- **Mobile-first.** Most opens are on a phone ==> single-column, large tap targets,
  no horizontal scroll, the Vitals grid collapses to 2-up / 1-up gracefully.
- **Scannable in 3 seconds.** Status-dot color language (green/neutral/caution/
  alert) for instant parsing; strong typographic hierarchy; generous whitespace
  and consistent vertical rhythm; section labels readers can skim.
- **Restrained, intentional palette.** Navy `#0a1628` + burnt orange `#e05c2a` +
  cream `#f4efe6` (from the JSX). NOTE: reconcile with the current
  `html_renderer.py` palette ==> pick one system and apply it everywhere so the
  brand reads as deliberate, not accreted.
- **Typography:** a serif for body warmth + a mono/condensed for labels (the JSX
  pairs Georgia + Courier Prime). Confirm web-font fallbacks that survive email.

## Guardrails that hold across every phase

- **Persona distinctiveness is untouchable.** No new module wears a named
  persona's voice. The 10 personas + lint + 11-spread system stay as-is.
- **Mock-mode parity.** Every new module needs a `USE_REAL_AI=0` mock path so
  `mock run` still renders a full issue for debugging.
- **Additive, not destructive.** New modules render around the existing story
  stack; they don't replace spreads.

---

## Phase 0 — Rename to The Boise Pulse (own clean pass)

Do this first and alone so it doesn't tangle with feature commits.

**Scope:** "Morning Edition" ==> "Boise Pulse" across live files only. 72 hits / 31
files, but skip generated output (`magazines/*.html`, `*.stories.json`,
`_debug_*`). Files that actually matter:

- `src/personas.py` (12 ==> inside every writer's `prompt_voice`; highest care)
- `src/html_renderer.py` (6 ==> masthead, colophon)
- `src/ai_engine.py` (4 ==> prompt header, writer labels)
- `src/gemini_fetcher.py` (4), `src/email_sender.py` (2), `src/issue_types.py`,
  `src/ledger.py`, `src/data_sources.py`, `generate_magazine.py`,
  `pre_publish_check.py`
- Config/docs: `CLAUDE.md`, `SPEC.md`, `DESIGN.md`, `GEMINI_*` prompts, `.bat`
  files, `.env` masthead values

**Also decide:** masthead tagline + whether to add the heartbeat SVG to
`html_renderer` (the JSX has a clean `<polyline>` version to lift).

**Deliverable:** a `mock run` renders an issue branded "The Boise Pulse" end to end.
**Effort:** small, mechanical. **Risk:** low (but re-run lint after, since persona
prompts changed).

---

## Phase 1 — The Vitals (the utility moat)

The headline feature. A scannable outdoor-decision dashboard that gives readers a
reason to open even when they won't read a column. Built as a **standing module**,
not a spread/story ==> it renders above the story stack, every issue.

**1a. Schema (research JSON).** Since it's Gemini-fed, add a `vitals` block to
`research/YYYY-MM-DD.json`:
```
"vitals": {
  "cells": [
    {"label": "Foothills Trails", "icon": "...", "main": "Soft",
     "sub": "mud below 4,000 ft", "status": "caution"}, ...
  ],
  "advisory": {"level": "info|caution|alert", "text": "..."}
}
```
Status enum: `good | neutral | caution | alert` (drives the dot color, lifted from
the JSX `statusColors`). Cells rotate by season (winter: Bogus + inversion;
spring: trail mud + pollen; summer: AQI + river; fall: cottonwoods + hunting) but
the schema shape is constant.

**1b. Gemini prompt.** Add a Vitals section to `GEMINI_DEEPRESEARCH_*.txt` asking
it to return: temp, foothills/trail status (Ridge-to-Rivers), Boise River cfs +
temp (USGS gauge), AQI, pollen, Bogus (in season), sunrise/sunset, and a one-line
advisory. You paste, Claude parses into the `vitals` block alongside the existing
beats.

**1c. Render + placement (Claude's call).** New `render_vitals()` in
`html_renderer.py` ==> the navy grid with status dots + advisory bar.
**Placement: directly under the masthead/heartbeat, BEFORE Maggie's editor note.**
Rationale: it's a deliberate brand moment ==> "The Pulse" opens with the city's
**Vitals**, the heartbeat line flowing straight into the vital signs. It's also the
scannable hook the WOW mandate wants readers to hit first. Order becomes:
masthead+heartbeat ==> The Vitals ==> Maggie's "Today's Edition" ==> story spreads.

**Seasonal cells (Claude's call) ==> fixed 6-cell grid, contents rotate by season.**
Two constant anchors + four seasonal:
- **Always:** Weather (temp + sky) · Daylight (sunrise/sunset).
- **Winter (Dec-Feb):** Bogus Basin (snow/lifts) · Inversion + Air Quality · Roads/
  passes.
- **Spring (Mar-May):** Foothills Trails (mud) · Boise River (cfs + temp) · Pollen.
- **Summer (Jun-Aug):** Air Quality / smoke · Boise River (float + temp) · Fire/UV.
- **Fall (Sep-Nov):** Foothills Trails · Cottonwoods / foliage · First-frost watch.
Shape is identical season to season ==> only the four seasonal cells swap, so each
issue's Vitals takes minutes once the format exists.

**1d. Lint carve-out.** Teach `voice_lint` that the vitals block is emoji-legal and
not subject to persona checks; keep persona body copy emoji-free.

**1e. Mock path.** A deterministic mock Vitals built from whatever `weather` data
already exists, so `mock run` renders it.

**Deliverable:** every issue opens with a 3-second-scannable Vitals module, fed by
your morning Gemini run. **Effort:** medium. **Risk:** low to personas (it's data);
main work is render + schema. **Confidence it's the right first move:** high.

*Later hardening (not now):* replace manual/Gemini entry with live fetchers in
`data_sources.py` ==> USGS river gauge, AirNow AQI, Ridge-to-Rivers, Bogus feed.

---

## Phase 2 — Growth scaffolding (cheap, high ROI)

Render/schema additions, near-zero voice risk, direct help to deliverability and
organic growth.

- **"In today's Pulse" TOC** ==> auto-generated from the issue's headlines, rendered
  under the masthead.
- **Reply nudge + share line** ==> footer CTAs. Reply prompts help inbox placement;
  the share line is the forward engine. Issue-level schema fields.
- **Social teaser (pre-CTA)** ==> Claude generates one teaser line for tomorrow's
  hook during curation and writes it to a small `teasers/YYYY-MM-DD.txt` output you
  paste into IG/Nextdoor the night before. No new platform integration.

**Deliverable:** issues carry a TOC, a reply prompt, a share line, and a
copy-paste social teaser file. **Effort:** small-medium. **Risk:** low.

---

## Phase 3 — Utility breadth

Adds the "indispensable tool" quality the notes correctly flagged.

- **Quick Hits** ==> a 5-6 item scannable roundup of "other news" that doesn't earn
  a full column. Sourced from the news buckets already fetched in `data_sources`. **Voice owner: Maggie (EIC) or a neutral "Newsroom" byline ==>
  NOT a persona.** New render module; emoji-legal. Schema:
  `[{emoji, bold, rest}]`.
- **Weekend Preview** ==> upgrade the Thursday `weekend_guide` issue with a
  structured day-by-day events list + a single confident "Pick of the Weekend."
  Schema + render module; fits the existing Thursday slot logic.

**Deliverable:** broader coverage per issue; Thursday gains a real backbone.
**Effort:** medium. **Risk:** low-medium (needs the Quick Hits voice decision
confirmed).

---

## Phase 4 — Monetization (documented, deferred)

Build when a subscriber base justifies a sales motion. Captured now so the schema
is designed with the right guardrail from day one.

- Sponsor surfaces: Together With header, Vitals seasonal sponsor, sponsored Find.
- **Hard rule:** sponsored modules use a **neutral/editor voice + explicit
  disclosure**, never a named persona's voice. Protects the independence that makes
  Nina, Dani, et al. credible.
- Schema: `sponsor` blocks with `disclosure` required; render with a visible
  "Sponsored" / "paid for the slot, the opinion is ours" label.

**Deliverable:** none yet ==> spec only. **Trigger:** revisit at first meaningful
subscriber milestone.

---

## Suggested sequence & rationale

1. **Phase 0 rename** ==> clears the brand decision out of the way, isolated commit.
2. **Phase 1 Vitals** ==> highest reader-value, lowest risk to the persona system,
   and you already run Gemini each morning so the MVP path is short.
3. **Phase 2 growth scaffolding** ==> cheap, compounding, helps deliverability.
4. **Phase 3 utility breadth** ==> after Vitals proves the data-module pattern.
5. **Phase 4 monetization** ==> deferred per decision.

## Open items before building

All resolved except one:
- **Tagline** ==> pick from the three candidates (lead: "Boise's vital signs, three
  mornings a week"). Not a blocker for Phase 0; can drop in during render work.

Everything else is locked: name, heartbeat SVG (yes), Quick Hits voice (Maggie),
Vitals placement (under masthead, before Maggie) and seasonal cells (above),
emoji policy, monetization deferred, Gemini-fed Vitals, and the Design & UX bar.
