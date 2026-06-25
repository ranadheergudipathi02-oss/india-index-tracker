"""Reset changes.jsonl to a pristine baseline that matches the current/ snapshots:
one {type:"initial"} entry per index, today's date, no diff history. Use to discard
test data or re-baseline after manual fixes. Does NOT touch current/.

Run:  python fetcher/reset_baseline.py
"""
import os, sys, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config as C
from datetime import datetime

date = datetime.now(C.IST).date().isoformat()
lines = []
for path in sorted(glob.glob(os.path.join(C.CURRENT_DIR, "*.json"))):
    doc = json.load(open(path, encoding="utf-8"))
    added = [{"symbol": m["symbol"], "name": m.get("name", "")} for m in doc["members"]]
    lines.append(json.dumps({"date": date, "index": doc["id"], "type": "initial",
                             "added": added, "removed": []}, ensure_ascii=False))

with open(C.CHANGES_FILE, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines) + "\n")
print(f"reset changes.jsonl -> {len(lines)} initial entries (date {date})")
