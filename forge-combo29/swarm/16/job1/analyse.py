#!/usr/bin/env python3
"""analyse.py : reads raw/*.tsv and prints the job-1 table. No number is typed by hand."""
import collections
import sys

import chess

rows = []
for path in ("raw/G.tsv", "raw/R.tsv"):
    with open(path) as fh:
        head = fh.readline()
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) < 11:
                continue
            rows.append(p)

total = len(rows)
diff = [r for r in rows if r[10] != "-"]
print(f"positions compared: {total}")
print(f"positions with any differing field (hce/nnue/total): {len(diff)}")
print(f"positions with identical hce, nnue and total: {total - len(diff)}")
print()

field_counts = collections.Counter()
for r in diff:
    for f in r[10].split(","):
        field_counts[f] += 1
print("differing field counts:", dict(field_counts))
print()

print("| set | idx | FEN | hce | nnue | total | hce_m | nnue_m | total_m | diff fields |")
print("|---|---|---|---|---|---|---|---|---|---|")
for r in diff:
    print("| " + " | ".join([r[0], r[1], f"`{r[2]}`", r[3], r[4], r[5], r[7], r[8], r[9], r[10]]) + " |")
print()

# prediction P3: does every difference have castling rights or an ep square?
p3_violations = []
for r in diff:
    b = chess.Board(r[2])
    if not b.castling_rights and b.ep_square is None:
        p3_violations.append(r)
print(f"P3 check: differences in positions with no castling rights and no ep square: {len(p3_violations)}")
for r in p3_violations[:10]:
    print("   ", r[2])

# control
with open("raw/ctrl.tsv") as fh:
    head = fh.readline()
    ctrl = [l.rstrip("\n").split("\t") for l in fh if l.strip()]
ctrl_diff = [c for c in ctrl if c[10] != "-"]
print(f"P2 control (G[0] sent twice, self vs mirror-of-self): rows {len(ctrl)} differences {len(ctrl_diff)}")

# magnitude summary on total
if diff:
    mags = sorted(abs(int(r[5]) - int(r[9])) for r in diff)
    print(f"|total difference| min {mags[0]} median {mags[len(mags)//2]} max {mags[-1]}")
