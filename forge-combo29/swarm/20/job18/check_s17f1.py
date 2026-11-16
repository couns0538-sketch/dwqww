#!/usr/bin/env python3
"""check_s17f1.py — seat 20 job 18: my OWN check of seat 17's S-F1, plus the info-line count detail.

Uses AUDIT/hardened.py (fresh process per search, reads to bestmove before quit) and ASSERTS that the parsed fields
exist before recording anything.

usage: check_s17f1.py <exe> <outdir>
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

EXE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

POS = {
    "startpos": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "midgame": "r2q1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 1",
}
GOS = ["go depth 2 searchmoves", "go depth 4 searchmoves", "go depth 2 searchmoves e7e5",
       "go depth 2 searchmoves a2a3", "go depth 2", "go searchmoves"]

rows = []
print(f"exe {EXE}")
print(f"{'pos':9s} {'command':30s} {'bestmove':9s} {'nodes':6s} {'depthlines':>10s} {'score':8s}")
for name, fen in POS.items():
    for go in GOS:
        e = Engine(EXE)
        try:
            e.position(fen)
            r = e.search(go, timeout=120)
        finally:
            e.close()
        assert r["bestmove"] is not None, f"NO bestmove — nothing measured for {go}"
        assert r["score"] is not None, f"NO score parsed for {go} — refusing to record"
        rows.append({"pos": name, "go": go, "bestmove": r["bestmove"], "nodes": r["nodes"],
                     "depth_lines": r["info_depth_lines"], "score": r["score"],
                     "info_strings": [x for x in [r["last_info"]] if x]})
        print(f"{name:9s} {go:30s} {r['bestmove']:9s} {r['nodes']:6d} {r['info_depth_lines']:10d} "
              f"{str(r['score']):8s}")

with open(os.path.join(OUT, "check_s17f1.json"), "w") as f:
    json.dump({"exe": EXE, "rows": rows}, f, indent=1)
print("\nwrote check_s17f1.json")
