# The /IndexConstituent/<bad> path returns an Angular SPA shell. Mine its bundles for
# the authoritative index list / CSV-filename map (same trick that cracked BSE).
import requests, re
from urllib.parse import urljoin

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
H = {"User-Agent": UA, "Referer": "https://www.niftyindices.com/", "Accept": "*/*"}
s = requests.Session()

shell = s.get("https://niftyindices.com/IndexConstituent/ind_niftyalpha50list.csv",
              headers=H, timeout=20).text
print("shell len:", len(shell))
scripts = [urljoin("https://niftyindices.com/", x)
           for x in re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', shell)]
links = [urljoin("https://niftyindices.com/", x)
         for x in re.findall(r'href=["\']([^"\']+\.(?:js|json)[^"\']*)["\']', shell)]
print("scripts:", scripts)
print("asset links:", [l for l in links if l.endswith(".json")][:20])

pat_csv = re.compile(r'ind_[A-Za-z0-9_]*list\.csv')
pat_const = re.compile(r'[A-Za-z]*[Cc]onstituent[A-Za-z]*')
found_csv, found_const, found_api = set(), set(), set()
for url in scripts:
    if "niftyindices.com" not in url:
        continue
    try:
        js = s.get(url, headers=H, timeout=30).text
    except Exception as e:
        print("ERR", url, e); continue
    found_csv |= set(pat_csv.findall(js))
    found_const |= set(pat_const.findall(js))
    found_api |= set(re.findall(r'["\'`](/?[A-Za-z0-9_./-]*(?:IndexConstituent|getIndex|indexlist|IndexList|getEquity)[A-Za-z0-9_./-]*)["\'`]', js))

print("\n=== ind_*list.csv literals in bundles ===", sorted(found_csv)[:40])
print("\n=== 'constituent' tokens ===", sorted(found_const)[:30])
print("\n=== index/constituent endpoints ===", sorted(found_api)[:30])
