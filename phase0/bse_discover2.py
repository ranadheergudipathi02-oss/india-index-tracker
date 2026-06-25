# Read the call-site context around the promising BSE endpoints to learn exact
# query-param names (ASP.NET routes are exact; no more guessing).
import requests, re

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
h = {"User-Agent": UA, "Accept": "*/*", "Referer": "https://www.bseindia.com/"}
s = requests.Session()

bundles = [
    "https://www.bseindia.com/assets/includenew/js/scripts-OXCQKZIU.js",
    "https://www.bseindia.com/assets/includenew/js/main-WDSOQSQ3.js",
]
blob = ""
for u in bundles:
    try:
        blob += "\n" + s.get(u, headers=h, timeout=30).text
    except Exception as e:
        print("ERR", u, e)

targets = ["NS_IndexWeight_SPDJ_ng", "NS_IndexWeight_SPDJ_Download_ng", "IndexMasterNew_ng",
           "IndexList/w", "GetGroupIndex", "GetIndexDetails", "Index_Constituents", "Mkt_BSE_Index_ng"]

for t in targets:
    print("\n" + "=" * 70 + f"\nTARGET: {t}")
    seen = set()
    for m in re.finditer(re.escape(t), blob):
        a = max(0, m.start() - 90)
        b = min(len(blob), m.end() + 260)
        ctx = blob[a:b].replace("\n", " ")
        key = ctx[:120]
        if key in seen:
            continue
        seen.add(key)
        print("  …", ctx)
        if len(seen) >= 3:
            break
