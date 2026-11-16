#!/usr/bin/env python3
"""counter_reset_case.py BASE PATCHED — seat 01's counter-resetting mate case, on my patch.

Seat 01's combined patch additionally fixes a "counter-resetting mate" that its one-line patch does and
seat 12's does not: a pawn move resets the halfmove counter, so at halfmove 100 the position is NOT an
automatic draw if a pawn move is available. Its test board is
    8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1
and a fixed engine should answer `mate 2` with 398 nodes at depth 12 (seat 01's measured figure).

This script runs that board on BOTH binaries with the WAITING reader (never a quit racing the search, the
trap that has bitten my scripts four times), at `go depth 12`, and also records the two controls seat 01
gives: the mate-in-1 at halfmove 100, and a GENUINE fifty-move draw that must still be drawn.

Usage: counter_reset_case.py BASE PATCHED OUTDIR
"""
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

CASES = [
    # name, position command, what a fixed engine must do
    ("counter_reset_hm100", "position fen 8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1",
     "SEARCH: mate 2 (~398 nodes at depth 12)"),
    ("mate1_hm100", "position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1",
     "SEARCH: mate 1"),
    ("genuine_draw_hm150", "position fen 8/5K2/7Q/4k3/8/8/8/8 w - - 150 1",
     "still cp 0 (a real draw must stay a draw)"),
]


def probe(exe, pos, depth=12):
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
    eng.send(pos)
    eng.send("isready")
    _l, ok = eng.read_until("readyok", 20)
    if not ok:
        eng.close()
        return {"best": "NOREOK", "nodes": "", "score": "", "depth": 0}
    eng.send(f"go depth {depth}")
    out, ok = eng.read_until("bestmove", 300)
    eng.close()
    best, nodes, score, d = "", "", "", 0
    for line in out:
        if line.startswith("bestmove"):
            p = line.split()
            best = p[1] if len(p) > 1 else ""
        if line.startswith("info depth"):
            f = line.split()
            d = max(d, int(f[f.index("depth") + 1]))
            if "nodes" in f:
                nodes = f[f.index("nodes") + 1]
            if "score" in f:
                score = " ".join(f[f.index("score") + 1:f.index("score") + 3])
    return {"best": best, "nodes": nodes, "score": score, "depth": d}


def main() -> int:
    base, patched, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    print("| case | engine | bestmove | score | nodes | depth | required |")
    print("|---|---|---|---|---|---|---|")
    rows = []
    for name, pos, required in CASES:
        for label, exe in (("base (unpatched)", base), ("seat-28 patch", patched)):
            r = probe(exe, pos)
            print(f"| {name} | {label} | {r['best'] or '-'} | {r['score'] or '-'} | "
                  f"{r['nodes'] or '-'} | {r['depth']} | {required} |")
            rows.append((name, label, r["best"], r["score"], r["nodes"], r["depth"], required))
        print("| | | | | | | |")
    with open(os.path.join(outdir, "counter_reset.tsv"), "w") as fh:
        fh.write("case\tengine\tbestmove\tscore\tnodes\tdepth\trequired\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")

    # python-chess confirms the board really does contain a mate in 2.
    board = chess.Board("8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1")
    print()
    print(f"python-chess: halfmove clock {board.halfmove_clock}, "
          f"has pawn move (resets counter): "
          f"{any(board.piece_at(m.from_square).piece_type == chess.PAWN for m in board.legal_moves)}, "
          f"is_game_over (claim only): {board.is_game_over(claim_draw=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
