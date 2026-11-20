#!/usr/bin/env python3
# kimi5 job 37 step 4 grader: reads runlist.tsv + s4/*.rows, prints and writes grading.tsv.
# Base rows: k3/patO.rows, k3/patG.rows (patched r15d build at defaults, K3-proven == r15d).
# ALIVE = any position's (depth,nodes) differs on any of the up-to-four runs; else DEAD; NOT SEEN = a run missing.
import os, sys

J = os.path.dirname(os.path.abspath(__file__))

def read_rows(path):
    rows = {}
    with open(path) as f:
        for line in f:
            p = line.split()
            rows[int(p[0])] = (int(p[1]), int(p[2]), p[3])
    return rows

base = {"O": read_rows(f"{J}/k3/patO.rows"), "G": read_rows(f"{J}/k3/patG.rows")}
base_sum = {s: sum(v[1] for v in r.values()) for s, r in base.items()}

out = ["option\tside\tsuite\tsum\tratio\tpos_nodes_diff\tpos_bm_diff\tn"]
per_opt = {}
for line in open(f"{J}/runlist.tsv"):
    if line.startswith("option"):
        continue
    name, side, value = line.rstrip("\n").split("\t")
    for suite in ("O", "G"):
        path = f"{J}/s4/s4_{name}_{side}_{suite}.rows"
        if not os.path.exists(path):
            per_opt.setdefault(name, set()).add("NOTSEEN")
            out.append(f"{name}\t{side}\t{suite}\tNA\tNA\tNA\tNA\t0")
            continue
        rows = read_rows(path)
        b = base[suite]
        nd = sum(1 for i in b if i in rows and rows[i][:2] != b[i][:2])
        bm = sum(1 for i in b if i in rows and rows[i][2] != b[i][2])
        s = sum(v[1] for v in rows.values())
        out.append(f"{name}\t{side}\t{suite}\t{s}\t{s / base_sum[suite]:.6f}\t{nd}\t{bm}\t{len(rows)}")
        if nd > 0:
            per_opt.setdefault(name, set()).add("ALIVE")
        else:
            per_opt.setdefault(name, set()).add("quiet")

cls = []
for name, states in per_opt.items():
    c = "NOT SEEN" if "NOTSEEN" in states else ("ALIVE" if "ALIVE" in states else "DEAD")
    cls.append((name, c))

with open(f"{J}/grading.tsv", "w") as f:
    f.write("\n".join(out) + "\n")
with open(f"{J}/classification.txt", "w") as f:
    for name, c in cls:
        f.write(f"{name}\t{c}\n")
    f.write(f"ALIVE {sum(1 for _, c in cls if c == 'ALIVE')}; DEAD {sum(1 for _, c in cls if c == 'DEAD')}; "
            f"NOT SEEN {sum(1 for _, c in cls if c == 'NOT SEEN')}\n")
print("\n".join(out))
print(*cls, sep="\n")
