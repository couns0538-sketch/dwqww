#!/usr/bin/env python3
"""known8902.py EXE OUTDIR

The brief's area-1 "known" line says: "an impossible-castling FEN is ACCEPTED
(perft 3 8,902 against python-chess 8,802)".

8,902 is startpos perft 3. This script tests whether the 8,902 seen by whoever wrote
that line was the START POSITION LEFT OVER from a REFUSED position command, rather than
the impossible-castling FEN being searched.

For each candidate "impossible castling" FEN:
  - is it accepted at all by this build?
  - perft 3 with the FEN as the FIRST and ONLY position command (fresh process);
  - perft 3 after `position startpos` was sent first;
  - python-chess perft 3 of the same FEN.
"""
import os
import subprocess
import sys

import chess

CASES = [
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "4k3/8/8/8/8/8/8/R3K3 w Kk - 0 1",
    "4k3/8/8/8/8/8/8/4K3 w KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/4K3 w KQkq - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1",
    "4k2r/8/8/8/8/8/8/4K3 w Kq - 0 1",
]


def perft_py(fen, depth):
    b = chess.Board(fen)
    def rec(bd, d):
        if d == 0:
            return 1
        t = 0
        for m in bd.legal_moves:
            bd.push(m)
            t += rec(bd, d - 1)
            bd.pop()
        return t
    return rec(b, depth)


def eng(exe, lines):
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    proc = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                          capture_output=True, timeout=300, env=env)
    return proc.stdout, proc.stderr


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    lines_out = []
    for i, fen in enumerate(CASES):
        o1, e1 = eng(exe, ["position fen " + fen, "isready", "go perft 3"])
        o2, e2 = eng(exe, ["position startpos", "isready", "position fen " + fen, "isready", "go perft 3"])
        with open(os.path.join(outdir, "case_%02d.txt" % i), "w") as fh:
            fh.write("fen: %s\n--- A: FEN only\n%s%s\n--- B: startpos then FEN\n%s%s\n"
                     % (fen, o1, e1, o2, e2))
        n1 = [l.split()[1] for l in o1.splitlines() if l.startswith("nodes ")]
        n2 = [l.split()[1] for l in o2.splitlines() if l.startswith("nodes ")]
        acc = "invalid FEN" not in o1
        try:
            py = perft_py(fen, 3)
        except Exception as exc:
            py = type(exc).__name__
        lines_out.append("| %d | `%s` | %s | %s | %s | %s |" %
                         (i, fen, acc, n1[0] if n1 else "-", n2[0] if n2 else "-", py))
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write("| # | FEN | accepted | perft3 (FEN first) | perft3 (startpos first) | python-chess perft3 |\n")
        fh.write("|---|---|---|---|---|---|\n")
        fh.write("\n".join(lines_out) + "\n")
    print(open(os.path.join(outdir, "summary.md")).read())


if __name__ == "__main__":
    main()
