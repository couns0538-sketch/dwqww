#!/usr/bin/env python3
"""f1_8902.py EXE OUTDIR

F1: the brief's area-1 "known" line — "an impossible-castling FEN is ACCEPTED
(perft 3 8,902 against python-chess 8,802)" — is a misdiagnosis.

8,902 is startpos perft 3 and 8,802 is python-chess perft 3 of
  rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1
(castling rights KQ but no rook on h1). This build REFUSES that FEN and then searches
THE OLD POSITION (startpos), which is where 8,902 comes from.

Cases (each in a FRESH process, raw output kept):
  A  FEN only, fresh process                        -> refused + perft 3 of startpos
  B  startpos, then the FEN, then perft 3            -> refused + perft 3 of startpos
  C  the FEN, then a DIFFERENT legal FEN, perft 3     -> second command takes effect
     (proves the stickiness lasts only until the next successful position command)
"""
import os
import subprocess
import sys

import chess

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1"
OTHER = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"


def perft_py(fen, d):
    b = chess.Board(fen)

    def rec(bd, depth):
        if depth == 0:
            return 1
        t = 0
        for m in bd.legal_moves:
            bd.push(m)
            t += rec(bd, depth - 1)
            bd.pop()
        return t
    return rec(b, d)


def run(exe, outdir, name, lines):
    env = dict(os.environ)
    for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
        env.pop(k, None)
    p = subprocess.run([exe], input="\n".join(lines + ["quit"]) + "\n", text=True,
                       capture_output=True, timeout=300, env=env)
    with open(os.path.join(outdir, name + ".txt"), "w") as fh:
        fh.write("=== exe: %s\n" % os.path.abspath(exe))
        fh.write("=== lines sent:\n" + "\n".join(">>> " + s for s in lines) + "\n")
        fh.write("=== stdout:\n" + p.stdout + "\n=== stderr:\n" + p.stderr)
        fh.write("=== returncode: %d\n" % p.returncode)
    return p.stdout


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    a = run(exe, outdir, "A_fen_only", ["position fen " + FEN, "isready", "go perft 3"])
    b = run(exe, outdir, "B_startpos_then_fen",
            ["position startpos", "isready", "position fen " + FEN, "isready", "go perft 3"])
    c = run(exe, outdir, "C_fen_then_other",
            ["position fen " + FEN, "isready", "position fen " + OTHER, "isready", "go perft 3"])

    def nodes(o):
        n = [l.split()[1] for l in o.splitlines() if l.startswith("nodes ")]
        return n[0] if n else "-"

    rows = [
        ("A  FEN only (fresh process)", "refused" if "invalid FEN" in a else "accepted", nodes(a)),
        ("B  startpos then FEN", "refused" if "invalid FEN" in b else "accepted", nodes(b)),
        ("C  FEN then a legal FEN", "refused" if "invalid FEN" in c else "accepted", nodes(c)),
    ]
    py = perft_py(FEN, 3)
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write("| case | answer to `position fen` | perft 3 nodes |\n|---|---|---|\n")
        for name, ans, n in rows:
            fh.write("| %s | %s | %s |\n" % (name, ans, n))
        fh.write("\nreference numbers: startpos perft 3 = 8902; python-chess perft 3 of the "
                 "impossible-castling FEN = %d\n" % py)
        fh.write("\nThe refused command's answer line (case A) was:\n")
        for ln in a.splitlines():
            if ln.startswith("info string"):
                fh.write("    " + ln + "\n")
    print(open(os.path.join(outdir, "summary.md")).read())


if __name__ == "__main__":
    main()
