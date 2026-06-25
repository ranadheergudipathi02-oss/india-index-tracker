# NSE calibration v2: expand NSE's abbreviated names to niftyindices' full-word slugs,
# generate multiple candidates per index, verify each by HTTP, dedupe by resolved file.
import requests, io, csv, time, os, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES_FILE = os.path.join(HERE, "..", "phase0", "nse_index_list.txt")
OUT = os.path.join(HERE, "maps"); os.makedirs(OUT, exist_ok=True)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
H = {"User-Agent": UA, "Referer": "https://www.niftyindices.com/",
     "Accept": "text/csv,*/*", "Accept-Language": "en-US,en;q=0.9"}

EXCLUDE = ["G-SEC", "GS ", "GSEC", "SDL", "BHARATBOND", "BHARAT BOND", "BOND", "AAA",
           "SOVEREIGN", "HTM", "1D RATE", "5YR BENCHMARK", "COMPSITE", "MAATR",
           "PR 1X", "PR 2X", "TR 1X", "TR 2X", "2X LEV", "1X INV", "USD",
           "MULTI ASSET", "FAR SELECT", "DIV POINT", "VIX", "REITS", "INVITS",
           "ARBITRAGE", "FUTURES"]

# multi-word / abbreviation expansions, applied to the lower-cased spaced name.
# order matters: longer / more specific first.
EXPAND = [
    ("oil and gas", "oilgas"), ("consr durbl", "consumerdurables"),
    ("fin service", "financialservices"), ("finserexbnk", "financialservicesexbank"),
    ("finsrv25 50", "financialservices2550"), ("pvt bank", "privatebank"),
    ("serv sector", "servicessector"), ("total mkt", "totalmarket"),
    ("div opps", "dividendopportunities"), ("growsect", "growthsectors"),
    ("noncyc cons", "noncyclicalconsumer"), ("new consump", "newageconsumption"),
    ("ind defence", "indiadefence"), ("ind digital", "indiadigital"),
    ("ind tourism", "indiatourism"), ("india mfg", "indiamanufacturing"),
    ("ms fin serv", "midsmallfinancialservices"), ("ms ind cons", "midsmallindiaconsumption"),
    ("ms it telcm", "midsmallittelecom"), ("midsml hlth", "midsmallhealthcare"),
    ("midsml", "midsmallcap"), ("largemid", "largemidcap"),
    ("mid liq", "midcapliquid"), ("mid select", "midcapselect"),
    ("enh esg", "enhancedesg"), ("liq 15", "liquid15"),
    ("qlty lv", "qualitylowvolatility"), ("low vol", "lowvolatility"),
    ("lowvol", "lowvolatility"), ("alphalowvol", "alphalowvolatility"),
    ("highbeta", "highbeta"), ("smlcap", "smallcap"), ("sml250", "smallcap250"),
    ("sml ", "smallcap "), ("qualty", "quality"), ("qlty", "quality"),
    ("momentm", "momentum"), ("momntm", "momentum"), ("eql wgt", "equalweight"),
    (" ew", " equalweight"), ("mqvlv", "multifactormqvlv"),
    ("m150", "midcap150"), ("m 150", "midcap150"),
]
def expand(name):
    s = name.lower()
    for a, b in EXPAND:
        s = s.replace(a, b)
    return s
def core(s):
    return re.sub(r"[^a-z0-9]", "", s)
def candidates(name):
    cores = []
    raw = core(name.lower())
    exp = core(expand(name))
    for c in (raw, exp):
        if c and c not in cores:
            cores.append(c)
    files = []
    for c in cores:
        for fn in (f"ind_{c}list.csv", f"ind_{c}_list.csv"):
            if fn not in files:
                files.append(fn)
    return files

def valid(text):
    head = text[:300].lower()
    return "symbol" in head and "company name" in head and "<html" not in head

with open(NAMES_FILE, encoding="utf-8") as f:
    names = sorted({ln.strip() for ln in f if ln.strip()})
scope = [n for n in names if not any(k in n.upper() for k in EXCLUDE)]
print(f"in-scope(equity)={len(scope)}\n")

s = requests.Session()
by_file = {}        # csv filename -> first index that resolved it
resolved, unresolved = [], []
for name in scope:
    hit = None
    for fn in candidates(name):
        url = "https://niftyindices.com/IndexConstituent/" + fn
        try:
            r = s.get(url, headers=H, timeout=15)
        except Exception:
            continue
        if r.status_code == 200 and valid(r.text):
            rows = list(csv.DictReader(io.StringIO(r.text)))
            hit = {"name": name, "csv": fn, "url": url, "members": len(rows),
                   "alias_of": by_file.get(fn)}
            by_file.setdefault(fn, name)
            break
        time.sleep(0.1)
    if hit:
        resolved.append(hit)
        tag = f"  (alias of {hit['alias_of']})" if hit["alias_of"] else ""
        print(f"  OK  {name:34} -> {hit['csv']:38} {hit['members']:>4}{tag}")
    else:
        unresolved.append(name); print(f"  ??  {name}")
    time.sleep(0.15)

uniq = [r for r in resolved if not r["alias_of"]]
print(f"\nRESOLVED {len(resolved)}  (unique files {len(uniq)})   UNRESOLVED {len(unresolved)}")
print("\nUNRESOLVED:")
for n in unresolved: print("   ", n)
with open(os.path.join(OUT, "nse_index_map.json"), "w", encoding="utf-8") as f:
    json.dump({"resolved": resolved, "unresolved": unresolved}, f, indent=2)
print("\n-> saved maps/nse_index_map.json")
