#!/usr/bin/env python3
import sys
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name PLANTED-STABLE", flush=True)
        print("option name Threads type spin default 1 min 1 max 256", flush=True)
        print("option name OwnBook type check default false", flush=True)
        print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("go"):
        print("info depth 12 seldepth 20 score mate -4 nodes 20000 nps 1 hashfull 0 time 1 pv c2b1", flush=True)
        print("bestmove c2b1", flush=True)
