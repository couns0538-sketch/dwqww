#!/usr/bin/env python3
"""kimi5 job12 Step 1: per-position identity against a reference rows file.
Node counts always; best moves when both sides carry them (job-8 rows do not).
Usage: cmp_j12.py <new.json> <ref.json>
Prints "N of N equal" per quantity; exit 1 on any difference.
"""
import json
import sys

new = json.load(open(sys.argv[1]))
ref = json.load(open(sys.argv[2]))

nn, rr = new["per_position"], ref["per_position"]
assert len(nn) == len(rr), (len(nn), len(rr))

nd = [i for i in range(len(nn)) if nn[i] != rr[i]]
ok = True
if nd:
    print(f"{new['tag']} vs {ref['tag']}: nodes {len(nn)-len(nd)} of {len(nn)} equal, DIFFER at {nd[:10]}")
    ok = False
else:
    print(f"{new['tag']} vs {ref['tag']}: nodes {len(nn)} of {len(nn)} equal", end="")

if "bestmove" in new and "bestmove" in ref:
    nb, rb = new["bestmove"], ref["bestmove"]
    bd = [i for i in range(len(nb)) if nb[i] != rb[i]]
    if bd:
        print(f"; bestmoves DIFFER at {bd[:10]}")
        ok = False
    else:
        print(f"; bestmoves {len(nb)} of {len(rb)} equal")
else:
    print("; bestmoves not compared (absent on one side)")
sys.exit(0 if ok else 1)
