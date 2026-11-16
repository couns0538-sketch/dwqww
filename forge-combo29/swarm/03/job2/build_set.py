#!/usr/bin/env python3
"""build_set.py OUT : assemble the job-2 special test set with one line per position:
<class>\t<source>\t<fen>
Sources: FILTER (from R/G by filter_special.py, capped at 100 per class) and CONSTRUCTED (class B only, because
R+G contained 0 class-B positions and 6,000 random games found 14 more; the constructed ones make the class big
enough to be a real test, and the report keeps the two groups apart)."""
import sys

OUT = sys.argv[1]
rows = []
for src_file, tag in (("pool_special.tsv", "FILTER"), ("ep_constructed.tsv", "CONSTRUCTED")):
    for line in open(src_file):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 3:
            rows.append((p[0], tag, p[2]))
# class B: real hits first (they are the rarer, more valuable ones), then constructed, capped at 100 total
hits = []
for line in open("ep_hits.txt"):
    p = line.rstrip("\n").split("\t")
    if len(p) >= 2:
        hits.append(("B", "EPHUNT", p[1]))

by_class = {}
for c, tag, fen in rows:
    by_class.setdefault(c, []).append((tag, fen))

final = []
for c in "ABCDE":
    if c == "B":
        final += hits
        continue
    for tag, fen in by_class.get(c, []):
        final.append((c, tag, fen))

with open(OUT, "w") as f:
    for c, tag, fen in final:
        f.write(f"{c}\t{tag}\t{fen}\n")

from collections import Counter
print("per class:", dict(Counter(c for c, _, _ in final)))
print("per class+source:", dict(Counter((c, tag) for c, tag, _ in final)))
print("total:", len(final))
