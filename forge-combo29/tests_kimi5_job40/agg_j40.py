#!/usr/bin/env python3
"""kimi5 job 40 aggregation: one run's rows against the base rows.
Prints: files read, exploded count + indices (depth < 12 or nodes >= cap),
node sum and ratio to base over NON-exploded positions, positions changed
(depth or nodes differ from base) over ALL, best moves changed over ALL.
Usage: agg_j40.py <base.rows> <run.rows> [run.caps]
"""
import sys

def read_rows(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                p = line.split()
                rows.append((int(p[0]), int(p[1]), int(p[2]), p[3]))
    return rows

base = read_rows(sys.argv[1])
run = read_rows(sys.argv[2])
caps = {}
if len(sys.argv) > 3:
    with open(sys.argv[3]) as f:
        for line in f:
            line = line.strip()
            if line:
                n, c = line.split()
                caps[int(n)] = int(c)

print(f"files_read: 2 base={sys.argv[1]} run={sys.argv[2]}" + (f" caps={sys.argv[3]}" if caps else ""))
assert len(base) == len(run), f"row count differs {len(base)} vs {len(run)}"

exploded = []
for n, d, nodes, bm in run:
    if d < 12 or (caps and nodes >= caps.get(n, 1 << 62)):
        exploded.append(n)
exset = set(exploded)

run_sum = sum(nodes for n, d, nodes, bm in run if n not in exset)
base_sum = sum(nodes for n, d, nodes, bm in base if n not in exset)
ratio = (run_sum / base_sum) if base_sum else float("nan")
changed = [n for (n, d, nodes, bm), (n2, d2, nodes2, bm2) in zip(run, base)
           if d != d2 or nodes != nodes2]
bm_changed = [n for (n, d, nodes, bm), (n2, d2, nodes2, bm2) in zip(run, base)
              if bm != bm2]

print(f"rows: {len(run)}")
print(f"exploded: {len(exploded)}" + (f" indices: {' '.join(map(str, exploded))}" if exploded else ""))
print(f"nonexploded_nodesum: {run_sum} base: {base_sum} ratio: {ratio:.6f}")
print(f"positions_changed: {len(changed)}" + (f" indices: {' '.join(map(str, changed))}" if changed else ""))
print(f"bestmoves_changed: {len(bm_changed)}" + (f" indices: {' '.join(map(str, bm_changed))}" if bm_changed else ""))
