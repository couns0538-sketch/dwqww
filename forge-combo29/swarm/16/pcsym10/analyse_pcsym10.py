#!/usr/bin/env python3
"""analyse_pcsym10.py : PC20 depth-10 result vs the base-tree S14 depth-10 result, position for position.

No number is typed: both tables are read and compared here.
"""
import statistics

PC = "raw_G353.tsv"
BASE = "../job3/raw/G_d10.tsv"


def load_pc(path):
    rows = {}
    with open(path) as fh:
        fh.readline()
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 13 and p[2] != "MISSING":
                rows[int(p[0])] = p
    return rows


def load_base(path):
    rows = {}
    with open(path) as fh:
        fh.readline()
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 13 and p[2] != "HANG":
                rows[int(p[0])] = p
    return rows


pc = load_pc(PC)
base = load_base(BASE)
n = len(pc)
print(f"PC20 rows {n}   base rows {len(base)}")

pc_score = sum(1 for r in pc.values() if r[10] == "True")
pc_bm = sum(1 for r in pc.values() if r[11] == "True")
pc_nodes = sum(1 for r in pc.values() if r[12] == "True")
base_score = sum(1 for r in base.values() if r[10] == "True")
base_bm = sum(1 for r in base.values() if r[11] == "True")

print()
print("| quantity | base tree + S14 | PC r15 + PC20 |")
print("|---|---|---|")
print(f"| mirror pairs total | {len(base)} | {n} |")
print(f"| score equal | {base_score} | {pc_score} |")
print(f"| bestmove equal (mirrored) | {base_bm} | {pc_bm} |")
print(f"| bestmove MISMATCH | {len(base)-base_bm} | {n-pc_bm} |")
print(f"| node counts equal | (not recorded) | {pc_nodes} |")
print()

# position-for-position agreement about whether the pair matches
common = [i for i in pc if i in base]
agree_bm = sum(1 for i in common if (pc[i][11] == "True") == (base[i][11] == "True"))
agree_score = sum(1 for i in common if (pc[i][10] == "True") == (base[i][10] == "True"))
print(f"common positions {len(common)}")
print(f"same verdict on bestmove-match: {agree_bm}/{len(common)}  "
      f"(disagree {len(common)-agree_bm})")
print(f"same verdict on score-match   : {agree_score}/{len(common)}  "
      f"(disagree {len(common)-agree_score})")
print()

# the 20 probe positions
probe = [i for i in range(min(20, n)) if i in pc]
print("first 20 positions, PC20:")
for i in probe[:10]:
    r = pc[i]
    print(f"  idx {i:3d} bm {r[2]} vs {r[7]} score {r[3]} vs {r[8]} nodes {r[4]} vs {r[9]} "
          f"score_equal {r[10]} bm_equal {r[11]}")
