# Resolve the in-scope "empty" BSE indices: alias-format quirk, or different feed?
import requests, time

BASE = "https://api.bseindia.com/BseIndiaAPI/api"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
api_h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*",
         "Origin": "https://www.bseindia.com", "Referer": "https://www.bseindia.com/"}
s = requests.Session()
s.get("https://www.bseindia.com/", headers={**api_h, "Accept": "text/html,*/*"}, timeout=15)

candidates = {
    "BSE 100":        ["BSE100", "100", "ALLCAP", "BSE-100"],
    "BSE 200":        ["BSE200", "200"],
    "BSE 500":        ["BSE500", "500", "ALLCAP500"],
    "BSE IPO":        ["BSEIPO"],
    "BSE OIL & GAS":  ["OIL&GAS", "OILGAS"],          # requests will %-encode the &
    "BSE FMCG":       ["FMCG", "BSEFMCG"],
    "BSE IT":         ["IT", "BSEIT", "INFOTECH"],
    "BSE Healthcare": ["HC", "HEALTHCARE", "BSEHC"],
}
for label, cands in candidates.items():
    print(f"\n{label}")
    for c in cands:
        try:
            r = s.get(f"{BASE}/NS_IndexWeight_SPDJ_ng/w", params={"iname": c},
                      headers=api_h, timeout=15)
            j = r.json()
            T = j.get("Table", []) if isinstance(j, dict) else []
            first = T[0].get("Scrip_Name") if T else ""
            print(f"   iname={c:<12} rows={len(T):<4} {first}")
        except Exception as e:
            print(f"   iname={c:<12} ERR {type(e).__name__}: {e}")
        time.sleep(0.6)
