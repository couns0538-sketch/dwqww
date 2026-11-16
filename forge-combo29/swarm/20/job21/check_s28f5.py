#!/usr/bin/env python3
"""check_s28f5.py — seat 20 job 21: my OWN check of seat 28's S-F5 (increment ignored below Move Overhead).

Fresh process per search, OwnBook false (else the book answers instantly and fakes a tiny search).
For each (wtime, winc) pair: wall time go->bestmove, nodes, depth.

usage: check_s28f5.py <exe> <outdir>
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"

rows = []
print(f"exe {EXE}")
print(f"{'wtime':>6s} {'winc':>6s} {'wall ms':>9s} {'nodes':>8s} {'depth':>6s} {'legal':>6s} {'bestmove':9s}")
for wtime in (5, 10, 11, 30, 100):
    for winc in (0, 1000):
        e = Engine(EXE)
        try:
            e.position(FEN)
            r = e.search(f"go wtime {wtime} btime {wtime} winc {winc} binc {winc}", timeout=120)
        finally:
            e.close()
        assert r["bestmove"] is not None and r["score"] is not None, \
            f"unparsed result for wtime {wtime} winc {winc} — refusing to record"
        legal = r["bestmove"] in {m.uci() for m in chess.Board(FEN).legal_moves}
        depth = None
        if r["last_info"]:
            depth = int(r["last_info"].split("depth ")[1].split()[0])
        rows.append({"wtime": wtime, "winc": winc, "wall_ms": round(r["wall"] * 1000, 2),
                     "nodes": r["nodes"], "depth": depth, "legal": legal, "bestmove": r["bestmove"]})
        print(f"{wtime:6d} {winc:6d} {r['wall']*1000:9.2f} {r['nodes']:8d} {str(depth):>6s} "
              f"{str(legal):>6s} {r['bestmove']:9s}")

print()
print("== pairwise: does the increment change anything at each wtime?")
for wtime in (5, 10, 11, 30, 100):
    a = [r for r in rows if r["wtime"] == wtime and r["winc"] == 0][0]
    b = [r for r in rows if r["wtime"] == wtime and r["winc"] == 1000][0]
    same = (a["nodes"] == b["nodes"] and a["depth"] == b["depth"])
    print(f"  wtime {wtime:4d}: winc0 {a['nodes']:7d} n / d{a['depth']}   "
          f"winc1000 {b['nodes']:7d} n / d{b['depth']}   -> "
          f"{'IDENTICAL (increment ignored)' if same else 'differs (increment used)'}")

with open(os.path.join(OUT, "check_s28f5.json"), "w") as f:
    json.dump({"exe": EXE, "fen": FEN, "rows": rows}, f, indent=1)
print("\nwrote check_s28f5.json")
