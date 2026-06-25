# Test NSE constituent sourcing alternatives now that /api/equity-stockIndices 404s.
import sys, os, io, csv, time, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nse_session import make_session, prime

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

print("=== A) niftyindices.com official constituent CSVs ===")
H = {"User-Agent": UA, "Referer": "https://niftyindices.com/",
     "Accept": "text/csv,application/csv,*/*", "Accept-Language": "en-US,en;q=0.9"}
csv_urls = [
    "https://niftyindices.com/IndexConstituent/ind_nifty50list.csv",
    "https://niftyindices.com/IndexConstituent/ind_niftybanklist.csv",
    "https://niftyindices.com/IndexConstituent/ind_nifty500list.csv",
    "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
]
for u in csv_urls:
    try:
        r = requests.get(u, headers=H, timeout=15)
        looks_csv = r.text[:300].count(",") > 2 and "<html" not in r.text[:300].lower()
        print(f"\n{r.status_code} len={len(r.text)} ct={r.headers.get('content-type')} csv={looks_csv}  {u}")
        if r.status_code == 200 and looks_csv:
            rows = list(csv.DictReader(io.StringIO(r.text)))
            cols = list(rows[0].keys()) if rows else []
            print("  rows:", len(rows), " cols:", cols)
            for row in rows[:3]:
                print("   ", (row.get("Symbol") or "").strip(), "—", (row.get("Company Name") or "").strip())
        else:
            print("  head:", r.text[:120].replace("\n", " "))
    except Exception as e:
        print("  ERR", type(e).__name__, e)
    time.sleep(1)

print("\n=== B) is /api/equity-stockIndices truly dead? (encoding variations) ===")
s = make_session()
print("prime:", prime(s))
base = "https://www.nseindia.com/api/equity-stockIndices"
api_hdr = {"Accept": "application/json, text/plain, */*",
           "Referer": "https://www.nseindia.com/market-data/live-equity-market",
           "X-Requested-With": "XMLHttpRequest", "sec-fetch-site": "same-origin",
           "sec-fetch-mode": "cors", "sec-fetch-dest": "empty"}
for q in ["?index=NIFTY%2050", "?index=NIFTY+50", "?index=NIFTY 50", "?index=NIFTY%20BANK"]:
    try:
        r = s.get(base + q, headers=api_hdr, timeout=10)
        print(f"  {r.status_code} len={len(r.text)}  {q}")
    except Exception as e:
        print("  ERR", type(e).__name__, e, q)
    time.sleep(1)
