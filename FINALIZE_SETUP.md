# Finalize Setup — two one-time actions

Both need *your* logged-in accounts (Google, GitHub), so they run on your machine/browser, not from Claude's sandbox. Each is ~3 minutes. Verified safe beforehand: the leaked key is already out of all files, and `.env` (your real secrets) is gitignored so the push can't re-leak it.

---

## 1. Revoke the old exposed GEMINI_API_KEY (Google AI Studio)

The key is already removed from the code, so this only invalidates the leaked value. Nothing in the pipeline depends on it anymore.

1. Go to **https://aistudio.google.com/app/apikey** (sign in as your Google account).
2. Find the API key that was active during our earlier session (the GEMINI one).
3. Click the **⋮ / Delete** (trash) icon next to it → confirm **Delete**.
4. Done. If you ever wire Gemini back into the automated path, generate a **new** key and put it in `.env` only (never in a committed file).

> Note: today's workflow uses Gemini *manually* (you paste research in), so there's no Gemini key in the automation at all. Deleting this key changes nothing about your daily run.

---

## 2. One-time push of the full project to GitHub

Right now `github.com/jonnyclan/boise-pulse` holds only the static site, so the CI safety-net and the 3x/week auto-generate workflow aren't active. This folder on your Desktop is your full local copy but isn't a git repo yet. These commands make the full project the repo and turn both workflows on.

### 2a. First, add the GitHub Actions secrets (so auto-generate can run)
In your browser: **GitHub → your `boise-pulse` repo → Settings → Secrets and variables → Actions → New repository secret.** Add these four (values are in your local `.env`):

- `ANTHROPIC_API_KEY`
- `YOUTUBE_API_KEY`
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`

(`ci.yml` needs none. Beehiiv keys are **not** needed here — the workflow generates and commits the issue; it never auto-sends.)

### 2b. Then push, from a terminal in this folder
Open a terminal in `C:\Users\jonny\Desktop\Dunzo\morning-edition` and run:

```bash
git init
git branch -M main
git remote add origin https://github.com/jonnyclan/boise-pulse.git
git add .
git commit -m "Full project: pipeline, personas, workflows, guardrails"
git push -u origin main --force
```

Notes:
- `--force` is intentional: it replaces the static-only repo with the full project (which still includes the rendered site in `magazines/`, so Vercel keeps deploying).
- `.env` will **not** be uploaded — it's gitignored. Confirm by running `git status` before the commit and checking `.env` is not listed.
- If `git push` asks for credentials, use your GitHub username + a **Personal Access Token** (Settings → Developer settings → Tokens), not your password.

### 2c. Confirm both workflows turned on
After the push: **GitHub repo → Actions tab.** You should see `ci` run immediately on the push (green check = safety-net live). `morning-edition` will then fire on its schedule (Tue/Thu/Fri, 7 a.m. MT). To test it now without waiting, open **Actions → morning-edition → Run workflow** (the `workflow_dispatch` button).

---

## After this is done
- The live site auto-updates whenever an issue is committed (manual run *or* the scheduled workflow), so you can drop the manual "upload to GitHub" step from your morning routine.
- CI runs on every push/PR — a broken edit (syntax, schema, email-unsafe CSS) can't reach `main`.
- You still trigger the Beehiiv **send** yourself each morning. That stays manual on purpose.
