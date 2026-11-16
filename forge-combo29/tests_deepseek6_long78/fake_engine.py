#!/usr/bin/env python3
"""fake_engine.py -- the long 78 plant: answers uciok, readyok, and bestmove a1a8 to every go."""
import sys
for line in sys.stdin:
    line = line.strip()
    if line == "uci":
        print("id name fake plant engine")
        print("uciok", flush=True)
    elif line == "isready":
        print("readyok", flush=True)
    elif line.startswith("go"):
        print("bestmove a1a8", flush=True)
    elif line == "quit":
        break
