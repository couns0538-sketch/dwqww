#!/usr/bin/env python3
import sys
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name PLANTED-ILLEGAL", flush=True)
        print("option name OwnBook type check default false", flush=True)
        print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("go"):
        print("info depth 1 seldepth 1 score cp 0 nodes 1 nps 1 hashfull 0 time 0 pv z9z9", flush=True)
        print("bestmove z9z9", flush=True)         # planted illegal move
