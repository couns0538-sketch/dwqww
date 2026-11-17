#!/usr/bin/env python3
"""gen2.py OUTDIR

THE CYCLE 2(c): area 1 job 1 again with the NEXT SEED. What differs from the first run
(job1, SEED 2101) is stated here before measuring, and is only the input:
  - SEED 2111 = 2101 + 10, as the brief prescribes (R with SEED + 10)
  - a NEW position set R2: random games from that seed, one position every 7 plies
  - a DIFFERENT mutation mix: the first run drew the five mutation kinds uniformly; this
    run weights them by the first run's MEASURED refusal rates, so that the accepted count
    is not dominated by one kind (that is the only lever that changed, and it is my own
    decision, written down before the run)
  - 20,000 FENs again, same engine (ASan+UBSan), same 19-F12-safe driver

Writes R2.fens and mutations2.tsv into OUTDIR.
"""
import os
import random
import sys

import chess

SEED = 2111
PLIES = 7
# weights measured in job1 (accepted/total per kind): replace 605/3939, delete 241/4173,
# insert 179/4019, swapfld 200/3904, dropfld 0/3965. Weight = 1 - acceptance rate, so the
# rarer kinds that DO get accepted are drawn more often.
WEIGHTS = {"replace": 0.85, "delete": 0.94, "insert": 0.95, "swapfld": 0.95, "dropfld": 1.0}


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
    open(os.path.join(outdir, "R2.fens"), "w").write("\n".join(R) + "\n")
    G = [l.strip() for l in open(os.path.join(outdir, "..", "job1", "set_G.fens")) if l.strip()]
    pool = [("G", f) for f in G] + [("R2", f) for f in R]
    kinds = list(WEIGHTS)
    weights = [WEIGHTS[k] for k in kinds]
    written = 0
    with open(os.path.join(outdir, "mutations2.tsv"), "w") as fh:
        while written < 20000:
            src, fen = pool[rng.randrange(len(pool))]
            kind = rng.choices(kinds, weights)[0]
            new, desc = mutate(rng, fen, kind)
            if new == fen:
                continue
            try:
                chess.Board(new); pv = "1"
            except Exception:
                pv = "0"
            written += 1
            fh.write("\t".join([str(written), src, kind, desc, new, pv]) + "\n")
    print("R2 positions:", len(R))
    print("mutations:", written)


if __name__ == "__main__":
    main()