#!/usr/bin/env python3
"""deepseek6 long 60 plant: a FAKE engine that answers every request with an ILLEGAL move.

Long 60's driver validates every engine move against python-chess before pushing it
(selfplay60.py:99). This engine returns a move that is not legal in the position it is given,
so the driver MUST stop that game and record an ILLEGAL reason. If the driver instead plays the
move, its "every move legal" claim in the long-60 report proves nothing.

The fake speaks just enough UCI to be driven: uci / uciok, isready / readyok, setoption (ignored),
ucinewgame, position (parsed for the side to move), go (answers a bestmove that is illegal).

usage: fake_illegal_engine.py     (as a drop-in for the --engine path)
"""
import sys

# A move that is illegal in almost every position, and is never legal from the start position.
# The driver feeds real positions from O; returning a null-ish non-move would be rejected as a
# format error, so we return a real-looking but illegal coordinate pair.
ILLEGAL = "e1e8"

for line in sys.stdin:
    cmd = line.strip()
    if cmd == "uci":
        print("id name fake-illegal-engine")
        print("uciok", flush=True)
    elif cmd == "isready":
        print("readyok", flush=True)
    elif cmd.startswith("setoption"):
        continue
    elif cmd == "ucinewgame":
        continue
    elif cmd.startswith("position"):
        continue
    elif cmd.startswith("go"):
        # answer immediately with the illegal move
        print("bestmove %s" % ILLEGAL, flush=True)
    elif cmd == "quit":
        break
