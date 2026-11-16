#!/usr/bin/env python3
"""deepseek6 long 32: R3/R4 comparison of my rows against kimi5's job-5 json.

kimi5's json carries `records`: a list of {pos, nodes, bestmove, ...} in the order of its
first200.fens. My rows are `index|nodes|bestmove` with 1-based index in the same order.
This script compares position by position and prints one line per configuration.

usage: cmp_kimi.py <mine.rows> <theirs.json> [tag]
exit 0 all equal, 1 a difference, 2 cannot compare
"""
import json
import sys


def load_mine(p):
    out = []
    for line in open(p):
        line = line.strip()
        if line:
            f = line.split("|")
            out.append((int(f[1]), f[2]))
    return out


def load_theirs(p):
    d = json.load(open(p))
    rec = d.get("records") or []
    return [(int(r["nodes"]), r["bestmove"]) for r in rec], d


mine_p, theirs_p = sys.argv[1], sys.argv[2]
tag = sys.argv[3] if len(sys.argv) > 3 else mine_p.split("/")[-1].replace(".rows", "")

A = load_mine(mine_p)
B, meta = load_theirs(theirs_p)

if len(A) != len(B):
    print("%-14s CANNOT COMPARE: %d rows against %d records" % (tag, len(A), len(B)))
    sys.exit(2)

sum_a = sum(x[0] for x in A)
sum_b = sum(x[0] for x in B)
node_diff = [i + 1 for i, (a, b) in enumerate(zip(A, B)) if a[0] != b[0]]
bm_diff = [i + 1 for i, (a, b) in enumerate(zip(A, B)) if a[1] != b[1]]

verdict = "EQUAL" if not node_diff and not bm_diff else "DIFFERS"
print("%-14s %-8s rows=%d  mine_sum=%d  kimi5_sum=%d  ratio=%.4f  nodes_equal=%d/%d  bm_equal=%d/%d%s" % (
    tag, verdict, len(A), sum_a, sum_b, (sum_a / sum_b if sum_b else 0),
    len(A) - len(node_diff), len(A), len(A) - len(bm_diff), len(A),
    ("  first_node_diff=%d" % node_diff[0]) if node_diff else ""))
sys.exit(0 if verdict == "EQUAL" else 1)
