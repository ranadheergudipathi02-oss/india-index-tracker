# Test the REAL BSE endpoints discovered from the JS bundle.
import requests, json

BASE = "https://api.bseindia.com/BseIndiaAPI/api"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*",
     "Accept-Language": "en-US,en;q=0.9",
     "Origin": "https://www.bseindia.com", "Referer": "https://www.bseindia.com/"}

s = requests.Session()
s.get("https://www.bseindia.com/", headers={**h, "Accept": "text/html,*/*"}, timeout=15)  # prime

def hit(path, show_rows=3):
    print("\n" + "=" * 70 + f"\nGET {path}")
    try:
        r = s.get(BASE + path, headers=h, timeout=20)
    except Exception as e:
        print("  ERR", type(e).__name__, e); return None
    ct = r.headers.get("content-type", "")
    print(f"  status={r.status_code} ct={ct} len={len(r.text)}")
    try:
        j = r.json()
    except Exception:
        print("  NOT JSON, head:", r.text[:160].replace("\n", " ")); return None
    if isinstance(j, dict):
        print("  dict keys:", list(j.keys()))
        for k, v in j.items():
            if isinstance(v, list) and v:
                print(f"  [{k}] {len(v)} rows; row0 keys: {list(v[0].keys()) if isinstance(v[0],dict) else type(v[0])}")
                for row in v[:show_rows]:
                    print("     ", json.dumps(row)[:200])
                break
    elif isinstance(j, list):
        print(f"  list {len(j)} rows; row0:", json.dumps(j[0])[:200] if j else None)
    return j

# 1) Index master — list of BSE indices + their codes
hit("/IndexMasterNew_ng/w?FLAGCODE=&LNFLAG=&PageNo=1&RecordsPerPage=200&IsHomePage=", show_rows=6)
# 2) SENSEX constituents via the display endpoint (16 = commonly-cited Sensex code)
hit("/indiceswatch_weight_ng/w?flag=16")
# 3) Sensex-specific endpoint
hit("/GetSensexData/w")
