# Phase 0 sanity probe — NSE + BSE reachability and parsing from this (residential) IP.
# Resolves: NSE coverage (full index list), per-index constituent fetch, BSE code/endpoint validity.
import json, time, sys, urllib.parse, os
import requests
from nsepython import nse_get_index_list, nsefetch

HERE = os.path.dirname(os.path.abspath(__file__))

def line(c="-"): print(c * 70)

# ---------------------------------------------------------------- NSE: coverage
def nse_coverage():
    line("="); print("NSE INDEX LIST (nse_get_index_list)"); line("=")
    t = time.time()
    names = nse_get_index_list()
    print(f"count={len(names)} fetched in {round(time.time()-t,1)}s")
    with open(os.path.join(HERE, "nse_index_list.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(names)))
    print("-> full list written to phase0/nse_index_list.txt")

    # crude keyword bucketing just to eyeball scope coverage
    buckets = {
        "broad":    ["NIFTY 50","NEXT 50","NIFTY 100","NIFTY 200","NIFTY 500","MIDCAP","SMALLCAP",
                     "MICROCAP","LARGEMIDCAP","TOTAL MARKET","MIDSMALLCAP"],
        "sectoral": ["BANK","IT","PHARMA","AUTO","FMCG","METAL","REALTY","MEDIA","ENERGY","PSU BANK",
                     "PRIVATE BANK","FINANCIAL","HEALTHCARE","CONSUMER DURABLE","OIL & GAS","CHEMICAL"],
        "thematic": ["CPSE","INFRA","MNC","COMMODITIES","CONSUMPTION","MANUFACTURING","MOBILITY","EV",
                     "DIGITAL","HOUSING","TOURISM","DEFENCE","RURAL","SME","IPO","REITS","CORE HOUSING"],
        "strategy": ["ALPHA","QUALITY","VALUE","MOMENTUM","LOW VOL","LOW-VOL","EQUAL WEIGHT","HIGH BETA",
                     "DIVIDEND","GROWTH SECTORS","VOL 30","ENHANCED"],
    }
    seen = set()
    for b, kws in buckets.items():
        hits = sorted({n for n in names if any(k in n.upper() for k in kws)})
        seen |= set(hits)
        print(f"\n[{b}] {len(hits)}")
        for n in hits: print("   ", n)
    other = sorted(set(names) - seen)
    print(f"\n[unbucketed] {len(other)}  (review these for missed scope)")
    for n in other: print("   ", n)
    return names

# ------------------------------------------------------- NSE: constituent fetch
def nse_constituents(index_name):
    url = "https://www.nseindia.com/api/equity-stockIndices?index=" + urllib.parse.quote(index_name)
    t = time.time()
    j = nsefetch(url)
    dt = round(time.time()-t, 2)
    rows = j.get("data", []) if isinstance(j, dict) else []
    members = []
    for r in rows:
        sym = r.get("symbol")
        if not sym or sym == index_name:      # skip the index-self summary row
            continue
        name = (r.get("meta") or {}).get("companyName") or sym
        members.append({"symbol": sym, "name": name})
    print(f"\n{index_name}: {len(members)} members in {dt}s  (raw rows={len(rows)})")
    for m in members[:5]:
        print("   ", m["symbol"], "—", m["name"])
    return members

def nse_fetch_test():
    line("="); print("NSE CONSTITUENT FETCH (2 indices)"); line("=")
    for idx in ["NIFTY 50", "NIFTY BANK"]:
        try:
            nse_constituents(idx)
            time.sleep(1.5)  # throttle
        except Exception as e:
            print(f"\n{idx}: FAILED -> {type(e).__name__}: {e}")

# ------------------------------------------------------------------- BSE probe
def bse_probe():
    line("="); print("BSE PROBE (candidate endpoints, code 16 = Sensex?)"); line("=")
    h = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.bseindia.com",
        "Referer": "https://www.bseindia.com/",
    }
    s = requests.Session()
    # prime cookies on the main site first
    try:
        r = s.get("https://www.bseindia.com/", headers=h, timeout=10)
        print(f"prime www.bseindia.com -> {r.status_code}, cookies={len(s.cookies)}")
    except Exception as e:
        print(f"prime FAILED -> {type(e).__name__}: {e}")

    candidates = [
        "https://api.bseindia.com/BseIndiaAPI/api/IndexConstituent/w?indexcode=16",
        "https://api.bseindia.com/BseIndiaAPI/api/ConstituentList/w?indxcode=16",
        "https://api.bseindia.com/BseIndiaAPI/api/GetIndexConstituents/w?Indx_code=16",
        "https://api.bseindia.com/BseIndiaAPI/api/GetSensexData/w?",
        "https://api.bseindia.com/BseIndiaAPI/api/SensexData/w?",
        "https://api.bseindia.com/BseIndiaAPI/api/Sensex/getSensexData/w?",
    ]
    for url in candidates:
        try:
            r = s.get(url, headers=h, timeout=10)
            snip = r.text[:160].replace("\n", " ")
            print(f"\n{r.status_code} len={len(r.text)}  {url}\n     {snip}")
        except Exception as e:
            print(f"\nERR {type(e).__name__}: {e}\n     {url}")
        time.sleep(1.0)

if __name__ == "__main__":
    nse_coverage()
    nse_fetch_test()
    bse_probe()
    line("="); print("PHASE 0 PROBE DONE"); line("=")
