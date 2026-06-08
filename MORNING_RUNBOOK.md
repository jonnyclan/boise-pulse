# The Boise Pulse — Morning Publish Runbook

Live site: https://boise-pulse.vercel.app
Repo: https://github.com/jonnyclan/boise-pulse
Cadence: Tuesday = deep dive · Thursday = weekend guide · Friday = quick hits

---

## Your morning routine (exact order)

**1. Run the deep-research prompt in Gemini.**
Open the file for today's day:
- Tuesday → `GEMINI_DEEPRESEARCH_TUESDAY.txt`
- Thursday → `GEMINI_DEEPRESEARCH_THURSDAY.txt`
- Friday → `GEMINI_DEEPRESEARCH_FRIDAY.txt`

Update the date at the top, paste it into Gemini's **Deep Research**, let it finish
(~2–5 min), and copy everything it returns. (Each prompt now includes The Vitals,
so Gemini will gather trail/river/AQI/etc.)

**2. Come to Claude (Cowork) and say the trigger.**
Say one of: **"run tuesday"** / **"run thursday"** / **"run friday"** (or
"run the newsletter" / "today's issue"). Claude will ask for the Gemini output —
**paste it in.**

**3. Claude builds the issue.**
Claude saves your research to `research/YYYY-MM-DD.json` (story assignments + Vitals),
runs the pipeline, and reports **GO / NO-GO** with the writer table and lint results.
The rendered preview opens in your browser.

**4. (Optional) Swap a story before it writes.**
If you want a different angle, say: **"swap [beat] to [topic]"**
(e.g. "swap lifestyle to Zoo Boise World Penguin Day"). Then proceed.

**5. Review the preview.** Read it. If something's off, ask Claude to adjust and re-run.

**6. Proof the email.**
Say **"proof the email."** Claude posts it to Beehiiv as a **draft** (nothing goes
to subscribers). Open it in the Beehiiv editor and check how the inbox version looks.

**7. Send it.**
When you're happy, say **"send the newsletter"** (or "send it"). It goes to all
Beehiiv subscribers.

**8. (Optional) Update the public web archive.**
The live site only refreshes when the new issue HTML lands in the GitHub repo.
Ask Claude to **upload today's issue to GitHub** (Claude can drive your browser to
do it), or — once the full source is pushed (see "Still to do") — it's automatic.

> No Gemini today / out of time? Say **"skip gemini"** and Claude self-selects
> stories from the live wire. Lower richness, but it ships.

---

## Still to do

**Urgent (security):**
- **Revoke the old `GEMINI_API_KEY`** at Google AI Studio. It was exposed in our
  session. It's already removed from the code, so nothing breaks.

**To make the system fully automatic (one-time, from your terminal):**
- **Push the full project to GitHub.** Right now the repo holds only the static
  site, so the **CI safety-net** and the **3x/week auto-publish workflow aren't
  active yet**, and new issues must be uploaded manually (step 8). A one-time
  `git push` of the whole folder from your machine fixes all three. Ask Claude for
  the exact commands when you're ready.

**Roadmap (optional, when you want them):**
- Standardize the Gemini prompts (the richer JSON format, with Tuesday/Thursday
  versions) — sharper, more structured research.
- Quick Hits + a structured Weekend Preview (more reader utility).
- Sponsor slots / monetization — deferred until you have a subscriber base.
- Extra hardening: prompt caching, JSON-schema validation on the curator, the
  Claude GitHub code-review action, Dependabot.

**Housekeeping (whenever):**
- Delete the inert test file `research/2026-06-06.json` (it's `{}`).
- `GEMINI_CLAUDE_VETTING.md` is now historical (the auto-Gemini path was removed).

---

## Keys already configured in `.env`
`ANTHROPIC_API_KEY` (writing), `BEEHIIV_API_KEY` + `BEEHIIV_PUBLICATION_ID`
(sending), `WEB_BASE_URL=https://boise-pulse.vercel.app` (email "read full" links).
