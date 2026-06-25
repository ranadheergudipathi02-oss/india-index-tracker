"""Phase 2 diff engine: compare new constituents vs the previous current/ snapshot,
emit append-only change records. Membership identity is the symbol (NSE ticker / BSE
scrip code). Names are carried for readability; a name-only change is NOT a membership
change and is ignored here.
"""
import json
import config as C


def compute_diff(old_members, new_members):
    """Return (added, removed) as lists of {symbol,name}, keyed by symbol."""
    old = {m["symbol"]: m for m in old_members}
    new = {m["symbol"]: m for m in new_members}
    added = [{"symbol": s, "name": new[s].get("name", "")} for s in new if s not in old]
    removed = [{"symbol": s, "name": old[s].get("name", "")} for s in old if s not in new]
    return added, removed


def append_change(entry):
    """Append one JSON object as a line to changes.jsonl (append-only)."""
    with open(C.CHANGES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def make_entry(date_str, index_id, type_, added, removed):
    return {"date": date_str, "index": index_id, "type": type_,
            "added": added, "removed": removed}
