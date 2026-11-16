"""edit_stable_sort.py : test-only edit — replace std::sort with std::stable_sort in pick_best.

The question: REPORT_pick_best.md found that 5 % of pick_best calls take the std::sort branch and that this
branch holds ~23 % of pick_best's local samples. Before anyone optimises it, the honest question is whether
the ORDER that sort produces matters at all. std::sort is NOT stable, so an equally-scored pair may come out
either way; if a stable sort gives different node counts, tie order matters and the sort is not freely
replaceable.

This edit changes ONLY the algorithm, not the comparator or the range.
"""

p = "src/search.cpp"
s = open(p).read()
old = """                std::sort(moves_.begin() + static_cast<std::ptrdiff_t>(index_),
                          moves_.begin() + static_cast<std::ptrdiff_t>(count_),
                          [](const Scored& a, const Scored& b) { return a.score > b.score; });"""
new = """                std::stable_sort(moves_.begin() + static_cast<std::ptrdiff_t>(index_),
                          moves_.begin() + static_cast<std::ptrdiff_t>(count_),
                          [](const Scored& a, const Scored& b) { return a.score > b.score; });"""
assert old in s
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("edit_stable_sort applied")
