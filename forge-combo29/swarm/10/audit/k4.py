#!/usr/bin/env python3
"""k4.py -- K4: "G perft 3 and the first 60 at perft 4 were equal in an earlier check"

"equal" is undefined in the brief, so it is tested as equal to python-chess 1.11.2 on the same board.
perft is safe through a plain pipe (it completes before EOF), but this uses the shared driver anyway so
there is one I/O path. A position where python-chess cannot parse the FEN is reported, not skipped.

Usage: k4.py OUTDIR
"""
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drv import Drv

EXE = os.environ.get("FORGE_EXE", "/home/ubuntu/builds/release/forge")
OUT = os.path.abspath(sys.argv[1])
SETS = os.path.join(OUT, "sets")
os.makedirs(os.path.join(OUT, "K4"), exist_ok=True)


def perft_py(b, d):
    if d == 0:
        return 1
    if d == 1:
        return b.legal_moves.count()
    n = 0
    for m in list(b.legal_moves):
        b.push(m)
        n += perft_py(b, d - 1)
        b.pop()
    return n


fens = [l.strip().split(";")[0].strip() for l in open(os.path.join(SETS, "set_G.epd")) if l.strip()]
d = Drv(EXE)
d.uci()
d.isready()
res = {"depth3": [], "depth4": [], "unparsed": [], "refused": []}
for i, fen in enumerate(fens):
    try:
        b = chess.Board(fen)
    except ValueError as e:
        res["unparsed"].append({"i": i, "fen": fen, "err": str(e)})
        continue
    d.pos("position fen " + fen)
    eng3, lines = d.perft(3)
    py3 = perft_py(chess.Board(fen), 3)
    res["depth3"].append({"i": i, "fen": fen, "engine": eng3, "python": py3, "equal": eng3 == py3})
    if i < 60:
        d.pos("position fen " + fen)
        eng4, lines = d.perft(4)
        py4 = perft_py(chess.Board(fen), 4)
        res["depth4"].append({"i": i, "fen": fen, "engine": eng4, "python": py4, "equal": eng4 == py4})
    if i % 50 == 0:
        print("  %d/%d" % (i, len(fens)), flush=True)
d.quit()

bad3 = [r for r in res["depth3"] if not r["equal"]]
bad4 = [r for r in res["depth4"] if not r["equal"]]
null3 = [r for r in res["depth3"] if r["engine"] is None]
summary = {
    "positions_G": len(fens),
    "checked_depth3": len(res["depth3"]),
    "mismatch_depth3": len(bad3),
    "checked_depth4": len(res["depth4"]),
    "mismatch_depth4": len(bad4),
    "null_engine_totals_depth3": len(null3),
    "unparsed_by_python_chess": len(res["unparsed"]),
    "verdict": "PASS" if not bad3 and not bad4 and not null3 else "REFUTED",
}
with open(os.path.join(OUT, "K4", "summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")
with open(os.path.join(OUT, "K4", "mismatches.json"), "w") as f:
    json.dump({"depth3": bad3, "depth4": bad4, "unparsed": res["unparsed"]}, f, indent=2)
    f.write("\n")
print(json.dumps(summary, indent=2))
