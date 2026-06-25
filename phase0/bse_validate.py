# Calibrate BSE: for all 75 indices from the master, test iname=shortalias and
# record which yield constituents (rows>0) vs which need an override mapping.
import requests, json, time, os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://api.bseindia.com/BseIndiaAPI/api"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
api_h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*",
         "Origin": "https://www.bseindia.com", "Referer": "https://www.bseindia.com/"}
s = requests.Session()
s.get("https://www.bseindia.com/", headers={**api_h, "Accept": "text/html,*/*"}, timeout=15)

OVERRIDE = {"SENSEX": "BSE30"}  # known legacy exception

master = s.get(f"{BASE}/IndexMasterNew_ng/w?FLAGCODE=&LNFLAG=&PageNo=1&RecordsPerPage=300&IsHomePage=",
               headers=api_h, timeout=20).json()["table"]
print(f"master indices: {len(master)}\n")

results = []
for row in master:
    name, code, alias = row["INDEXNAME"], row.get("code"), (row.get("shortalias") or "").strip()
    iname = OVERRIDE.get(alias, alias)
    rows = -1
    if iname:
        try:
            j = s.get(f"{BASE}/NS_IndexWeight_SPDJ_ng/w?iname={iname}", headers=api_h, timeout=15).json()
            rows = len(j.get("Table", [])) if isinstance(j, dict) else 0
        except Exception:
            rows = -2
        time.sleep(0.6)
    results.append({"name": name, "code": code, "shortalias": alias, "iname": iname, "members": rows})

ok = [r for r in results if r["members"] > 0]
empty = [r for r in results if r["members"] == 0]
print(f"WORKING: {len(ok)}/{len(master)}   EMPTY/needs-override: {len(empty)}\n")
print(f"{'INDEXNAME':40} {'code':>5} {'alias':>10} {'mem':>5}")
for r in sorted(results, key=lambda x: -x["members"]):
    flag = "" if r["members"] > 0 else "  <-- empty"
    print(f"{r['name'][:40]:40} {str(r['code']):>5} {r['shortalias'][:10]:>10} {r['members']:>5}{flag}")

with open(os.path.join(HERE, "bse_index_catalog.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print("\n-> saved phase0/bse_index_catalog.json")
