#!/usr/bin/env python3
import sys
for line in sys.stdin:
    w = line.split()
    if not w:
        continue
    if w[0] == "uci":
        print("id name fake-a1a8", flush=True)
        print("uciok", flush=True)
    elif w[0] == "isready":
        print("readyok", flush=True)
    elif w[0] == "go":
        print("bestmove a1a8", flush=True)
