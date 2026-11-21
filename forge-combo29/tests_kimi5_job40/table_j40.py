#!/usr/bin/env python3
"""kimi5 job 40 step 3 table: reads runlist.tsv, aggregates every run's rows against
the base rows (exploded = depth < 12 or nodes >= cap; ratio over non-exploded;
changed = depth or nodes differ, over ALL positions; bm = best move differs).
Prints how many rows files it read. Usage: table_j40.py (run from forge-combo29).
"""
import os

J = "tests_kimi5_job40"

def read_rows(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                p = line.split()
                rows.append((int(p[0]), int(p[1]), int(p[2]), p[3]))
    return rows

def read_caps(path):
    caps = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                n, c = line.split()
                caps[int(n)] = int(c)
    return caps

print("option\tvalue\tset\texploded\texp_indices\tnonexp_sum\tbase_sum\tratio\tchanged\tbm_changed")
files_read = 0
with open(os.path.join(J, "runlist.tsv")) as f:
    entries = [line.strip().split("\t") for line in f if line.strip()]
for name, value, set_ in entries:
    vtag = value.replace("-", "m")
    tag = f"s3_{name}_{vtag}_{set_}"
    base = read_rows(f"kimi5/job37/k3/base{set_}.rows")
    run = read_rows(os.path.join(J, "s3", f"{tag}.rows"))
    caps = read_caps(os.path.join(J, "s3", f"{tag}.caps"))
    files_read += 2
    exploded = [n for n, d, nodes, bm in run if d < 12 or nodes >= caps[n]]
    exset = set(exploded)
    run_sum = sum(nodes for n, d, nodes, bm in run if n not in exset)
    base_sum = sum(nodes for n, d, nodes, bm in base if n not in exset)
    ratio = f"{run_sum / base_sum:.6f}" if base_sum else "nan"
    changed = sum(1 for (n, d, nodes, bm), (_, d2, nodes2, _) in zip(run, base)
                  if d != d2 or nodes != nodes2)
    bm_changed = sum(1 for (_, _, _, bm), (_, _, _, bm2) in zip(run, base) if bm != bm2)
    print(f"{name}\t{value}\t{set_}\t{len(exploded)}\t{','.join(map(str, exploded)) or '-'}\t"
          f"{run_sum}\t{base_sum}\t{ratio}\t{changed}\t{bm_changed}")
print(f"rows_files_read: {files_read}")
