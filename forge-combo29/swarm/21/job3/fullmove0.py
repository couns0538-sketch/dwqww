#!/usr/bin/env python3
"""fullmove0.py EXE OUTDIR

F: Forge REFUSES `fullmove 0` while python-chess ACCEPTS it (python-chess's status is
STATUS_VALID for fullmove 0; FEN writers in the wild emit it). Combined with the sticky
board, a GUI that loads such a FEN gets a move of the OLD game, not an error it can see.

This script measures how far the two disagree, case by case, and whether the disagreement
is only the counter or the game itself:
  A  `position fen <fullmove 0 FEN>` then perft 1     -> startpos 20 (refused, stale board)
  B  python-chess of the same FEN, legal move count   -> the real count
  C  the same FEN with fullmove 1 (what a fix would send) -> the real count from Forge
  D  a fullmove 0 FEN reached from a real game (G), same three questions
"""
import os
import subprocess
import sys

import chess

CASES = [
    ("king_and_rook", "4k3/8/8/8/8/8/8/4K2R w K - 0 0"),
    ("ruy_lopez_mid", "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 0"),
    ("startpos_fullmove0", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0"),
]


def eng(exe, lines, timeout=120):
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    p = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                       capture_output=True, timeout=timeout, env=env)
    return p


def nodes(p):
    return [ln.split()[1] for ln in p.stdout.splitlines() if ln.startswith("nodes ")]


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    rows = ["| case | FEN (fullmove 0) | Forge answer | Forge perft 1 | python-chess accepts | python legal moves | FEN with fullmove 1 | Forge perft 1 then |",
            "|---|---|---|---|---|---|---|---|"]
    detail = []
    for name, fen in CASES:
        a = eng(exe, ["position fen " + fen, "isready", "go perft 1"])
        with open(os.path.join(outdir, name + "_A.txt"), "w") as fh:
            fh.write(">>> position fen %s\n>>> isready\n>>> go perft 1\n%s\n%s\n"
                     % (fen, a.stdout, a.stderr))
        fixed = fen.rsplit(" ", 1)[0] + " 1"
        c = eng(exe, ["position fen " + fixed, "isready", "go perft 1"])
        with open(os.path.join(outdir, name + "_C.txt"), "w") as fh:
            fh.write(">>> position fen %s\n>>> isready\n>>> go perft 1\n%s\n%s\n"
                     % (fixed, c.stdout, c.stderr))
        try:
            b = chess.Board(fen)
            py_ok = True
            py_n = b.legal_moves.count()
            py_status = str(b.status())
        except Exception as exc:
            py_ok = False
            py_n = "-"
            py_status = type(exc).__name__
        ans = [ln for ln in a.stdout.splitlines() if ln.startswith("info string")]
        rows.append("| %s | `%s` | %s | %s | %s (%s) | %s | `%s` | %s |" % (
            name, fen, (ans[0] if ans else "accepted"), (nodes(a) or ["-"])[0],
            py_ok, py_status, py_n, fixed, (nodes(c) or ["-"])[0]))
        detail.append((name, fen, ans, nodes(a), py_ok, py_n, nodes(c)))
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
