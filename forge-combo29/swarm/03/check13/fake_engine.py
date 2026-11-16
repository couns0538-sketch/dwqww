#!/usr/bin/env python3
"""fake_engine.py : a CONTROL engine that answers `go perft 1` correctly EXCEPT on the position whose FEN is in the
env var FAKE_FEN, where it drops one real move and adds one illegal move (a1a1).

It exists only to prove that a comparison harness REPORTS a disagreement when one is really there; a harness that
reports 0 differences against this fake is a broken harness. It is not an engine and never touches the real binary.
"""
import os
import sys
import chess

bad = os.environ.get("FAKE_FEN", "")
cur = None
for line in sys.stdin:
    cmd = line.strip()
    if cmd == "uci":
        print("id name fake-control", flush=True)
        print("uciok", flush=True)
    elif cmd == "isready":
        print("readyok", flush=True)
    elif cmd == "ucinewgame":
        pass
    elif cmd.startswith("position fen "):
        cur = cmd[len("position fen "):].strip()
    elif cmd.startswith("go perft 1"):
        b = chess.Board(cur) if cur else chess.Board()
        moves = sorted(m.uci() for m in b.legal_moves)
        if cur == bad and moves:
            moves = moves[1:] + ["a1a1"]
        for m in moves:
            print(f"{m}: 1", flush=True)
        print(f"nodes {len(moves)}", flush=True)
    elif cmd == "quit":
        break
