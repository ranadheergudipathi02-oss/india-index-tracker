"""Phase 1+2 fetcher + diff engine: loop NSE + BSE indices, throttle + retry, apply the
snapshot guard, diff against the previous current/ snapshot, append changes.jsonl, write
current/<slug>.json + meta.json, then a best-effort (non-fatal) git commit.

Run:  python fetcher/fetch.py
"""
import os, sys, io, csv, json, time, re, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
import diff
import requests
from datetime import datetime


def now_ist():
    return datetime.now(C.IST).isoformat(timespec="seconds")

def today_ist():
    return datetime.now(C.IST).date().isoformat()

def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load_indices():
    nse = json.load(open(os.path.join(C.MAPS_DIR, "nse_index_map.json"), encoding="utf-8"))
    bse = json.load(open(os.path.join(C.MAPS_DIR, "bse_index_map.json"), encoding="utf-8"))
    items = []
    for r in nse["resolved"]:
        if r.get("alias_of"):
            continue
        items.append({"exchange": "NSE", "name": r["name"], "kind": "nse_csv", "source": r["url"]})
    for r in bse:
        if not r.get("in_scope") or r["members"] <= 0:
            continue
        items.append({"exchange": "BSE", "name": r["name"], "kind": "bse_api",
                      "code": r["code"], "iname": r["iname"],
                      "source": f"{C.BSE_BASE}/NS_IndexWeight_SPDJ_ng/w?iname={r['iname']}"})
    return items


def fetch_nse_csv(url, session):
    r = session.get(url, headers=C.NSE_HEADERS, timeout=20)
    if "html" in r.headers.get("content-type", "") or "<html" in r.text[:200].lower():
        raise ValueError("expected CSV, got HTML (transient SPA shell / file moved?)")
    members = []
    for row in csv.DictReader(io.StringIO(r.text)):
        sym = (row.get("Symbol") or "").strip()
        if not sym:
            continue
        members.append({"symbol": sym,
                        "name": (row.get("Company Name") or row.get("Company") or "").strip(),
                        "isin": (row.get("ISIN Code") or "").strip()})
    return members


def fetch_bse(iname, session):
    r = session.get(f"{C.BSE_BASE}/NS_IndexWeight_SPDJ_ng/w", params={"iname": iname},
                    headers=C.BSE_HEADERS, timeout=20)
    j = r.json()
    rows = j.get("Table", []) if isinstance(j, dict) else []
    members = []
    for row in rows:
        sym = str(row.get("Scrip_code") or "").strip()
        if not sym:
            continue
        members.append({"symbol": sym,
                        "name": (row.get("Scrip_Name") or "").strip(),
                        "isin": (row.get("ISIN_NUMBER") or "").strip()})
    return members


def with_retry(fn, *args):
    last = "failed"
    for i in range(C.RETRIES):
        try:
            m = fn(*args)
            if m:
                return m
            last = "empty response"
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(C.RETRY_BACKOFF * (i + 1))
    raise RuntimeError(last)


def read_old(path):
    """Previous snapshot's member list, or None if no snapshot yet."""
    try:
        return json.load(open(path, encoding="utf-8")).get("members")
    except Exception:
        return None


def handle(it, session, meta, date_str, baseline):
    ex, name = it["exchange"], it["name"]
    iid = f"{ex}:{name}"
    path = os.path.join(C.CURRENT_DIR, f"{ex.lower()}_{slugify(name)}.json")
    try:
        members = (with_retry(fetch_nse_csv, it["source"], session) if it["kind"] == "nse_csv"
                   else with_retry(fetch_bse, it["iname"], session))
    except Exception as e:
        meta["indices"][iid] = {"status": "failed", "reason": str(e), "count": 0,
                                "source": it["source"], "fetched_at": now_ist()}
        return "failed"

    old = read_old(path)
    n = len(members)

    # snapshot guard: never overwrite/diff a healthy snapshot with a suspiciously short fetch
    if old is not None and n < len(old) * C.SHRINK_GUARD:
        meta["indices"][iid] = {"status": "guard_skipped", "count": n, "prev_count": len(old),
                                "reason": f"shrank {len(old)}->{n}", "source": it["source"],
                                "fetched_at": now_ist()}
        return "guard"

    # diff / baseline (baseline run, or an index new to tracking -> seed an "initial" entry)
    if baseline or old is None:
        diff.append_change(diff.make_entry(date_str, iid, "initial", members, []))
        added_n, removed_n, changed = n, 0, True
    else:
        added, removed = diff.compute_diff(old, members)
        if added or removed:
            diff.append_change(diff.make_entry(date_str, iid, "change", added, removed))
        added_n, removed_n, changed = len(added), len(removed), bool(added or removed)

    # current/<slug>.json — no timestamp inside, so unchanged indices stay byte-identical (clean git)
    doc = {"id": iid, "exchange": ex, "name": name, "code": it.get("code"),
           "source": it["source"], "count": n, "members": members}
    json.dump(doc, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    meta["indices"][iid] = {"status": "ok", "count": n, "prev_count": (len(old) if old else None),
                            "changed": changed, "added": added_n, "removed": removed_n,
                            "file": os.path.basename(path), "source": it["source"], "fetched_at": now_ist()}
    return "ok"


def git_commit(msg):
    root = C.PROJECT_ROOT
    if not os.path.isdir(os.path.join(root, ".git")):
        print("git: no repo (skipping commit)")
        return
    subprocess.run(["git", "-C", root, "add", "current", "changes.jsonl", "meta.json"],
                   capture_output=True, text=True)
    r = subprocess.run(["git", "-C", root, "commit", "-m", msg], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip().splitlines()
    print("git commit:", out[-1] if out else "(nothing to commit)")
    # push is a SEPARATE, non-fatal step (works once a remote is configured)
    try:
        p = subprocess.run(["git", "-C", root, "push"], capture_output=True, text=True, timeout=60)
        msg2 = (p.stdout + p.stderr).strip().splitlines()
        print("git push:", "ok" if p.returncode == 0 else f"skipped/non-fatal ({msg2[-1] if msg2 else p.returncode})")
    except Exception as e:
        print("git push: skipped/non-fatal —", e)


def main():
    os.makedirs(C.CURRENT_DIR, exist_ok=True)
    items = load_indices()
    if "--only" in sys.argv:                       # ops: re-fetch a subset, e.g. --only "NIFTY IT"
        sub = sys.argv[sys.argv.index("--only") + 1].lower()
        items = [it for it in items if sub in f'{it["exchange"]}:{it["name"]}'.lower()]
    date_str = today_ist()
    baseline = not os.path.exists(C.CHANGES_FILE)   # first ever run -> seed initial for all
    n_nse = sum(i["exchange"] == "NSE" for i in items)
    print(f"loaded {len(items)} indices ({n_nse} NSE, {len(items)-n_nse} BSE)  date={date_str}"
          f"{'  [BASELINE run: seeding initial]' if baseline else ''}\n")

    session = requests.Session()
    try:
        session.get("https://www.bseindia.com/", headers={**C.BSE_HEADERS, "Accept": "text/html,*/*"}, timeout=15)
    except Exception:
        pass

    meta = {"last_run": now_ist(), "indices": {}}
    if os.path.exists(C.META_FILE):     # preserve status of indices not processed this run (e.g. --only)
        try:
            meta["indices"] = json.load(open(C.META_FILE, encoding="utf-8")).get("indices", {})
        except Exception:
            pass
    t0 = time.time()
    failed = []
    changes = []
    for it in items:
        st = handle(it, session, meta, date_str, baseline)
        iid = f'{it["exchange"]}:{it["name"]}'
        m = meta["indices"][iid]
        if st == "ok" and m.get("changed"):
            changes.append((iid, m["added"], m["removed"]))
        if st == "failed":
            failed.append(it)
        time.sleep(C.NSE_SLEEP if it["kind"] == "nse_csv" else C.BSE_SLEEP)

    if failed:
        print(f"\nretry pass: {len(failed)} failed, cooling down 5s...")
        time.sleep(5)
        for it in failed:
            st = handle(it, session, meta, date_str, baseline)
            iid = f'{it["exchange"]}:{it["name"]}'
            if st == "ok" and meta["indices"][iid].get("changed"):
                changes.append((iid, meta["indices"][iid]["added"], meta["indices"][iid]["removed"]))
            print(f"  retry {iid:40} -> {st}")
            time.sleep(2.0)

    statuses = [m["status"] for m in meta["indices"].values()]
    meta["duration_sec"] = round(time.time() - t0, 1)
    meta["summary"] = {"total": len(meta["indices"]), "ok": statuses.count("ok"),
                       "failed": statuses.count("failed"), "guard_skipped": statuses.count("guard_skipped"),
                       "indices_changed": len(changes),
                       "members_added": sum(c[1] for c in changes),
                       "members_removed": sum(c[2] for c in changes)}
    json.dump(meta, open(C.META_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print(f"\nDONE in {meta['duration_sec']}s  {meta['summary']}")
    if changes:
        print("changes this run:")
        for iid, a, r in changes:
            print(f"   {iid:44} +{a} -{r}")
    git_commit(f"fetch {date_str}: {len(changes)} index change(s), "
               f"{meta['summary']['ok']}/{len(items)} ok")


if __name__ == "__main__":
    main()
