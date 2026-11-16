#!/usr/bin/env python3
"""fake_mate_engine.py : planted case for the MATE check (Rule 1).

Answers every `go` with a legal-looking PV (the first legal move, played by python-chess) but
claims `score mate 5`, which needs 9 plies. So: all moves legal, mate distance wrong. The same
harness (run_pv.py -> check_pv.py) must count "mate PVs wrong" >= 1 and "PVs with illegal" = 0.
That shows my mate check can see a wrong mate line, not just an illegal move.
"""
import sys

import chess

fen = None
for line in sys.stdin:
    cmd = line.strip()
    if cmd == "uci":
        print("id name Fake Mate Engine")
        print("id author swarm-25 plant")
        print("uciok", flush=True)
    elif cmd == "isready":
        print("readyok", flush=True)
    elif cmd.startswith("position fen "):
        fen = cmd[len("position fen "):].strip()
    elif cmd.startswith("go"):
        pv = []
        try:
            b = chess.Board(fen)
            for _ in range(3):
                mv = next(iter(b.legal_moves), None)
                if mv is None:
                    break
                pv.append(mv.uci())
                b.push(mv)
        except Exception:
            pv = []
        print("info depth 5 seldepth 5 score mate 5 nodes 1 nps 0 hashfull 0 time 0 pv " + " ".join(pv),
              flush=True)
        print("bestmove " + (pv[0] if pv else "0000"), flush=True)
    elif cmd == "quit":
        break
