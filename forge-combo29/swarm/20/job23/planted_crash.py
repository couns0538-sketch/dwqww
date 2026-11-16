#!/usr/bin/env python3
import sys, os, signal
for line in sys.stdin:
    c = line.strip()
    if c == "uci":
        print("id name PLANTED-CRASH", flush=True)
        print("option name OwnBook type check default false", flush=True)
        print("uciok", flush=True)
    elif c == "isready":
        print("readyok", flush=True)
    elif c.startswith("go"):
        os.kill(os.getpid(), signal.SIGSEGV)      # planted crash
