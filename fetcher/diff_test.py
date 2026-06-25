# Fast, deterministic unit test of the diff logic (no network).
import diff

old = [{"symbol": "A", "name": "Alpha"}, {"symbol": "B", "name": "Bravo"},
       {"symbol": "C", "name": "Charlie"}]
new = [{"symbol": "B", "name": "Bravo"}, {"symbol": "C", "name": "Charlie Renamed"},
       {"symbol": "D", "name": "Delta"}]

added, removed = diff.compute_diff(old, new)
assert [m["symbol"] for m in added] == ["D"], added
assert [m["symbol"] for m in removed] == ["A"], removed
# C was renamed but stayed a member -> NOT a membership change
assert "C" not in [m["symbol"] for m in added + removed]

# no change
a2, r2 = diff.compute_diff(old, old)
assert a2 == [] and r2 == []

print("diff_test OK: added=D, removed=A, rename-of-C ignored, no-op diff empty")
