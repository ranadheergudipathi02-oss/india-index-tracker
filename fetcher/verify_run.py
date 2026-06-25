import os, json, glob, requests, time
import config as C

files = glob.glob(os.path.join(C.CURRENT_DIR, "*.json"))
print(f"current/ files: {len(files)}")
total_members = 0
for f in files:
    total_members += json.load(open(f, encoding="utf-8")).get("count", 0)
print(f"total membership rows across all indices: {total_members}")

meta = json.load(open(C.META_FILE, encoding="utf-8"))
print("\nmeta summary:", meta["summary"], "| last_run:", meta["last_run"], "| dur:", meta["duration_sec"], "s")
print("\nnon-ok indices:")
for iid, m in meta["indices"].items():
    if m["status"] != "ok":
        print(" ", iid, m["status"], "-", m.get("reason", ""))

# is NIFTY 100 failure transient? re-fetch in isolation
print("\nre-fetch ind_nifty100list.csv in isolation:")
r = requests.get("https://niftyindices.com/IndexConstituent/ind_nifty100list.csv",
                 headers=C.NSE_HEADERS, timeout=20)
print("  status", r.status_code, "ct", r.headers.get("content-type"), "len", len(r.text),
      "| looks_csv:", "<html" not in r.text[:200].lower())
