#!/usr/bin/env python3
"""fake_engine.py : a deliberately WRONG engine, used as the planted case for Rule 1.

It speaks enough UCI that run_pv.py drives it unchanged, but its `info` line always carries the
illegal PV `a1a8`, and its bestmove is always `bestmove a1a8`. The SAME harness (run_pv.py ->
check_pv.py) must count one illegal PV per record. If it counts zero, the harness cannot see an
illegal PV and my "0 illegal" result is not shown.
"""
import sys

for line in sys.stdin:
    cmd = line.strip()
    if cmd == "uci":
        print("id name Fake Broken Engine")
        print("id author swarm-25 plant")
        print("uciok", flush=True)
    elif cmd == "isready":
        print("readyok", flush=True)
    elif cmd.startswith("go"):
        print("info depth 1 seldepth 1 score cp 0 nodes 1 nps 0 hashfull 0 time 0 pv a1a8", flush=True)
        print("bestmove a1a8", flush=True)
    elif cmd == "quit":
        break
