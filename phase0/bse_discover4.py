# Harvest literal iname values from the bundle + test Sensex iname candidates.
import requests, re, json, time

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
h = {"User-Agent": UA, "Accept": "*/*", "Referer": "https://www.bseindia.com/"}
s = requests.Session()
s.get("https://www.bseindia.com/", headers={**h, "Accept": "text/html,*/*"}, timeout=15)

blob = ""
for u in ["https://www.bseindia.com/assets/includenew/js/scripts-OXCQKZIU.js",
          "https://www.bseindia.com/assets/includenew/js/main-WDSOQSQ3.js"]:
    blob += "\n" + s.get(u, headers=h, timeout=30).text

literal = sorted(set(re.findall(r'iname=([A-Za-z0-9]{2,12})', blob)))
print("literal iname values in bundle:", literal)
for m in list(re.finditer("Indx_Cd", blob))[:3]:
    print("Indx_Cd ctx:", blob[max(0, m.start()-70):m.start()+150].replace("\n", " "))

BASE = "https://api.bseindia.com/BseIndiaAPI/api"
api_h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*",
         "Origin": "https://www.bseindia.com", "Referer": "https://www.bseindia.com/"}
candidates = ["SENSEX", "BSE30", "SENSEX30", "SNSX", "SNX30", "BSESENSEX", "30", "SPSENSEX"]
# add a few harvested ones that look index-like
candidates += [x for x in literal if x not in candidates][:8]

print("\n=== testing NS_IndexWeight_SPDJ_ng/w?iname=... ===")
for c in candidates:
    try:
        r = s.get(f"{BASE}/NS_IndexWeight_SPDJ_ng/w?iname={c}", headers=api_h, timeout=15)
        j = r.json()
        T = j.get("Table", []) if isinstance(j, dict) else []
        first = (T[0].get("Scrip_Name") if T else "")
        print(f"  iname={c:<10} rows={len(T):<3} {first}")
    except Exception as e:
        print(f"  iname={c:<10} ERR {type(e).__name__}: {e}")
    time.sleep(0.6)
