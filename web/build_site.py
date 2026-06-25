"""Generate the two aggregates the static frontend can't cheaply derive client-side:
  assets/directory.json  — categorized index directory (+ count, file, last_changed)
  assets/stocks.json     — reverse index: stock (by ISIN) -> indices it belongs to
Reads current/*.json + changes.jsonl + meta.json. Run after fetch.py.
"""
import os, sys, json, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fetcher"))
import config as C

ASSETS = os.path.join(C.PROJECT_ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)


def pad(name):
    return f" {name.upper()} "

def categorize(name):
    u = name.upper()
    p = pad(name)
    if any(k in u for k in ["ALPHA", "QUALITY", "QUALTY", "QLTY", "VALUE", "MOMENT",
                            "LOW VOL", "LOWVOL", "LOW VOLATILITY", "EQL WGT", "EQUAL WEIGHT",
                            "HIGHBETA", "HIGH BETA", "MULTIFACTOR", "MQVLV", "ENHANCED VALUE",
                            "DIVIDEND", "DIV OPPS"]) or " EW " in p or " MQ " in p or " AQL" in p:
        return "Strategy / Factor"
    if any(k in u for k in ["NIFTY 50", "NIFTY 100", "NIFTY 200", "NIFTY 500", "NEXT 50",
                            "MIDCAP", "SMLCAP", "SMALLCAP", "MICROCAP", "LARGEMID", "TOTAL MKT",
                            "TOTAL MARKET", "MIDSML", "MID SELECT", "FLEXICAP", "MULTICAP",
                            "SENSEX", "BSE 100", "BSE 200", "BSE 500", "BSE 1000", "BSE 150",
                            "BSE 250", "BSE 400", "BHARAT 22", "LARGECAP", "INDIA 150"]):
        return "Broad market"
    if any(k in u for k in ["BANK", "PHARMA", "AUTO", "FMCG", "METAL", "REALTY", "MEDIA",
                            "ENERGY", "FIN", "HEALTH", "CONSR DURBL", "CONSUMER DUR", "OIL",
                            "CHEMICAL", "CAPITAL MKT", "CAPITAL MARKET", "TELECOM", "TELCOM",
                            "POWER", "UTILIT", "INDUSTRIAL", "SERVICES", "SERV SECTOR", "TECK",
                            "INFORMATION TECH", "CAPITAL GOODS", "HOSPITAL", "INSURANCE",
                            "CONSUMER DURABLES"]) or " IT " in p or " HC " in p:
        return "Sectoral"
    return "Thematic"


def load_last_changed():
    last = {}
    if os.path.exists(C.CHANGES_FILE):
        for line in open(C.CHANGES_FILE, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            e = json.loads(line)
            d = e["date"]
            if e["index"] not in last or d > last[e["index"]]["date"]:
                last[e["index"]] = {"date": d, "type": e["type"]}
    return last


def main():
    meta = json.load(open(C.META_FILE, encoding="utf-8"))
    last_changed = load_last_changed()

    directory = []
    for iid, m in meta["indices"].items():
        if m["status"] not in ("ok", "guard_skipped"):
            continue
        ex, name = iid.split(":", 1)
        lc = last_changed.get(iid, {})
        directory.append({"id": iid, "exchange": ex, "name": name, "count": m.get("count"),
                          "file": m.get("file"), "category": categorize(name),
                          "last_changed": lc.get("date"), "last_change_type": lc.get("type")})
    directory.sort(key=lambda d: (d["exchange"], d["category"], d["name"]))

    # reverse index: ISIN -> stock + indices it's in
    stocks = {}
    for path in glob.glob(os.path.join(C.CURRENT_DIR, "*.json")):
        doc = json.load(open(path, encoding="utf-8"))
        iid = doc["id"]
        for mem in doc["members"]:
            key = mem.get("isin") or f'{doc["exchange"]}:{mem["symbol"]}'
            s = stocks.setdefault(key, {"isin": mem.get("isin", ""), "name": mem.get("name", ""),
                                        "symbols": {}, "indices": []})
            if mem.get("name") and len(mem["name"]) > len(s["name"]):
                s["name"] = mem["name"]
            s["symbols"][doc["exchange"]] = mem["symbol"]
            s["indices"].append(iid)
    stock_list = sorted(({"isin": s["isin"], "name": s["name"], "symbols": s["symbols"],
                          "indices": sorted(set(s["indices"]))} for s in stocks.values()),
                        key=lambda s: s["name"])

    json.dump(directory, open(os.path.join(ASSETS, "directory.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    json.dump(stock_list, open(os.path.join(ASSETS, "stocks.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))

    cats = {}
    for d in directory:
        cats[f'{d["exchange"]} · {d["category"]}'] = cats.get(f'{d["exchange"]} · {d["category"]}', 0) + 1
    print(f"directory.json: {len(directory)} indices")
    for k in sorted(cats):
        print(f"   {k}: {cats[k]}")
    print(f"stocks.json: {len(stock_list)} unique stocks")


if __name__ == "__main__":
    main()
