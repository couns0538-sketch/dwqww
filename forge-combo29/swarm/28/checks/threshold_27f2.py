#!/usr/bin/env python3
"""threshold_27f2.py EXE — where exactly is the "one root iteration" node threshold?

27-F2 says N < 26 at startpos answers the first legal move with no info line. This sweeps N and finds
the exact switch for two positions, and reports what the engine does at the switch. Uses the same
timing.Engine harness (raw fd reads) so `quit` can never race `go`.

Two positions: startpos (20 legal moves) and NONBOOK (many legal moves).
"""
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
NONBOOK = "r1bqk2r/p1ppbppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"


def probe(exe, fen, nodes):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("OwnBook", "false"), ("Threads", 1), ("Hash", 16)]:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        eng.read_until("readyok", 20)
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"position fen {fen}")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"go nodes {nodes}")
    out, ok = eng.read_until("bestmove", 30)
    eng.close()
    best = ""
    n_last = 0
    for line in out:
        if line.startswith("bestmove"):
            p = line.split()
            best = p[1] if len(p) > 1 else ""
        if line.startswith("info depth") and " nodes " in line:
            f = line.split()
            n_last = int(f[f.index("nodes") + 1])
    return best, n_last


def main() -> int:
    exe = sys.argv[1]
    for label, fen in (("startpos", STARTPOS), ("NONBOOK", NONBOOK)):
        n_moves = len(list(chess.Board(fen).legal_moves))
        print(f"\n{label}: {n_moves} legal moves")
        print("| nodes | bestmove | nodes reported by the last info line |")
        print("|---|---|---|")
        for n in (1, 5, 10, 15, 19, 20, 21, 22, 23, 24, 25, 26, 27, 30, 40, 60, 100, 200):
            best, n_last = probe(exe, fen, n)
            print(f"| {n} | {best or '-'} | {n_last} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
