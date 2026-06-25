# Fetcher configuration: paths, headers, throttle/retry, correctness-guard thresholds.
import os
from datetime import timezone, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS_DIR    = os.path.join(PROJECT_ROOT, "calibration", "maps")   # produced by calibration/
CURRENT_DIR  = os.path.join(PROJECT_ROOT, "current")              # current/<slug>.json
META_FILE    = os.path.join(PROJECT_ROOT, "meta.json")
CHANGES_FILE = os.path.join(PROJECT_ROOT, "changes.jsonl")        # append-only diff log

IST = timezone(timedelta(hours=5, minutes=30))   # detection timestamps in IST

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
NSE_HEADERS = {"User-Agent": UA, "Referer": "https://www.niftyindices.com/",
               "Accept": "text/csv,*/*", "Accept-Language": "en-US,en;q=0.9"}
BSE_BASE = "https://api.bseindia.com/BseIndiaAPI/api"
BSE_HEADERS = {"User-Agent": UA, "Accept": "application/json, text/plain, */*",
               "Origin": "https://www.bseindia.com", "Referer": "https://www.bseindia.com/"}

# survival: throttle between requests + retry with backoff (NSE/BSE block aggressive clients)
NSE_SLEEP = 0.35
BSE_SLEEP = 0.6
RETRIES = 3
RETRY_BACKOFF = 2.0          # seconds * attempt

# correctness guard: never overwrite a healthy snapshot with a suspiciously short fetch
SHRINK_GUARD = 0.5           # skip write if new_count < prev_count * SHRINK_GUARD
