# Phase 0 — Sanity Test Findings

**Status: COMPLETE. All three open unknowns resolved.** Run from a residential IP on
the local Windows PC (Python 3.12.0, nsepython 2.97, requests). Project root:
`C:\Claude developement\static-index-tracker\` (separate from the unrelated dir the
session launched in).

The headline: the data paths the master prompt *assumed* are mostly wrong, but the
goal is fully achievable via better sources. Details below — read the deviations.

---

## 1. Residential-IP reachability — CONFIRMED
All three hosts respond from this IP with browser-like headers:
- `www.nseindia.com/api/*` — JSON 200 (after cookie priming; see NSE notes)
- `niftyindices.com` — CSV 200, no bot wall
- `api.bseindia.com/BseIndiaAPI/api/*` — JSON 200 (with Origin/Referer = bseindia.com)

The naive `requests.get(nseindia.com)` gets a 403 Akamai wall; this is an application
block, not an IP block (0.25s response). It is bypassable (below). No datacenter-IP
ban observed because we are on residential IP, as the architecture requires.

---

## 2. NSE — coverage + path

**Index list:** `nse_get_index_list()` works and returns **213 indices**. Important:
it does NOT hit nseindia.com — it reads a static CDN blob
(`iislliveblob.niftyindices.com/jsonfiles/LiveIndicesWatch.json`). So it is reliable
and Akamai-free. Full list saved in `phase0/nse_index_list.txt`.

**Coverage is the OPPOSITE problem the prompt feared.** The prompt worried strategy/
thematic indices would be *missing*. They are all present (NIFTY200MOMENTM30,
NIFTY500 QUALITY 50, NIFTY ALPHA 50, NIFTY EV, NIFTY IND DEFENCE, …). The real issue
is the list is **too broad**: ~130 of the 213 are out-of-scope fixed-income / leverage
instruments — G-SEC, SDL, BHARATBOND, AAA BOND, `TR/PR 2X LEV`, USD variants. Phase 1
needs a **scope filter** (allow equity broad/sectoral/thematic/strategy; drop bond/
gsec/sdl/leverage/USD). Net in-scope ≈ 80 equity indices.

**Constituents — the assumed endpoint is DEAD.** `/api/equity-stockIndices?index=…`
(the canonical one nsepython + every tutorial uses) returns a clean **404** from this
IP, across all encodings — while sibling endpoints (`allIndices`, `marketStatus`,
`equity-master`) return JSON 200 with the same session. It is retired/moved, not
blocked.

**Constituents — the replacement (better) source:** the official NSE Indices CSVs:
```
https://niftyindices.com/IndexConstituent/ind_<slug>list.csv
```
Verified: `ind_nifty50list.csv` (50), `ind_niftybanklist.csv`, `ind_nifty500list.csv`
(500). Columns: `Company Name, Industry, Symbol, Series, ISIN Code` → exactly the
`{symbol, name}` we store, plus ISIN. Authoritative (NSE Indices Ltd), no Akamai, clean.

**Open Phase-1 task (NSE):** build the in-scope index-name → CSV-slug map. Slug is
roughly `ind_<lowercased, spaces/special stripped>list.csv` but has irregulars; must
be verified per index (one-time calibration, like BSE below).

### Working NSE session priming (kept for any nseindia.com/api need)
Homepage 403s, but `GET /market-data/live-equity-market` after it yields valid cookies
(`_abck, ak_bmsc, bm_sz, nsit, AKA_A2`); subsequent `/api/*` JSON calls then succeed.
Code in `phase0/nse_session.py`. Not needed for constituents (CSVs don't require it).

---

## 3. BSE — codes + path  (the genuine hard unknown — now fully cracked)

Endpoints were discovered by downloading bseindia.com's Angular bundles and grepping
the string literals (`phase0/bse_discover*.py`) — no browser needed. Base:
`https://api.bseindia.com/BseIndiaAPI/api`. All calls need `Origin` + `Referer` =
`https://www.bseindia.com`.

**Index master + codes:**
```
/IndexMasterNew_ng/w?FLAGCODE=&LNFLAG=&PageNo=1&RecordsPerPage=300&IsHomePage=
```
Returns `{table:[…]}`, **75 indices**, each with `INDEXNAME`, `code`, `shortalias`.
Confirms **SENSEX = code 16** (prompt's guess was right) plus 74 others. Full catalog
saved in `phase0/bse_index_catalog.json`. The hardcoded-code-mapping the prompt wanted
is now fetched dynamically — no guessing.

**Constituents:**
```
/NS_IndexWeight_SPDJ_ng/w?iname=<INAME>      ->  {Table:[…]}
```
Each row: `Scrip_code, Scrip_Name, ISIN_NUMBER, Weightage, Industry_Name, MKT_CAP, …`
→ richer than NSE (gives weight + ISIN). Store `{symbol: Scrip_code, name: Scrip_Name}`.
A `_Download_ng` CSV variant also exists.

**The iname mapping** (the only subtlety): `iname` is the index's `Indx_Cd`, which
equals `shortalias` for **61 of 75** indices. 14 need an override (verified):

| INDEXNAME | shortalias | correct iname |
|---|---|---|
| BSE SENSEX | SENSEX | `BSE30` |
| BSE 100 / 200 / 500 | BSE-100/200/500 | `BSE100` / `BSE200` / `BSE500` |
| BSE IPO | BSE IPO | `BSEIPO` |
| BSE FMCG | FMCG | `BSEFMCG` |
| BSE IT | IT | `BSEIT` |
| BSE Healthcare | HC | `BSEHC` |
| BSE Oil & Gas | OIL&GAS | `OILGAS` |
| BSE PSU / Capital Goods / Consumer Durables | PSU/CG/CD | likely `BSEPSU`/`BSECG`/`BSECD` (confirm in P1) |
| BSE DOLLEX 30/100/200 | DOL-30/… | USD variants — **out of scope**, skip |

Strategy: `iname = OVERRIDE.get(shortalias, shortalias)`; calibrate the override map
once by fetching all in-scope indices and recording any that return 0 rows.

---

## Decision: nsepython vs raw-HTTP
**Hybrid, leaning raw-HTTP to stable sources:**
- NSE index list: `nse_get_index_list()` (or read the niftyindices blob directly).
- NSE constituents: raw HTTP → niftyindices.com CSVs. (NOT nseindia.com API, NOT
  nsepython per-index — both dead/fragile.)
- BSE: raw HTTP → api.bseindia.com (`IndexMasterNew_ng` + `NS_IndexWeight_SPDJ_ng`).

We avoid the Akamai-protected nseindia.com path entirely for the actual data. Pin
nsepython only as a convenience for the index-name list.

## Deviations from the master prompt (must carry into Phase 1)
1. nsepython per-index endpoints are dead → use niftyindices CSVs.
2. NSE coverage isn't under-inclusive, it's over-inclusive → add a scope filter.
3. BSE codes fetched dynamically (75) → tiny iname-override map, not a full hardcoded
   code table.
4. The real BSE unknown was the *constituents endpoint* (prompt didn't specify one) —
   now identified and verified.

## Phase 1 ready-list
- [ ] NSE index→CSV-slug map for ~80 in-scope equity indices (+ scope filter).
- [ ] BSE iname override map finalized (confirm PSU/CG/CD; decide on Dollex/USD).
- [ ] Fetcher: loop both exchanges, throttle + retry, snapshot guard, write `current/`,
      log per-index status to `meta.json`.
