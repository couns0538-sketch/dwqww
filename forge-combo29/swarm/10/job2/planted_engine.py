#!/usr/bin/env python3
"""planted_engine.py -- a FAKE engine for testing the deepseek6 long56 runner's classifier.
It answers uci/uciok, isready/readyok, and for every `go` it prints a bestmove that is
ILLEGAL for startpos (a1a8).  If the runner's illegal-bestmove check works, this must be
counted as illegal.  Any other command: silence."""
import sys

for line in sys.stdin:
    line = line.strip()
    if line == "uci":
        print("id name PLANTED FAKE", flush=True)
        print("uciok", flush=True)
    elif line == "isready":
        print("readyok", flush=True)
    elif line.startswith("go"):
        print("bestmove a1a8", flush=True)
    elif line == "quit":
        break
