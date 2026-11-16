#!/usr/bin/env python3
"""cross_s13.py THEIRS MYJSON OUT : compare another seat's raw per-position values with mine, value by value.

THEIRS: their "idx depth nodes marker" text file (whitespace separated, optional leading '#' header).
MYJSON: my engine_perft.py JSON ({results: {idx: {depth: nodes}}}).
Prints how many (position, depth) values agree, and lists any disagreement. Asserts that BOTH sides actually
contained numbers — a file with no parsed values must not be able to print "agrees".
"""
import json
import sys

theirs_path, mine_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
theirs = {}
nbad_header = 0
for line in open(theirs_path):
    s = line.strip()
    if not s or s.startswith("#"):
        continue
    p = s.split()
    if len(p) < 3:
        nbad_header += 1
        continue
    idx, dep, nodes = int(p[0]), int(p[1]), int(p[2])
    theirs[(idx, dep)] = nodes

mine = json.load(open(mine_path))["results"]
common, agree, disagree, only_theirs, only_mine = 0, 0, [], [], []
for (idx, dep), v in theirs.items():
    m = mine.get(str(idx), {}).get(str(dep))
    if m is None:
        only_theirs.append((idx, dep, v))
        continue
    common += 1
    if m == v:
        agree += 1
    else:
        disagree.append((idx, dep, v, m))
for idx_s, row in mine.items():
    for dep_s, v in row.items():
        if (int(idx_s), int(dep_s)) not in theirs:
            only_mine.append((int(idx_s), int(dep_s), v))

lines = [
    f"their records parsed: {len(theirs)}  (malformed lines skipped: {nbad_header})",
    f"my records: {sum(len(r) for r in mine.values())}",
    f"(position, depth) keys present in BOTH: {common}",
    f"values EQUAL: {agree}",
    f"values DIFFERENT: {len(disagree)}",
    f"keys only in theirs: {len(only_theirs)}",
    f"keys only in mine: {len(only_mine)}",
]
with open(out, "w") as f:
    f.write("\n".join(lines) + "\n")
    for row in disagree[:50]:
        f.write(f"DIFF idx={row[0]} depth={row[1]} theirs={row[2]} mine={row[3]}\n")
print("\n".join(lines))
if len(theirs) == 0:
    sys.exit("FAIL: their file yielded no numbers — cannot confirm anything from it")
if common == 0:
    sys.exit("FAIL: no overlapping keys — cannot confirm anything")
if agree == 0:
    sys.exit("FAIL: not a single value agreed — the comparison did not measure agreement")
