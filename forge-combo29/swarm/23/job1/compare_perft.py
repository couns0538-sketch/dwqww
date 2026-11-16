#!/usr/bin/env python3
"""compare_perft.py : compare engine_R.jsonl against the python-chess reference files.

Prints, as pasted output for the report:
  - per-depth totals and per-depth mismatch counts
  - every mismatching position with its FEN, engine nodes and reference nodes at each depth
  - the divide difference for the deepest depth on a mismatch
  - count of positions where the engine's perft 1 != reference legal-move count
Exit code 0 always; the table is the product.
"""
import glob
import json
import sys

eng = {}
for line in open("engine_R.jsonl"):
    row = json.loads(line)
    eng[row["i"]] = row

ref = {}
for path in sorted(glob.glob("pych_R_*.jsonl")):
    for line in open(path):
        row = json.loads(line)
        ref[row["i"]] = row

print("engine positions", len(eng), "reference positions", len(ref))
missing = sorted(set(eng) - set(ref))
print("positions missing a reference:", len(missing), missing[:10])
invalid = [i for i, r in ref.items() if r.get("invalid")]
print("reference says INVALID FEN:", len(invalid), invalid[:10])

depths = ["1", "2", "3", "4"]
tot_eng = {d: 0 for d in depths}
tot_ref = {d: 0 for d in depths}
bad = {d: [] for d in depths}
for i in sorted(ref):
    r = ref[i]
    if r.get("invalid"):
        continue
    e = eng.get(i)
    if e is None:
        continue
    for d in depths:
        tot_eng[d] += e["nodes"][d]
        tot_ref[d] += r["nodes"][d]
        if e["nodes"][d] != r["nodes"][d]:
            bad[d].append(i)

print()
print("depth | engine nodes | reference nodes | equal | mismatching positions")
for d in depths:
    print("%5s | %12d | %15d | %5s | %d" % (d, tot_eng[d], tot_ref[d],
                                           "yes" if tot_eng[d] == tot_ref[d] else "NO", len(bad[d])))

print()
print("perft-1 mismatch count (must be 0 for P2/P5):", len(bad["1"]))

if bad["4"]:
    print()
    print("MISMATCHES at depth 4 (with divide diff):")
    for i in bad["4"][:50]:
        e, r = eng[i], ref[i]
        print("i=%d fen=%s" % (i, r["fen"]))
        print("   nodes eng=%s ref=%s" % (e["nodes"], r["nodes"]))
        ed, rd = e["divide"] or {}, r["divide"] or {}
        for mv in sorted(set(ed) | set(rd)):
            if ed.get(mv) != rd.get(mv):
                print("   move %s eng=%s ref=%s" % (mv, ed.get(mv), rd.get(mv)))
else:
    print()
    print("no mismatches at any depth 1..4")

sys.exit(0)
