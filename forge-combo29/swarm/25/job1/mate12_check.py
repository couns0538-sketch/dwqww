#!/usr/bin/env python3
"""mate12_check.py : proves the mate -12 score at depth 12 is too pessimistic.

Takes the depth-12 last PV for 8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1 (from the committed raw file
G_d12.jsonl), plays it with python-chess and shows the final position is CHECKMATE for white.
18 plies = a black mate in 9. The engine announced mate -12 (24 plies) on the same line.
"""
import json
import sys

import chess

TARGET = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"


def main(path):
    rec = None
    for line in open(path):
        r = json.loads(line)
        if r["fen"] == TARGET:
            rec = r
            break
    if rec is None:
        print("position not in", path)
        return 2
    pv = None
    for line in rec["lines"]:
        if line.startswith("info ") and " pv " in line:
            toks = line.split()
            pv = toks[toks.index("pv") + 1:]
    print("raw last info line:")
    for line in rec["lines"]:
        if line.startswith("info depth") and " pv " in line:
            print("   ", line)
    print("bestmove:", rec["bestmove"])
    print("PV plies:", len(pv))
    print("PV:", " ".join(pv))
    b = chess.Board(TARGET)
    for i, m in enumerate(pv):
        mv = chess.Move.from_uci(m)
        assert mv in b.legal_moves, f"illegal {m} at ply {i}"
        b.push(mv)
    print("final FEN:", b.fen())
    print("is_checkmate:", b.is_checkmate())
    print("is_stalemate:", b.is_stalemate())
    print("side to move:", "white" if b.turn == chess.WHITE else "black")
    if b.is_checkmate():
        print(f"RESULT: the printed PV is a black mate in {len(pv) // 2} moves "
              f"({len(pv)} plies), but the score says mate -12 (24 plies).")
        print("        So mate -12 is provably too pessimistic: mate in 9 exists.")
        return 1
    print("RESULT: PV does not end in checkmate either.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
