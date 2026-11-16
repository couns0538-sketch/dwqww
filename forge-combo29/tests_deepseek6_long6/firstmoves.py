#!/usr/bin/env python3
"""firstmoves.py -- print "index rootFen m1 m2" for the first N positions of a fens file.

Uses the engine itself to get legal moves: `go perft 1` lists them, one line each.
The two moves are taken in the engine's own generation order, filtered to legal.

Usage: firstmoves.py --exe PATH --set FENS --limit N [--out FILE]
"""
import argparse
import os
import re
import subprocess
import sys

PERFT_MOVE = re.compile(r"^([a-h][1-8][a-h][1-8][nbrq]?):\s+(\d+)\s*$")


def load(path, limit):
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            out.append(line)
            if limit and len(out) >= limit:
                break
    return out


def legal_moves(exe, fen):
    inp = "position fen %s\ngo perft 1\nquit\n" % fen
    res = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=60)
    moves = []
    for line in res.stdout.splitlines():
        m = PERFT_MOVE.match(line.strip())
        if m and int(m.group(2)) > 0:
            moves.append(m.group(1))
    return moves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--set", required=True)
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--out", default="")
    ap.add_argument("--fen-out", default="")
    args = ap.parse_args()
    exe = os.path.abspath(args.exe)
    fens = load(args.set, args.limit)
    lines = []
    few = []
    for i, fen in enumerate(fens):
        ms = legal_moves(exe, fen)
        if len(ms) < 2:
            few.append((i, len(ms)))
            lines.append("%d | %s | %s | (fewer than two legal moves)" % (i, fen, " ".join(ms)))
            continue
        lines.append("%d | %s | %s %s" % (i, fen, ms[0], ms[1]))
    text = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    if args.fen_out:
        with open(args.fen_out, "w") as fh:
            for i, fen in enumerate(fens):
                fh.write(fen + "\n")
    print("positions %d, with fewer than two legal moves: %s" % (len(fens), few or "none"),
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
