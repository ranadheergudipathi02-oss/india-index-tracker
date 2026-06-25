# Discover real BSE API endpoints by grepping bseindia.com's JS bundles for
# string literals. ASP.NET/Angular front-ends embed every endpoint path.
import requests, re
from urllib.parse import urljoin

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
h = {"User-Agent": UA,
     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "Accept-Language": "en-US,en;q=0.9", "Referer": "https://www.bseindia.com/"}

s = requests.Session()
home = s.get("https://www.bseindia.com/", headers=h, timeout=20)
print("home:", home.status_code, "len", len(home.text))

scripts = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', home.text)
scripts = [urljoin("https://www.bseindia.com/", x) for x in scripts]
print(f"\n{len(scripts)} script tags:")
for x in scripts:
    print("  ", x)

pat_api = re.compile(r'(?:https?://[^"\'`]*?)?BseIndiaAPI/api/[A-Za-z0-9_]+(?:/w)?')
pat_kw  = re.compile(r'["\'`](/?[A-Za-z0-9_./]*[Cc]onstituent[A-Za-z0-9_./]*)["\'`]')
pat_idx = re.compile(r'["\'`](/?[A-Za-z0-9_./]*[Ii]ndex[A-Za-z0-9_./]*/w)["\'`]')

found_api, found_kw, found_idx = set(), set(), set()
for url in scripts:
    if "bseindia.com" not in url:
        continue
    try:
        js = s.get(url, headers={**h, "Accept": "*/*"}, timeout=30).text
    except Exception as e:
        print("  ERR", url, type(e).__name__, e); continue
    found_api |= set(pat_api.findall(js))
    found_kw  |= set(pat_kw.findall(js))
    found_idx |= set(pat_idx.findall(js))

print("\n=== BseIndiaAPI/api/* endpoints found ===")
for x in sorted(found_api): print("  ", x)
print("\n=== strings containing 'constituent' ===")
for x in sorted(found_kw): print("  ", x)
print("\n=== '*Index*/w' endpoint strings ===")
for x in sorted(found_idx): print("  ", x)
