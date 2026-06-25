# Isolate: are the "should-work" filenames wrong, or is niftyindices throttling the burst?
import requests, time

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
H = {"User-Agent": UA, "Referer": "https://www.niftyindices.com/", "Accept": "text/csv,*/*"}
s = requests.Session()
files = [
    "ind_nifty50list.csv",                 # control (known good)
    "ind_niftyalpha50list.csv",
    "ind_niftyalpha50_list.csv",
    "ind_niftyprivatebanklist.csv",
    "ind_niftyprivatebank_list.csv",
    "ind_nifty100equalweightlist.csv",
    "ind_nifty100equalweight_list.csv",
    "ind_niftyhousinglist.csv",
    "ind_niftyhousing_list.csv",
    "ind_niftyinternetlist.csv",
    "ind_nifty50shariahlist.csv",
    "ind_nifty50shariah_list.csv",
]
for fn in files:
    url = "https://niftyindices.com/IndexConstituent/" + fn
    try:
        r = s.get(url, headers=H, timeout=15)
        head = r.text[:70].replace("\n", " ")
        print(f"{r.status_code} ct={r.headers.get('content-type','')[:25]:25} len={len(r.text):>6}  {fn}\n      {head}")
    except Exception as e:
        print(f"ERR {type(e).__name__}: {e}  {fn}")
    time.sleep(1.5)
