#!/usr/bin/env python3
import sys
n = 0
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name PLANTED-HANG", flush=True)
        print("option name OwnBook type check default false", flush=True)
        print("uciok", flush=True)
    elif c == "isready":
        n += 1
        if n == 1:
            print("readyok", flush=True)
        # every later isready: answer NOTHING  -> planted hang
    elif c.startswith("go"):
        pass
