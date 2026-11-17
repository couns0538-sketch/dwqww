#!/usr/bin/env python3
import sys
for line in sys.stdin:
    w = line.split()
    if not w:
        continue
    if w[0] == "uci":
        print("id name fake-noready", flush=True)
        print("uciok", flush=True)
    elif w[0] == "go":
        print("bestmove a2a3", flush=True)
