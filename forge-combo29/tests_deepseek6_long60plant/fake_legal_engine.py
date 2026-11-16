#!/usr/bin/env python3
"""deepseek6 long 60 CONTROL: a fake engine that always answers a LEGAL move.

The pair to fake_illegal_engine.py. Long 60's driver must flag the illegal fake (4 of 4 games,
ILLEGAL) and must NOT flag this one. Without the control, "4 illegal games caught" could just be
a driver that fails on everything that is not the real engine.
"""
import sys

import chess

mv = None
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name fake-legal-engine")
        print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("position"):
        fen = c.split("fen", 1)[1].strip() if "fen" in c else chess.STARTING_FEN
        b = chess.Board(fen)
        legal = sorted(m.uci() for m in b.legal_moves)
        mv = legal[0] if legal else "0000"
    elif c.startswith("go"):
        print("bestmove %s" % mv, flush=True)
    elif c == "quit":
        break
