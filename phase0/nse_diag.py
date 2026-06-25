# Disambiguate: is it THIS endpoint (moved) or ALL /api/ calls (session/Akamai)?
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nse_session import make_session, prime

s = make_session()
print("prime (home, live-mkt, #cookies):", prime(s))
print("cookies:", sorted(c.name for c in s.cookies))

API_HDR = {
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nseindia.com/market-data/live-equity-market",
    "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin",
    "X-Requested-With": "XMLHttpRequest",
}
tests = [
    "https://www.nseindia.com/api/allIndices",
    "https://www.nseindia.com/api/marketStatus",
    "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050",
    "https://www.nseindia.com/api/equity-master",
]
for url in tests:
    try:
        r = s.get(url, headers=API_HDR, timeout=10)
        ct = r.headers.get("content-type", "")
        is_json = ct.startswith("application/json")
        head = "" if is_json else r.text[:90].replace("\n", " ")
        print(f"\n{r.status_code} json={is_json} len={len(r.text)}  {url}\n   {head}")
    except Exception as e:
        print(f"\nERR {type(e).__name__}: {e}  {url}")
    time.sleep(1.2)
