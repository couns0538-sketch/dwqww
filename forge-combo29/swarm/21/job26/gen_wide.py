#!/usr/bin/env python3
"""gen_wide.py OUTDIR [N]

A WIDER mutation alphabet than every earlier sweep: multi-character corruptions.

Kinds (each applied once per FEN, the text recorded):
  trunc_rank      cut a rank field short at a random point
  dup_group       duplicate 2-4 characters inside a rank field
  swap_ranks      transpose two whole rank fields (rank order damaged)
  join_ranks      delete one '/' (two ranks merged)
  extra_slash     insert one extra '/'
  bad_piece       replace a random piece letter with a random non-piece character
  field_garbage   replace one of the six fields with random text
  short_rank      pad a rank field with digits so it exceeds 8 squares

Writes mutations_wide.tsv with the same columns as the earlier inputs:
  idx, src, kind, description, mutatedFEN, pythonAccepts(1/0)
"""
import os
import random
import string
import sys

import chess

SEED = 2101
KINDS = ["trunc_rank", "dup_group", "swap_ranks", "join_ranks", "extra_slash",
         "bad_piece", "field_garbage", "short_rank"]


def mutate(rng, fen, kind):
    parts = fen.split()
    if len(parts) < 6:
        return None, None
    ranks = parts[0].split("/")
    if kind == "trunc_rank":
        i = rng.randrange(len(ranks))
        cut = rng.randrange(0, max(1, len(ranks[i])))
        new = list(ranks)
        new[i] = ranks[i][:cut]
        parts[0] = "/".join(new)
        desc = "trunc_rank %d -> %r" % (i + 1, new[i])
    elif kind == "dup_group":
        i = rng.randrange(len(ranks))
        r = ranks[i]
        if len(r) < 2:
            return None, None
        a = rng.randrange(len(r) - 1)
        g = r[a:a + rng.randrange(2, 5)]
        new = list(ranks)
        new[i] = r[:a] + g + r[a:]
        parts[0] = "/".join(new)
        desc = "dup_group rank %d %r" % (i + 1, g)
    elif kind == "swap_ranks":
        a, b = rng.sample(range(8), 2)
        ranks[a], ranks[b] = ranks[b], ranks[a]
        parts[0] = "/".join(ranks)
        desc = "swap_ranks %d<->%d" % (a + 1, b + 1)
    elif kind == "join_ranks":
        if len(ranks) != 8:
            return None, None
        i = rng.randrange(7)
        joined = ranks[:i] + [ranks[i] + ranks[i + 1]] + ranks[i + 2:]
        parts[0] = "/".join(joined)
        desc = "join_ranks %d+%d" % (i + 1, i + 2)
    elif kind == "extra_slash":
        i = rng.randrange(len(ranks) + 1)
        new = ranks[:i] + [""] + ranks[i:]
        parts[0] = "/".join(new)
        desc = "extra_slash at %d" % (i + 1)
    elif kind == "bad_piece":
        i = rng.randrange(len(ranks))
        r = ranks[i]
        if not r:
            return None, None
        j = rng.randrange(len(r))
        ch = rng.choice("!#@$%^&*()[]{}<>,.;:?")
        new = list(ranks)
        new[i] = r[:j] + ch + r[j + 1:]
        parts[0] = "/".join(new)
        desc = "bad_piece rank %d %r->%r" % (i + 1, r[j], ch)
    elif kind == "field_garbage":
        i = rng.randrange(6)
        old = parts[i]
        parts[i] = "".join(rng.choice(string.ascii_letters + string.digits + "-")
                           for _ in range(rng.randrange(1, 6)))
        desc = "field_garbage field %d %r->%r" % (i + 1, old, parts[i])
    else:  # short_rank
        i = rng.randrange(len(ranks))
        new = list(ranks)
        new[i] = ranks[i] + str(rng.randrange(1, 9))
        parts[0] = "/".join(new)
        desc = "short_rank pad %d -> %r" % (i + 1, new[i])
    out = " ".join(parts)
    return (out, desc) if out != fen else (None, None)


def main():
    outdir = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(SEED)
    here = os.path.dirname(os.path.abspath(__file__))
    G = [l.strip() for l in open(os.path.join(here, "..", "job1", "set_G.fens")) if l.strip()]
    R = [l.strip() for l in open(os.path.join(here, "..", "job1", "set_R.fens")) if l.strip()]
    pool = [("G", f) for f in G] + [("R", f) for f in R]
    written = 0
    with open(os.path.join(outdir, "mutations_wide.tsv"), "w") as fh:
        guard = 0
        while written < n and guard < n * 40:
            guard += 1
            src, fen = pool[rng.randrange(len(pool))]
            kind = rng.choice(KINDS)
            new, desc = mutate(rng, fen, kind)
            if new is None:
                continue
            try:
                chess.Board(new)
                pv = "1"
            except Exception:
                pv = "0"
            written += 1
            fh.write("\t".join([str(written), src, kind, desc, new, pv]) + "\n")
    print("wide mutations:", written)


if __name__ == "__main__":
    main()