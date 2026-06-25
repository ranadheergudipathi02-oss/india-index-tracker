# Phase 1 — Fetcher (COMPLETE & verified)

Built the fetcher, calibrated the index→source maps, ran it twice end-to-end.

## Result
- **150 indices fetched OK** (77 NSE + 73 BSE), **13,450 membership rows**, ~100–150s/run.
- Run 1: 149/150 (one transient NSE SPA-shell blip on NIFTY 100). Run 2: **150/150**.
- Idempotent: re-running overwrites `current/` cleanly and populates `prev_count`.

## Layout
```
static-index-tracker/
  calibration/            # one-time map builders (kept for re-calibration)
    maps/
      nse_index_map.json  # 77 NSE indices -> niftyindices CSV url (+ 40 unresolved backlog)
      bse_index_map.json  # 75 BSE indices -> code + iname (3 USD Dollex flagged out-of-scope)
  fetcher/
    config.py             # paths, headers, throttle/retry, snapshot-guard threshold
    fetch.py              # main loop  (python fetcher/fetch.py)
  current/                # OUTPUT: <exchange>_<slug>.json per index, current constituents
  meta.json               # OUTPUT: last_run (IST), duration, per-index status, summary
  phase0/ , PHASE0_FINDINGS.md
```

## Data sources (verified)
- **NSE** constituents: `niftyindices.com/IndexConstituent/ind_<slug>list.csv` (official, no Akamai).
- **BSE** constituents: `api.bseindia.com/BseIndiaAPI/api/NS_IndexWeight_SPDJ_ng/w?iname=<iname>`
  (needs Origin/Referer = bseindia.com). Index codes/inames from `IndexMasterNew_ng/w`.

## `current/<slug>.json` shape
```json
{ "id":"NSE:NIFTY 50","exchange":"NSE","name":"NIFTY 50","code":null,
  "source":"...","count":50,"fetched_at":"2026-06-25T07:30:33+05:30",
  "members":[{"symbol":"ADANIENT","name":"Adani Enterprises Ltd.","isin":"INE423A01024"}, ...] }
```
NSE `symbol` = ticker; BSE `symbol` = scrip code. `isin` is captured for both → enables
cross-exchange company matching (Phase 3 "stock → which indices").

## Correctness guards implemented (Phase 1 portion)
- **Throttle + retry**: 0.35s (NSE) / 0.6s (BSE) between requests; 3 retries w/ backoff.
- **End-of-run retry pass**: failed indices get one calmer retry (caught the NIFTY 100 blip).
- **Snapshot guard**: never overwrite a healthy snapshot with an empty/short fetch
  (`new < prev*0.5` → keep old file, mark `guard_skipped`). Empty fetch → `failed`, no write.
- **First-run baseline**: no prev snapshot → any non-empty fetch is written (no crash, no guard).

## Known gap (explicit backlog)
40 niche NSE factor/strategy/thematic indices (Alpha 50, Private Bank, Nifty50 Value 20,
EQL WGT, ESG, Shariah, Internet, EV, ...) are unresolved — niftyindices CSV filenames are
inconsistent and unguessable. All broad/sectoral/midcap/smallcap and most factor indices ARE
covered. Backlog list is in `nse_index_map.json:"unresolved"`. To close it authoritatively:
harvest the real CSV links from each niftyindices index page (sitemap crawl) — a follow-up.

## Not yet built
- **Phase 2** — Diff engine: compare new fetch vs previous `current/`, append `{date,index,
  type,added,removed}` to `changes.jsonl`; seed `type:"initial"` on first run; git commit
  (push isolated/non-fatal).
- **Phase 3** — Static frontend (GitHub Pages) reading the JSON.
- **Phase 4** — Task Scheduler ~18:00 IST + Telegram alerts; pin nsepython.
