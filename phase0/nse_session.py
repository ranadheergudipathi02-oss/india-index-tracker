# Robust NSE session fetcher — proper Akamai cookie priming, full browser headers.
# This is the "raw HTTP" path the spec wants as the real fetch mechanism.
import requests, time, urllib.parse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
HTML_ACCEPT = ("text/html,application/xhtml+xml,application/xml;q=0.9,"
               "image/avif,image/webp,*/*;q=0.8")

def make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",          # no 'br' — brotli may be absent
        "Connection": "keep-alive",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    })
    return s

def prime(s):
    nav = {"Accept": HTML_ACCEPT, "sec-fetch-dest": "document", "sec-fetch-mode": "navigate",
           "sec-fetch-user": "?1", "upgrade-insecure-requests": "1"}
    r1 = s.get("https://www.nseindia.com/", headers={**nav, "sec-fetch-site": "none"}, timeout=10)
    r2 = s.get("https://www.nseindia.com/market-data/live-equity-market",
               headers={**nav, "sec-fetch-site": "same-origin", "Referer": "https://www.nseindia.com/"},
               timeout=10)
    return r1.status_code, r2.status_code, len(s.cookies)

def fetch_index(s, index):
    url = "https://www.nseindia.com/api/equity-stockIndices?index=" + urllib.parse.quote(index)
    return s.get(url, headers={
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.nseindia.com/market-data/live-equity-market",
        "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin",
        "X-Requested-With": "XMLHttpRequest",
    }, timeout=10)

if __name__ == "__main__":
    s = make_session()
    print("prime (home, live-mkt, #cookies):", prime(s))
    for idx in ["NIFTY 50", "NIFTY BANK"]:
        try:
            r = fetch_index(s, idx)
            ct = r.headers.get("content-type", "")
            print(f"\n{idx}: status={r.status_code} ct={ct} len={len(r.text)}")
            j = r.json()
            data = j.get("data", [])
            members = [row for row in data if row.get("symbol") and row.get("symbol") != idx]
            print(f"  rows={len(data)} members={len(members)} timestamp={j.get('timestamp')}")
            for row in members[:3]:
                print("   ", row.get("symbol"), "—", (row.get("meta") or {}).get("companyName"))
        except Exception as e:
            body = locals().get("r")
            head = (body.text[:160].replace("\n", " ")) if body is not None else ""
            print(f"\n{idx}: FAILED {type(e).__name__}: {e} | body head: {head}")
        time.sleep(1.5)
