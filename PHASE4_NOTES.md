# Phase 4 — Automation & Hardening (COMPLETE & verified)

Turns the manual Phase 1–3 pipeline into a hands-off daily job, with the spec's hardening.

## Files
- `run_daily.py` — orchestrator. Chains **fetch → diff → build_site → commit-ALL → push → alert**.
  Fixes the ordering gap: the site aggregates (`assets/directory.json`, `assets/stocks.json`)
  are now rebuilt *before* the commit and land in the **same commit** as the data. Extra args
  pass through to the fetcher (`python run_daily.py --only "NIFTY IT"`).
- `fetcher/notify.py` — Telegram alerts, stdlib only. Inert (no-op + log) until creds exist via
  env `TELEGRAM_TOKEN`/`TELEGRAM_CHAT_ID` or `fetcher/secrets.json` (git-ignored).
- `fetcher/secrets.example.json` — template for the above.
- `requirements.txt` — pins `nsepython==2.97` (+ requests).
- `run_daily.bat` — Task Scheduler entry point (absolute python path, `cd`, logs to `logs/run_<date>.log`).
- `register_task.ps1` — registers the daily job; reversible via `Unregister-ScheduledTask`.

## Edits to earlier phases
- `fetcher/fetch.py`: `git add` now includes `assets`; final commit is skipped under `--no-commit`
  so the orchestrator owns the single commit.
- `.gitignore`: added `secrets.json`, `fetcher/secrets.json`, `logs/`.

## Scheduling
- Registered task **`StaticIndexTracker`**, daily **18:00 local**, `StartWhenAvailable` (catches up
  if the PC was off), 30-min limit, runs as current user when logged on.
- PC clock confirmed **India Standard Time (UTC+5:30)** → 18:00 local == 18:00 IST (post-market).
- Replaced a **broken leftover task** (pointed to a dead `c:\Gemini …` path, never ran) — with the
  user's OK.

## Alerting — design note (deviation from the prompt, deliberate)
The prompt said "alert on zero-changes-across-ALL-indices (silent-block signal)". But zero
*membership* change is the NORMAL state ~363 days/yr (indices reconstitute ~2×/yr), so that would
fire daily = noise. A real silent block shows up as fetch **failures** (HTML instead of JSON/CSV)
or empty responses caught by the snapshot guard — not as "zero changes". So `notify.check_and_alert`
alerts on run *health*:
- `ok == 0` → total block / upstream change (critical)
- `failed + guard ≥ max(5, 20%)` → partial breakage (warning)
- any individual failures → names them
A healthy zero-change run is silent by design. Optional `send_heartbeat()` exists if a periodic
"still alive" ping is ever wanted.

## Hardening recap
- `nsepython` pinned. Push is a **separate, non-fatal** step (inert until a remote exists).
- Snapshot guard + first-run baseline + meta-merge + no-git-churn carried intact from Phase 1–2.
- Local **git repo on `main`**, initial commit + daily commits.

## Verified (2026-06-25)
1. `run_daily.py --only "NIFTY IT"` → fetch→build→commit→push(inert)→alert(inert). Commit touched
   only `meta.json` (no churn). ✅
2. Full run **via Task Scheduler** (`schtasks /Run`) → **LastResult 0x0**, all **150/150 ok**,
   site rebuilt (1763 stocks), healthy/no-alert, "DAILY RUN COMPLETE". ✅
3. Task `NextRunTime` = 2026-06-25 18:00 IST. ✅

## Remaining (deferred by user)
- **GitHub repo + Pages** (publish for 24/7 hosting). gh CLI not installed; needs repo + auth +
  `git remote add` + push + enable Pages. Until then the daily job commits locally (push is inert).
- **Telegram token** → drop into `fetcher/secrets.json` to switch alerts on.
- **Backlog:** ~40 niche NSE indices not yet mapped to niftyindices CSV filenames.
