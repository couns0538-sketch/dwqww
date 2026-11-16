#!/usr/bin/env python3
"""check_s27f3.py — seat 20 job 17: my OWN check of seat 27's S-F3 (hashfull samples only 1000 clusters).

Same position, same search, only `Hash` changes. Uses the hardened driver (fresh process per search, reads to
bestmove before quit).

usage: check_s27f3.py <exe> <outdir>
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

EXE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

POSITIONS = {
    "midgame": "r2q1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 0 1",
    "startpos": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
}
HASHES = [16, 64, 256, 1024]


def hashfull_of(line):
    m = re.search(r"hashfull (\d+)", line)
    return int(m.group(1)) if m else None


rows = []
print(f"exe {EXE}")
print()
for name, fen in POSITIONS.items():
    for go in ("go depth 12", "go depth 18"):
        print(f"== {name}  {go}")
        print(f"{'Hash':>6s} {'bestmove':9s} {'score':10s} {'nodes':9s} {'hashfull':>9s}")
        for h in HASHES:
            e = Engine(EXE, opts=[("Hash", h)])
            try:
                e.position(fen)
                r = e.search(go, timeout=240)
            finally:
                e.close()
            hf = hashfull_of(r["last_info"])
            assert hf is not None, f"NO hashfull FIELD in the answer — refusing to record ({r['last_info']!r})"
            assert r["nodes"] > 0, f"NO NODES in the answer — refusing to record ({r['last_info']!r})"
            rows.append({"pos": name, "go": go, "hash": h, "bestmove": r["bestmove"],
                         "score": r["score"], "nodes": r["nodes"], "hashfull": hf})
            print(f"{h:6d} {str(r['bestmove']):9s} {str(r['score']):10s} {r['nodes']:9d} {hf:9d}")
        print()

with open(os.path.join(OUT, "check_s27f3.json"), "w") as f:
    json.dump({"exe": EXE, "rows": rows}, f, indent=1)
print("wrote check_s27f3.json")
