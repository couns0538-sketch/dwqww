#!/usr/bin/env python3
"""Probe the 2-occurrence cell under several conditions to explain 22,108 vs the report's 7,581.

The report's 7,581 appears THREE times in the source record, in different roles:
  * as the 2-occurrence cell in the sparse-endgame ladder (TRIGGER.md),
  * as the BARE-position control on the same board (HANDOFF §1 controls, "E2 bare ... 7,581"),
  * as the value "the same root as a bare FEN = cp 381 / 7,581 nodes" (TRIGGER.md, 23-F134).
So 7,581 may legitimately be the BARE-board number and not the 2-occurrence number.  This
script varies exactly one thing at a time: history, depth, and the bare-vs-list axis.
"""
import sys

import chess

from harness import Engine

BASE = sys.argv[1] if len(sys.argv) > 1 else "./forge_base"
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
CYCLE = ["b8c8", "a1b2", "c8b8", "b2a1"]

runs = [
    ("bare FEN, depth 10", FEN, [], "depth 10"),
    ("bare FEN, depth 12", FEN, [], "depth 12"),
    ("bare FEN, depth 8", FEN, [], "depth 8"),
    ("2 occ, depth 10", FEN, CYCLE, "depth 10"),
    ("2 occ, depth 12", FEN, CYCLE, "depth 12"),
    ("2 occ, depth 8", FEN, CYCLE, "depth 8"),
    ("2 occ, depth 6", FEN, CYCLE, "depth 6"),
    ("3 occ, depth 10", FEN, CYCLE * 2, "depth 10"),
]

eng = Engine(BASE)
print("%-22s %-10s %-8s %-12s %-9s %s" % ("case", "go", "nodes", "score", "bestmove", "pv"))
rows = 0
for label, fen, moves, go in runs:
    board = chess.Board(fen)
    replay = board.copy()
    for m in moves:
        replay.push(chess.Move.from_uci(m))
    r = eng.search(board, go, moves)
    rows += 1
    print("%-22s %-10s %-8s %-12s %-9s %s"
          % (label, go, r["nodes"], r["score"], r["bestmove"],
             " ".join(r["pv"]) if r["pv"] else "(EMPTY)"))
eng.close()
print("\nrows examined: %d" % rows)
