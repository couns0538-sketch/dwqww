#!/usr/bin/env python3
import sys
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name FAKE silent engine"); print("option name OwnBook type check default false"); print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("go perft"):
        print("nodes 0", flush=True)
    elif c.startswith("go"):
        pass
