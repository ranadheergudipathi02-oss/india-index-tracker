# Consolidated NSE resolver: scope filter + expansion + curated overrides + LENIENT
# validator (accept any octet-stream CSV with Symbol+ISIN, regardless of header wording).
import requests, io, csv, time, os, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES_FILE = os.path.join(HERE, "..", "phase0", "nse_index_list.txt")
OUT = os.path.join(HERE, "maps"); os.makedirs(OUT, exist_ok=True)
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
H = {"User-Agent": UA, "Referer": "https://www.niftyindices.com/", "Accept": "text/csv,*/*"}

EXCLUDE = ["G-SEC", "GS ", "GSEC", "SDL", "BHARATBOND", "BHARAT BOND", "BOND", "AAA",
           "SOVEREIGN", "HTM", "1D RATE", "5YR BENCHMARK", "COMPSITE", "MAATR",
           "PR 1X", "PR 2X", "TR 1X", "TR 2X", "2X LEV", "1X INV", "USD",
           "MULTI ASSET", "FAR SELECT", "DIV POINT", "VIX", "REITS", "INVITS",
           "ARBITRAGE", "FUTURES"]
EXPAND = [
    ("oil and gas","oilgas"),("consr durbl","consumerdurables"),("fin service","financialservices"),
    ("finserexbnk","financialservicesexbank"),("finsrv25 50","financialservices2550"),
    ("pvt bank","privatebank"),("serv sector","servicessector"),("total mkt","totalmarket"),
    ("div opps","dividendopportunities"),("growsect","growthsectors"),("noncyc cons","noncyclicalconsumer"),
    ("new consump","indianewageconsumption"),("ind defence","indiadefence"),("ind digital","indiadigital"),
    ("ind tourism","indiatourism"),("india mfg","indiamanufacturing"),("ms fin serv","midsmallfinancialservices"),
    ("ms ind cons","midsmallindiaconsumption"),("ms it telcm","midsmallittelecom"),("midsml hlth","midsmallhealthcare"),
    ("midsml","midsmallcap"),("largemid","largemidcap"),("mid liq","midcapliquid"),("mid select","midcapselect"),
    ("enh esg","enhancedesg"),("liq 15","liquid15"),("qlty lv","qualitylowvolatility"),("low vol","lowvolatility"),
    ("lowvol","lowvolatility"),("alphalowvol","alphalowvolatility"),("smlcap","smallcap"),("sml250","smallcap250"),
    ("qualty","quality"),("qlty","quality"),("momentm","momentum"),("momntm","momentum"),
    ("eql wgt","equalweight"),(" ew","equalweight"),("mqvlv","multifactormqvlv"),("m150","midcap150"),
]
CURATED = {  # name -> candidate cores (verified-or-best-guess)
    "NIFTY CAPITAL MKT": ["niftycapitalmarkets"], "NIFTY NEW CONSUMP": ["niftyindianewageconsumption"],
    "NIFTY TMMQ 50": ["niftytotalmarketmomentumquality50"], "NIFTY TRANS LOGIS": ["niftytransportationandlogistics"],
    "NIFTY500 HEALTH": ["nifty500healthcare"], "NIFTY500 LMS EQL": ["nifty500largemidsmallequalcapweighted"],
    "NIFTY500 MULTICAP": ["nifty500multicap502525"], "NIFTYMS400 MQ 100": ["niftymidsmallcap400momentumquality100"],
    "NIFTYSML250MQ 100": ["niftysmallcap250momentumquality100"], "NIFTY HOUSING": ["niftyhousing"],
}
def expand(n):
    s = n.lower()
    for a, b in EXPAND: s = s.replace(a, b)
    return s
def cores(n):
    out = []
    for c in (re.sub(r"[^a-z0-9]","",n.lower()), re.sub(r"[^a-z0-9]","",expand(n))) + tuple(CURATED.get(n, [])):
        if c and c not in out: out.append(c)
    return out
def files(n):
    fs = []
    for c in cores(n):
        for fn in (f"ind_{c}list.csv", f"ind_{c}_list.csv"):
            if fn not in fs: fs.append(fn)
    return fs
def ok(r):
    if "html" in r.headers.get("content-type", ""): return False
    h = r.text[:400].lower()
    return "symbol" in h and "isin" in h and "<html" not in h

names = sorted({ln.strip() for ln in open(NAMES_FILE, encoding="utf-8") if ln.strip()})
scope = [n for n in names if not any(k in n.upper() for k in EXCLUDE)]
s = requests.Session()
by_file, resolved, unresolved = {}, [], []
for n in scope:
    hit = None
    for fn in files(n):
        url = "https://niftyindices.com/IndexConstituent/" + fn
        r = None
        for _ in range(2):
            try:
                r = s.get(url, headers=H, timeout=15)
                if r.status_code == 200: break
                time.sleep(0.8)
            except Exception:
                r = None; time.sleep(0.8)
        if r is not None and r.status_code == 200 and ok(r):
            rows = list(csv.DictReader(io.StringIO(r.text)))
            sym = "Symbol"
            hit = {"name": n, "csv": fn, "url": url, "members": len(rows),
                   "alias_of": by_file.get(fn)}
            by_file.setdefault(fn, n); break
        time.sleep(0.2)
    (resolved if hit else unresolved).append(hit or n)
    if hit:
        print(f"  OK {n:36} {hit['csv']:48} {hit['members']:>4}" + (f"  (alias {hit['alias_of']})" if hit['alias_of'] else ""))
    time.sleep(0.15)

uniq = [r for r in resolved if not r["alias_of"]]
print(f"\nFINAL NSE: resolved {len(resolved)} (unique files {len(uniq)}), unresolved {len(unresolved)} of {len(scope)} in-scope")
print("\nUNRESOLVED (backlog — known indices, filename TBD):")
for n in unresolved: print("   ", n)
json.dump({"resolved": resolved, "unresolved": unresolved, "in_scope": len(scope)},
          open(os.path.join(OUT, "nse_index_map.json"), "w", encoding="utf-8"), indent=2)
print("\n-> saved maps/nse_index_map.json")
