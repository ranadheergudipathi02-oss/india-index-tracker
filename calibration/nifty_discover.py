# Discover how niftyindices.com identifies indices + serves constituents, so we can
# map NSE's abbreviated index names -> the correct constituent source.
import requests, re
from urllib.parse import urljoin

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
h = {"User-Agent": UA,
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "Accept-Language": "en-US,en;q=0.9", "Referer": "https://www.niftyindices.com/"}
s = requests.Session()
home = s.get("https://www.niftyindices.com/", headers=h, timeout=25)
print("home:", home.status_code, "len", len(home.text))

scripts = [urljoin("https://www.niftyindices.com/", x)
           for x in re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', home.text)]
print(f"\n{len(scripts)} scripts:")
for x in scripts:
    print("  ", x)

# refs already in the homepage HTML
print("\nhomepage csv/constituent refs:",
      sorted(set(re.findall(r'(ind_[A-Za-z0-9_]*list\.csv|IndexConstituent[^"\'<> ]*)', home.text)))[:20])

pat_csv = re.compile(r'ind_[A-Za-z0-9_]*list\.csv')
pat_const = re.compile(r'["\'`](/?[A-Za-z0-9_./]*[Cc]onstituent[A-Za-z0-9_./]*)["\'`]')
pat_api = re.compile(r'["\'`](/[A-Za-z][A-Za-z0-9_./]*(?:\.aspx|/w)?)["\'`]')
csv, const, api = set(), set(), set()
for url in scripts:
    if "niftyindices.com" not in url:
        continue
    try:
        js = s.get(url, headers={**h, "Accept": "*/*"}, timeout=30).text
    except Exception as e:
        print("  ERR", url, e); continue
    csv |= set(pat_csv.findall(js))
    const |= set(pat_const.findall(js))
    api |= {x for x in pat_api.findall(js) if any(k in x.lower() for k in ("index", "constituent", "equity", "watch", "getdata", "backpage"))}

print("\n=== ind_*list.csv literals ===");        [print("  ", x) for x in sorted(csv)]
print("\n=== 'constituent' strings ===");          [print("  ", x) for x in sorted(const)]
print("\n=== index/constituent-ish endpoints ===");[print("  ", x) for x in sorted(api)]
