# Phase 2 — Diff Engine (COMPLETE & verified)

Adds change tracking on top of the Phase 1 fetcher: every run diffs each index's new
constituents against the previous `current/` snapshot and appends membership changes to
an append-only log, then makes a best-effort git commit.

## Files
- `fetcher/diff.py` — `compute_diff(old,new)` (by symbol), `append_change`, `make_entry`.
- `fetcher/fetch.py` — integrated diff into the fetch loop; git commit/push.
- `fetcher/diff_test.py` — fast synthetic unit test (no network).
- OUTPUT `changes.jsonl` (append-only), plus `current/` + `meta.json` from Phase 1.

## changes.jsonl format (one JSON object per line)
```json
{"date":"2026-06-25","index":"NSE:NIFTY IT","type":"change",
 "added":[{"symbol":"WIPRO","name":"Wipro Ltd."}],
 "removed":[{"symbol":"FAKECO","name":"Fake Test Co Ltd."}]}
```
`type`: `"initial"` (index's first appearance / baseline run) | `"change"`. Written ONLY
when a diff is detected. `date` = detection date (IST). Membership identity = **symbol**
(NSE ticker / BSE scrip code); a name-only change is not a membership change.

## Logic & guards
- **Baseline:** first ever run (no `changes.jsonl`) seeds one `initial` entry per index; a
  brand-new index later (no `current/` file yet) also gets `initial`. No diff on baseline.
- **Snapshot guard:** empty/short fetch (`new < prev*0.5`) → keep old snapshot, mark
  `guard_skipped`, no diff, no overwrite. (Primary corruption defense.)
- **No git churn:** `current/<slug>.json` holds no timestamp (that's in `meta.json`), so
  unchanged indices stay byte-identical run to run — git diffs show only real changes.
- **meta.json merges** across runs, so a partial `--only` run doesn't wipe other indices.
- **Git:** commit (current/ + changes.jsonl + meta.json) is best-effort; **push is a
  separate, non-fatal step** (inert until a remote is configured) — a failed push never
  blocks or corrupts a run.

## Verified end-to-end (2026-06-25)
1. Baseline run → 150 `initial` entries, 150 `current/` files, commit. ✅
2. Tampered `current/nse_nifty-it.json` (swapped WIPRO→FAKECO), re-ran `--only "NIFTY IT"`
   → detected exactly `+WIPRO / -FAKECO`, appended one `change` entry, restored the file. ✅
3. Full no-op run → `indices_changed=0` (no false positives), `changes.jsonl` unchanged,
   only `meta.json` re-touched. ✅  `diff_test.py` passes (add/remove/rename-ignored/no-op). ✅

## Ops
- `python fetcher/fetch.py`            full daily run
- `python fetcher/fetch.py --only "NIFTY IT"`   re-fetch a subset (meta merges, not wiped)

## Next
- **Phase 3** — static GitHub Pages frontend reading current/ + changes.jsonl + meta.json.
- **Phase 4** — Task Scheduler ~18:00 IST + Telegram alerts; add git remote + enable push; pin nsepython.
- **Backlog** — 40 niche NSE indices (filenames TBD via niftyindices page crawl).
