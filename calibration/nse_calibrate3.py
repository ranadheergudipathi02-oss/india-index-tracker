# Final NSE pass: curated candidate cores for the 50 stragglers, with retry on
# non-200 (to defeat transient throttling), merged into the final map.
import requests, io, csv, time, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "maps")
MAP = os.path.join(OUT, "nse_index_map.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
H = {"User-Agent": UA, "Referer": "https://www.niftyindices.com/", "Accept": "text/csv,*/*"}

# straggler -> candidate cores (between 'ind_' and 'list.csv'/'_list.csv')
CURATED = {
    "NIFTY ALPHA 50": ["niftyalpha50"],
    "NIFTY ALPHALOWVOL": ["niftyalphalowvolatility30", "niftyalphalowvol30"],
    "NIFTY AQL 30": ["niftyalphaqualitylowvolatility30"],
    "NIFTY AQLV 30": ["niftyalphaqualityvaluelowvolatility30"],
    "NIFTY CAPITAL MKT": ["niftycapitalmarkets"],
    "NIFTY DIV OPPS 50": ["niftydividendopportunities50"],
    "NIFTY EV": ["niftyevnewageautomotive", "niftyev"],
    "NIFTY FIN SERVICE": ["niftyfinancialservices"],
    "NIFTY FINSRV25 50": ["niftyfinancialservices2550"],
    "NIFTY FPI 150": ["niftyfpi150"],
    "NIFTY GROWSECT 15": ["niftygrowthsectors15"],
    "NIFTY HIGHBETA 50": ["niftyhighbeta50"],
    "NIFTY HOUSING": ["niftyhousing"],
    "NIFTY INDIA CORPORATE GROUP INDEX - ADITYA BIRLA GROUP":
        ["niftyindiacorporategroupindexadityabirlagroup", "niftyadityabirlagroup"],
    "NIFTY INDIA CORPORATE GROUP INDEX - MAHINDRA GROUP":
        ["niftyindiacorporategroupindexmahindragroup", "niftymahindragroup"],
    "NIFTY INDIA CORPORATE GROUP INDEX - TATA GROUP":
        ["niftyindiacorporategroupindextatagroup", "niftytatagroup"],
    "NIFTY INFRALOG": ["niftyinfrastructurelogistics", "niftyindiainfrastructurelogistics"],
    "NIFTY INTERNET": ["niftyinternet"],
    "NIFTY LOW VOL 50": ["niftylowvolatility50"],
    "NIFTY MID LIQ 15": ["niftymidcapliquid15", "niftymidliq15"],
    "NIFTY MS FIN SERV": ["niftymidsmallfinancialservices", "niftymidsmallcapfinancialservices"],
    "NIFTY MS IT TELCM": ["niftymidsmallittelecom", "niftymidsmallcapittelecom"],
    "NIFTY MULTI INFRA": ["niftymultiinfrastructure", "niftymultiinfra"],
    "NIFTY MULTI MFG": ["niftymultimanufacturing", "niftymultimfg"],
    "NIFTY MULTI MQ 50": ["niftymultimomentumquality50", "niftymultimq50"],
    "NIFTY NEW CONSUMP": ["niftynewageconsumption", "niftyindianewageconsumption", "niftynewconsumption"],
    "NIFTY NONCYC CONS": ["niftynoncyclicalconsumer"],
    "NIFTY PVT BANK": ["niftyprivatebank"],
    "NIFTY QLTY LV 30": ["niftyqualitylowvolatility30"],
    "NIFTY SERV SECTOR": ["niftyservicessector", "niftyservicesector"],
    "NIFTY SHARIAH 25": ["niftyshariah25"],
    "NIFTY SME EMERGE": ["niftysmeemerge", "niftyemerge"],
    "NIFTY SML250 Q50": ["niftysmallcap250quality50"],
    "NIFTY TATA 25 CAP": ["niftytatagroup25cap", "niftytata25cap"],
    "NIFTY TMMQ 50": ["niftytotalmarketmomentumquality50", "niftytmmq50"],
    "NIFTY TRANS LOGIS": ["niftytransportationlogistics", "niftytransportationandlogistics"],
    "NIFTY100 ENH ESG": ["nifty100enhancedesg"],
    "NIFTY100 EQL WGT": ["nifty100equalweight"],
    "NIFTY100 ESG": ["nifty100esg"],
    "NIFTY100 LIQ 15": ["nifty100liquid15"],
    "NIFTY50 EQL WGT": ["nifty50equalweight"],
    "NIFTY50 SHARIAH": ["nifty50shariah"],
    "NIFTY50 VALUE 20": ["nifty50value20"],
    "NIFTY500 FLEXICAP": ["nifty500flexicap"],
    "NIFTY500 HEALTH": ["nifty500healthcare", "nifty500health"],
    "NIFTY500 LMS EQL": ["nifty500largemidsmallequalcapweighted", "nifty500lmsequalcapweighted"],
    "NIFTY500 MULTICAP": ["nifty500multicap502525", "nifty500multicap"],
    "NIFTY500 SHARIAH": ["nifty500shariah"],
    "NIFTYMS400 MQ 100": ["niftymidsmallcap400momentumquality100"],
    "NIFTYSML250MQ 100": ["niftysmallcap250momentumquality100"],
}

def valid(t):
    h = t[:300].lower(); return "symbol" in h and "company name" in h and "<html" not in h

def fetch(url, retries=2):
    for i in range(retries):
        try:
            r = requests.get(url, headers=H, timeout=15)
            if r.status_code == 200 and valid(r.text):
                return r
            if r.status_code != 200:
                time.sleep(1.0)  # back off transient throttling
        except Exception:
            time.sleep(1.0)
    return None

data = json.load(open(MAP, encoding="utf-8"))
resolved = {r["name"]: r for r in data["resolved"]}
by_file = {r["csv"]: r["name"] for r in data["resolved"] if not r.get("alias_of")}
still = []
for name in data["unresolved"]:
    hit = None
    for core in CURATED.get(name, []):
        for fn in (f"ind_{core}list.csv", f"ind_{core}_list.csv"):
            r = fetch("https://niftyindices.com/IndexConstituent/" + fn)
            if r:
                rows = list(csv.DictReader(io.StringIO(r.text)))
                hit = {"name": name, "csv": fn, "url": "https://niftyindices.com/IndexConstituent/" + fn,
                       "members": len(rows), "alias_of": by_file.get(fn)}
                by_file.setdefault(fn, name); break
            time.sleep(0.3)
        if hit: break
    if hit:
        resolved[name] = hit
        tag = f"  (alias of {hit['alias_of']})" if hit["alias_of"] else ""
        print(f"  OK  {name:38} -> {hit['csv']:46} {hit['members']:>4}{tag}")
    else:
        still.append(name); print(f"  ??  {name}")

allres = list(resolved.values())
uniq = [r for r in allres if not r.get("alias_of")]
print(f"\nFINAL: resolved {len(allres)}  (unique files {len(uniq)})   unresolved {len(still)}")
print("UNRESOLVED:", still)
json.dump({"resolved": allres, "unresolved": still}, open(MAP, "w", encoding="utf-8"), indent=2)
print("-> updated maps/nse_index_map.json")
