# Find the SECOND call in Data() (the real constituents fetch) and how iname is set.
import requests, re

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
h = {"User-Agent": UA, "Accept": "*/*", "Referer": "https://www.bseindia.com/"}
s = requests.Session()
blob = ""
for u in ["https://www.bseindia.com/assets/includenew/js/scripts-OXCQKZIU.js",
          "https://www.bseindia.com/assets/includenew/js/main-WDSOQSQ3.js"]:
    blob += "\n" + s.get(u, headers=h, timeout=30).text

def show(label, pattern, before=40, after=600, limit=4):
    print("\n" + "=" * 70 + f"\n{label}  (/{pattern}/)")
    seen = set()
    for m in re.finditer(pattern, blob):
        a, b = max(0, m.start() - before), min(len(blob), m.end() + after)
        ctx = blob[a:b].replace("\n", " ")
        if ctx[:100] in seen:
            continue
        seen.add(ctx[:100])
        print("  …", ctx, "\n")
        if len(seen) >= limit:
            break

# the whole Data() body that loads constituents
show("Data() body after flag call", r'indicesWatchWeight\+"\?flag="', after=700)
# usage of the weight endpoint (not the definition map)
show("nSIndexWeightSPDJ usage", r'\.nSIndexWeightSPDJ\b', after=300)
# how iname is set
show("this.iname assignment", r'\.iname\s*=', before=20, after=120)
# the ?iname= query template
show("?iname= template", r'\?iname=', before=80, after=200)
