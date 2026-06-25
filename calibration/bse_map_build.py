# Build the final BSE index map: code + iname (shortalias + overrides) + verified
# member count. Confirms PSU/CG/CD override guesses; flags USD Dollex as out-of-scope.
import requests, time, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "maps"); os.makedirs(OUT, exist_ok=True)
BASE = "https://api.bseindia.com/BseIndiaAPI/api"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*",
     "Origin": "https://www.bseindia.com", "Referer": "https://www.bseindia.com/"}

# shortalias (from master) -> correct iname for the constituents endpoint
OVERRIDE = {"SENSEX": "BSE30", "BSE-100": "BSE100", "BSE-200": "BSE200", "BSE-500": "BSE500",
            "BSE IPO": "BSEIPO", "OIL&GAS": "OILGAS", "FMCG": "BSEFMCG", "IT": "BSEIT",
            "HC": "BSEHC", "PSU": "BSEPSU", "CG": "BSECG", "CD": "BSECD",
            "DOL-30": "DOLLEX30", "DOL-100": "DOLLEX100", "DOL-200": "DOLLEX200"}
USD_VARIANTS = {"DOL-30", "DOL-100", "DOL-200"}  # redundant USD versions -> out of scope

s = requests.Session()
s.get("https://www.bseindia.com/", headers={**h, "Accept": "text/html,*/*"}, timeout=15)
master = s.get(f"{BASE}/IndexMasterNew_ng/w?FLAGCODE=&LNFLAG=&PageNo=1&RecordsPerPage=300&IsHomePage=",
               headers=h, timeout=20).json()["table"]

out = []
for row in master:
    name, code = row["INDEXNAME"], row.get("code")
    alias = (row.get("shortalias") or "").strip()
    iname = OVERRIDE.get(alias, alias)
    in_scope = alias not in USD_VARIANTS
    members = -1
    if iname:
        try:
            j = s.get(f"{BASE}/NS_IndexWeight_SPDJ_ng/w", params={"iname": iname},
                      headers=h, timeout=15).json()
            members = len(j.get("Table", [])) if isinstance(j, dict) else 0
        except Exception:
            members = -2
        time.sleep(0.5)
    out.append({"name": name, "code": code, "shortalias": alias, "iname": iname,
                "members": members, "in_scope": in_scope})

ok = [r for r in out if r["members"] > 0 and r["in_scope"]]
bad = [r for r in out if r["members"] <= 0 and r["in_scope"]]
print(f"BSE: {len(ok)} in-scope indices with constituents; {len(bad)} still empty; "
      f"{len(out)-len([r for r in out if r['in_scope']])} USD-variant skipped\n")
for r in sorted(out, key=lambda x: -x["members"]):
    s_ = "skip-USD" if not r["in_scope"] else (f"{r['members']}" if r["members"] > 0 else "EMPTY")
    print(f"  {r['name'][:38]:38} code={str(r['code']):>4} iname={r['iname'][:10]:10} {s_}")
json.dump(out, open(os.path.join(OUT, "bse_index_map.json"), "w", encoding="utf-8"), indent=2)
print("\n-> saved maps/bse_index_map.json")
