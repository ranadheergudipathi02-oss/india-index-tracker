# Phase 3 — Static Frontend (COMPLETE & verified)

A dependency-free static site (plain HTML/JS/CSS) served from the repo root, reading the
JSON the fetcher produces. Designed for GitHub Pages (serve from `main` root).

## Files
- `index.html` — shell (header stats + stock search + `<main>`).
- `assets/style.css` — styling.
- `assets/app.js` — vanilla SPA, hash-routed (`#/`, `#changes`, `#i/<id>`, `#s/<isin>`).
- `web/build_site.py` — generates the two aggregates the client can't cheaply derive:
  - `assets/directory.json` — categorized index directory (exchange · {Broad/Sectoral/Thematic/Strategy}, count, file, last_changed)
  - `assets/stocks.json` — reverse index: stock (by ISIN) → indices it belongs to (1763 stocks)

## Data flow (no duplication)
The site reads the fetcher's files in place: `meta.json` (stats), `changes.jsonl` (history),
`current/<slug>.json` (members, fetched on index click). `build_site.py` derives the two
aggregates from those after each fetch. Nothing is copied.

## Features (all verified in-browser)
- **Directory** — indices grouped by exchange → category, each card showing constituent
  count + last-changed/baselined date.
- **Index detail** — constituents table (#, symbol, company, ISIN) + per-index change history.
- **Recent changes** — global add/remove feed (currently the honest "baseline just
  established" empty state + the 150-index baseline note).
- **Stock lookup** — type a symbol/name/ISIN → which indices contain it, grouped by exchange.
  Cross-exchange via ISIN: e.g. Reliance (INE002A01018) shows in 19 NSE + 22 BSE indices,
  with both the NSE ticker (RELIANCE) and BSE scrip code (500325).

## Run / preview
```
python -m http.server 8770 --directory <repo>      # then open http://localhost:8770/
python web/build_site.py                            # refresh directory.json + stocks.json
```

## GitHub Pages
Serve from `main` branch root. `index.html`, `assets/`, `current/`, `changes.jsonl`,
`meta.json` are all under root and web-accessible. (`fetcher/`, `calibration/`, `phase0/`,
`*.md` are served too but simply unreferenced.)

## Utility added
- `fetcher/reset_baseline.py` — rewrite `changes.jsonl` to a pristine baseline matching
  `current/` (used to discard the tamper-test entry; handy after manual data fixes).

## Next
- **Phase 4** — Task Scheduler ~18:00 IST batch (fetch → diff → **build_site.py** → commit →
  push), Telegram alerts on any fetch failure or zero-changes-across-ALL (silent-block
  signal), add the GitHub remote + enable push, pin nsepython.
- **Backlog** — 40 niche NSE indices (filenames TBD via niftyindices page crawl).
