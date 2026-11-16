#!/usr/bin/env python3
import sys, random
for line in sys.stdin:
    c=line.strip()
    if c=="uci":
        print("id name PLANTED-RANDOM",flush=True)
        print("option name Threads type spin default 1 min 1 max 256",flush=True)
        print("option name OwnBook type check default false",flush=True)
        print("uciok",flush=True)
    elif c=="isready": print("readyok",flush=True)
    elif c.startswith("go"):
        n=random.randint(1800,2200)
        print(f"info depth 5 seldepth 8 score cp 30 nodes {n} nps 1 hashfull 0 time 1 pv e2e4",flush=True)
        print("bestmove e2e4",flush=True)
