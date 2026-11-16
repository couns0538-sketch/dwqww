#!/usr/bin/env python3
"""swarm seat 01, job 1: build 20,000 mutated FENs from G (set_G.epd) and R (set_R.fens).

Each base FEN gets exactly one random mutation, chosen with SEED 101:
  replace  - one character replaced by a random FEN-legal character (or a junk char)
  insert   - one character inserted at a random offset
  delete   - one character removed
  swap     - two of the six space-separated fields exchanged
  drop     - one of the six fields removed
Output CSV: index,base_set,mutation_kind,mutation_detail,mutated_fen
The mutation is written beside the FEN exactly as the job asks.
"""
import csv
import random
import sys

SEED = 101
TOTAL = 20000
CHAR_POOL = "12345678rnbqkpRNBQKP/-w"


def load(path, tag):
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            out.append((tag, line))
    return out


def mutate(rng, fen):
    fields = fen.split(" ")
    kind = rng.choice(["replace", "insert", "delete", "swap", "drop"])
    if kind in ("replace", "insert", "delete"):
        pos = rng.randrange(len(fen))
        if kind == "replace":
            ch = rng.choice(CHAR_POOL)
            new = fen[:pos] + ch + fen[pos + 1:]
            detail = "replace offset %d '%s'->'%s'" % (pos, fen[pos], ch)
        elif kind == "insert":
            ch = rng.choice(CHAR_POOL)
            new = fen[:pos] + ch + fen[pos:]
            detail = "insert offset %d '%s'" % (pos, ch)
        else:
            ch = fen[pos]
            new = fen[:pos] + fen[pos + 1:]
            detail = "delete offset %d '%s'" % (pos, ch)
        return kind, detail, new
    if kind == "swap":
        if len(fields) < 2:
            return "swap", "no-op (single field)", fen
        i, j = rng.sample(range(len(fields)), 2)
        fields[i], fields[j] = fields[j], fields[i]
        return kind, "swap fields %d and %d" % (i + 1, j + 1), " ".join(fields)
    if len(fields) < 2:
        return "drop", "no-op (single field)", fen
    i = rng.randrange(len(fields))
    detail = "drop field %d '%s'" % (i + 1, fields[i])
    del fields[i]
    return kind, detail, " ".join(fields)


def main(out_csv):
    rng = random.Random(SEED)
    g_pool = load(sys.argv[2], "G")
    r_pool = load(sys.argv[3], "R")
    rows = []
    for idx in range(TOTAL):
        # half the FENs from each set, as the job asks for both
        pool = g_pool if rng.random() < 0.5 else r_pool
        tag, fen = pool[rng.randrange(len(pool))]
        kind, detail, new = mutate(rng, fen)
        rows.append((idx, tag, kind, detail, new))
    with open(out_csv, "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["idx", "base_set", "mutation_kind", "mutation_detail", "mutated_fen"])
        for r in rows:
            w.writerow(r)
    print("wrote %d mutated FENs from %d G + %d R base positions" % (len(rows), len(g_pool), len(r_pool)))


if __name__ == "__main__":
    main(sys.argv[1])
