#!/usr/bin/env python3
"""Minimal fake UCI engine for cases N3 and N4: emits one progress line every 20 ms for 2.0 s."""
import sys
import time

for raw in sys.stdin:
    cmd = raw.strip()
    if cmd == "uci":
        print("id name FakeSpamEngine", flush=True)
        print("uciok", flush=True)
    elif cmd == "isready":
        print("readyok", flush=True)
    elif cmd.startswith("go"):
        t0 = time.monotonic()
        while time.monotonic() - t0 < 2.0:
            print("info depth 1 score cp 0", flush=True)
            time.sleep(0.02)
        print("bestmove e2e4", flush=True)
    elif cmd == "quit":
        break
