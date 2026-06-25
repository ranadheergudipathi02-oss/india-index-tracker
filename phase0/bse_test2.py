# Final BSE piece: constituents via NS_IndexWeight_SPDJ_ng/w?iname=<shortalias>
import requests, json

BASE = "https://api.bseindia.com/BseIndiaAPI/api"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*",
     "Accept-Language": "en-US,en;q=0.9",
     "Origin": "https://www.bseindia.com", "Referer": "https://www.bseindia.com/"}
s = requests.Session()
s.get("https://www.bseindia.com/", headers={**h, "Accept": "text/html,*/*"}, timeout=15)

def hit(path):
    print("\n" + "=" * 70 + f"\nGET {path}")
    r = s.get(BASE + path, headers=h, timeout=20)
    print(f"  status={r.status_code} ct={r.headers.get('content-type')} len={len(r.text)}")
    try:
        j = r.json()
    except Exception:
        print("  NOT JSON:", r.text[:140].replace("\n", " ")); return
    keys = list(j.keys()) if isinstance(j, dict) else "(list)"
    print("  keys:", keys)
    T = (j.get("Table") or j.get("table") or []) if isinstance(j, dict) else j
    print("  Table rows:", len(T))
    if T:
        print("  row0 keys:", list(T[0].keys()))
        for row in T[:6]:
            print("   ", json.dumps(row)[:240])

for iname in ["SENSEX", "BANKEX"]:
    hit(f"/NS_IndexWeight_SPDJ_ng/w?iname={iname}")
