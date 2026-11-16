#!/usr/bin/env python3
"""fake_bestmove.py : a STANDALONE planted control for job 5 — not an engine, and not a proxy.

It answers the UCI conversation correctly but always plays the ILLEGAL move a1a1 at a fixed depth, with a plausible
info line. Its only purpose is to prove that bestmove_parity.py REPORTS a difference and flags the move illegal when
one is really there (file 2, Rule 1: a zero needs a planted one).

Two earlier attempts at a *proxy* wrapper deadlocked by waiting for a reply the real engine never sends after
`position` (it answers `readyok` to the following `isready`, not to `position`). A standalone fake has no such
coupling, so the control itself cannot hang.

MODE env var: `illegal` (default) plays a1a1; `legal` plays python-chess's first legal move — the second gives a
control where the harness must NOT flag illegality but must still see whatever differs.
"""
import os
import sys

import chess

MODE = os.environ.get("FAKE_MODE", "illegal")
cur = None
depth = 8

for line in sys.stdin:
    cmd = line.strip()
    if cmd == "uci":
        print("id name fake-control-planted", flush=True)
        print("option name Hash type spin default 16 min 1 max 2048", flush=True)
        print("option name Threads type spin default 1 min 1 max 256", flush=True)
        print("option name OwnBook type check default false", flush=True)
        print("uciok", flush=True)
    elif cmd == "isready":
        print("readyok", flush=True)
    elif cmd == "ucinewgame":
        pass
    elif cmd.startswith("setoption"):
        pass
    elif cmd.startswith("position fen "):
        cur = cmd[len("position fen "):].strip()
    elif cmd.startswith("go depth "):
        try:
            depth = int(cmd.split()[2])
        except (IndexError, ValueError):
            depth = 8
        if MODE == "legal":
            mv = next(iter(chess.Board(cur).legal_moves)).uci()
        else:
            mv = "a1a1"
        print(f"info depth {depth} seldepth {depth} score cp 12 nodes 4242 nps 1000000 "
              f"hashfull 0 time 4 pv {mv}", flush=True)
        print(f"bestmove {mv}", flush=True)
    elif cmd == "quit":
        break
