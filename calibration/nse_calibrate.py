# Build the NSE in-scope equity index -> niftyindices constituent-CSV map.
# Scope filter drops fixed-income/leverage/USD; slug resolver verifies each CSV by HTTP.
import requests, io, csv, time, os, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES_FILE = os.path.join(HERE, "..", "phase0", "nse_index_list.txt")
OUT = os.path.join(HERE, "maps"); os.makedirs(OUT, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
H = {"User-Agent": UA, "Referer": "https://www.niftyindices.com/",
     "Accept": "text/csv,application/csv,*/*", "Accept-Language": "en-US,en;q=0.9"}

# --- scope filter: exclude non-equity (fixed income, leverage, USD, etc.) -------
EXCLUDE = ["G-SEC", "GS ", "GSEC", "SDL", "BHARATBOND", "BHARAT BOND", "BOND", "AAA",
           "SOVEREIGN", "HTM", "1D RATE", "5YR BENCHMARK", "COMPSITE", "MAATR",
           "PR 1X", "PR 2X", "TR 1X", "TR 2X", "2X LEV", "1X INV", " USD", "USD",
           "MULTI ASSET", "FAR SELECT", "DIV POINT", "VIX", "REITS", "INVITS"]
def in_scope(name):
    u = name.upper()
    return not any(k in u for k in EXCLUDE)

with open(NAMES_FILE, encoding="utf-8") as f:
    names = [ln.strip() for ln in f if ln.strip()]
scope = [n for n in names if in_scope(n)]
print(f"total={len(names)}  in-scope(equity)={len(scope)}  dropped={len(names)-len(scope)}\n")

# --- slug candidates -----------------------------------------------------------
def core(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())
def candidates(name):
    c = core(name)
    base = c[6:] if c.startswith("nifty") else c  # niftyindices files keep 'nifty'
    out = [f"ind_{c}list.csv", f"ind_{c}_list.csv"]
    if c != "nifty" + base:
        out += [f"ind_nifty{base}list.csv"]
    # dedupe preserve order
    seen, res = set(), []
    for x in out:
        if x not in seen:
            seen.add(x); res.append(x)
    return res

def valid_csv(text):
    head = text[:300].lower()
    return ("symbol" in head and "company name" in head and "<html" not in head)

resolved, unresolved = [], []
s = requests.Session()
for name in scope:
    hit = None
    for fn in candidates(name):
        url = "https://niftyindices.com/IndexConstituent/" + fn
        try:
            r = s.get(url, headers=H, timeout=15)
        except Exception:
            continue
        if r.status_code == 200 and valid_csv(r.text):
            rows = list(csv.DictReader(io.StringIO(r.text)))
            hit = {"name": name, "csv": fn, "url": url, "members": len(rows)}
            break
        time.sleep(0.15)
    if hit:
        resolved.append(hit); print(f"  OK  {name:34} -> {hit['csv']:34} {hit['members']:>4}")
    else:
        unresolved.append(name); print(f"  ??  {name:34} (no CSV via simple slug)")
    time.sleep(0.25)

print(f"\nRESOLVED {len(resolved)}/{len(scope)}   UNRESOLVED {len(unresolved)}")
print("\nUNRESOLVED (need manual slug / different source):")
for n in unresolved:
    print("   ", n)

with open(os.path.join(OUT, "nse_index_map.json"), "w", encoding="utf-8") as f:
    json.dump({"resolved": resolved, "unresolved": unresolved}, f, indent=2)
print(f"\n-> saved maps/nse_index_map.json")
