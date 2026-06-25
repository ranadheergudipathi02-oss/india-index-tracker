import nsepython, json, urllib.parse, time
from nsepython import nsefetch

print("index/const funcs:", [x for x in dir(nsepython) if 'index' in x.lower() or 'const' in x.lower()])
print("nsefetch module:", getattr(nsefetch, "__module__", "?"))

url = "https://www.nseindia.com/api/equity-stockIndices?index=" + urllib.parse.quote("NIFTY 50")
print("\nURL:", url)
for attempt in (1, 2):
    j = nsefetch(url)
    print(f"\nattempt {attempt}: type={type(j).__name__}")
    if isinstance(j, dict):
        print("  keys:", list(j.keys()))
        print("  data len:", len(j.get("data", [])))
        print("  snippet:", json.dumps(j)[:500])
    else:
        print("  raw:", str(j)[:500])
    time.sleep(2)
