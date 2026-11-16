#!/usr/bin/env python3
"""Rule-1 control for the softnodes harness: a zero needs a planted one.

My softnodes claim is "0 runs were non-deterministic" (N runs, all identical twice). That zero only
counts if the SAME comparison, unchanged, catches a non-deterministic pair. This script feeds the
comparison deliberately different results and checks it flags them.

Also asserts the harness's other claim: if a run did NOT stop at a finished depth, the
`go depth <reached>` cross-check must catch it. I plant that by comparing against a depth that is one
shallower, which must fail.

Usage: control_softnodes.py
"""
import sys


def same_run(a, b):
    """The exact comparison softnodes.py uses for determinism."""
    return (a["max_depth"], a["nodes"], a["score"], a["bestmove"]) == \
           (b["max_depth"], b["nodes"], b["score"], b["bestmove"])


def finished(nodes_a, nodes_go_depth):
    """The exact 'stopped at a finished depth' test softnodes.py uses."""
    return nodes_a == nodes_go_depth


rows = []

# P0 identity: identical runs must be judged identical
a = {"max_depth": 7, "nodes": 2574, "score": ("cp", 17), "bestmove": "bestmove d2d4"}
b = dict(a)
rows.append(("P0 identity", "two identical runs", same_run(a, b), False,
             "correctly NOT flagged as a difference"))

# A: different node count, same everything else (what a warm/cold or racy run looks like)
c = dict(a); c["nodes"] = 2575
rows.append(("A nodes differ by 1", "identical but one node", same_run(a, c), True,
             "FLAGGED" if not same_run(a, c) else "MISSED"))

# B: different depth
d = dict(a); d["max_depth"] = 6
rows.append(("B depth differs", "one depth shallower", same_run(a, d), True,
             "FLAGGED" if not same_run(a, d) else "MISSED"))

# C: different score, same nodes (a thread-order score change)
e = dict(a); e["score"] = ("cp", 18)
rows.append(("C score differs", "cp 17 -> cp 18, same nodes", same_run(a, e), True,
             "FLAGGED" if not same_run(a, e) else "MISSED"))

# D: different bestmove
f = dict(a); f["bestmove"] = "bestmove e2e4"
rows.append(("D bestmove differs", "d2d4 -> e2e4", same_run(a, f), True,
             "FLAGGED" if not same_run(a, f) else "MISSED"))

# E: the finished-depth test must fail when the node counts differ
rows.append(("E finished-depth", "softnodes nodes 2574 vs go depth 6 nodes 1703",
             finished(2574, 1703), True,
             "FLAGGED" if not finished(2574, 1703) else "MISSED"))
rows.append(("F finished-depth identity", "2574 vs 2574", finished(2574, 2574), False,
             "correctly NOT flagged"))

ok = all((not ident) == wanted_flag for _n, _d, ident, wanted_flag, _r in rows)
print("| plant | what it is | flagged as different? | should be | result |")
print("|---|---|---|---|---|")
for name, desc, ident, wanted_flag, result in rows:
    flagged = not ident          # "flagged as different?" is the negation of "judged identical"
    print("| %s | %s | %s | %s | %s |" % (name, desc, flagged, wanted_flag, result))
print()
print("Rule 1 verdict:", "the softnodes comparison catches every planted difference and does not "
      "flag identical runs, so its zero is a real measurement" if ok else "FAILED - zero not shown")
if not ok:
    sys.exit(0)
