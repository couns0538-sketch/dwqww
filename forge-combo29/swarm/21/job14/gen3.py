#!/usr/bin/env python3
"""gen3.py OUTDIR

Third independent input set for area 1 job 1: SEED 2121, uniform mutation mix (matching job1,
so the three runs are comparable). Writes R3.fens and mutations3.tsv.
"""
import os
import random
import sys

import chess

SEED = 2121
PLIES = 7
KINDS = ["replace", "insert", "delete", "swapfld", "dropfld"]


def games(rng, n):
    out = []
    for _ in range(n):
        b = chess.Board()
        ply = 0
        while not b.is_game_over(claim_draw=False) and ply < 300:
            if ply and ply % PLIES == 0:
                out.append(b.fen())
            ms = list(b.legal_moves)
            if not ms:
                break
            b.push(rng.choice(ms))
            ply += 1
    return out


def mutate(rng, fen, kind):
    alpha = "0123456789prnbqkPRNBQK/- wb"
    if kind == "replace":
        i = rng.randrange(len(fen)); ch = rng.choice(alpha)
        return fen[:i] + ch + fen[i+1:], "replace %d %r->%r" % (i, fen[i], ch)
    if kind == "insert":
        i = rng.randrange(len(fen)+1); ch = rng.choice(alpha)
        return fen[:i] + ch + fen[i:], "insert %d %r" % (i, ch)
    if kind == "delete":
        i = rng.randrange(len(fen))
        return fen[:i] + fen[i+1:], "delete %d %r" % (i, fen[i])
    f = fen.split()
    if kind == "swapfld":
        a, b = rng.sample(range(len(f)), 2)
        f[a], f[b] = f[b], f[a]
        return " ".join(f), "swapfld %d/%d" % (a+1, b+1)
    a = rng.randrange(len(f))
    return " ".join(f[:a] + f[a+1:]), "dropfld %d" % (a+1)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(SEED)
    R = games(rng, 145)
    open(os.path.join(outdir, "R3.fens"), "w").write("\n".join(R) + "\n")
    here = os.path.dirname(os.path.abspath(__file__))
    G = [l.strip() for l in open(os.path.join(here, "..", "job1", "set_G.fens")) if l.strip()]
    pool = [("G", f) for f in G] + [("R3", f) for f in R]
    written = 0
    with open(os.path.join(outdir, "mutations3.tsv"), "w") as fh:
        while written < 20000:
            src, fen = pool[rng.randrange(len(pool))]
            kind = rng.choice(KINDS)
            new, desc = mutate(rng, fen, kind)
            if new == fen:
                continue
            try:
                chess.Board(new); pv = "1"
            except Exception:
                pv = "0"
            written += 1
            fh.write("\t".join([str(written), src, kind, desc, new, pv]) + "\n")
    print("R3 positions:", len(R), "mutations:", written)


if __name__ == "__main__":
    main()