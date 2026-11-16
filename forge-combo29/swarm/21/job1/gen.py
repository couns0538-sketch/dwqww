#!/usr/bin/env python3
"""gen.py — build set R (random games, SEED 2101) and 20,000 single-mutation FENs from G and R.

usage: gen.py R_OUT MUT_OUT [N_MUT]
Every random choice comes from random.Random(SEED) with SEED = 2101 (seat 21: SEED = S*100+1).
One position is taken every 7 plies of each random legal game.
Mutations (one per FEN, chosen at random among five kinds):
  replace  - replace one character of the whole FEN string with a random character
  insert   - insert one random character at a random offset
  delete   - delete one character
  swapfld  - swap two whitespace-separated fields
  dropfld  - delete one whitespace-separated field
Mutation text is written beside the mutated FEN so it can be replayed.
"""
import random
import sys

import chess

SEED = 2101
PLIES_PER_SAMPLE = 7


def random_games(rng, n_games):
    positions = []
    for _ in range(n_games):
        board = chess.Board()
        ply = 0
        while not board.is_game_over(claim_draw=False) and ply < 300:
            if ply % PLIES_PER_SAMPLE == 0 and ply > 0:
                positions.append(board.fen())
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
            ply += 1
    return positions


def mutate(rng, fen):
    kind = rng.choice(["replace", "insert", "delete", "swapfld", "dropfld"])
    alphabet = "0123456789prnbqkPRNBQK/- wb"
    if kind == "replace":
        i = rng.randrange(len(fen))
        ch = rng.choice(alphabet)
        out = fen[:i] + ch + fen[i + 1:]
        desc = "replace pos %d %r -> %r" % (i, fen[i], ch)
    elif kind == "insert":
        i = rng.randrange(len(fen) + 1)
        ch = rng.choice(alphabet)
        out = fen[:i] + ch + fen[i:]
        desc = "insert pos %d %r" % (i, ch)
    elif kind == "delete":
        i = rng.randrange(len(fen))
        out = fen[:i] + fen[i + 1:]
        desc = "delete pos %d %r" % (i, fen[i])
    elif kind == "swapfld":
        fields = fen.split()
        if len(fields) < 2:
            return None
        a, b = rng.sample(range(len(fields)), 2)
        fields[a], fields[b] = fields[b], fields[a]
        out = " ".join(fields)
        desc = "swap fields %d and %d" % (a + 1, b + 1)
    else:
        fields = fen.split()
        if len(fields) < 2:
            return None
        a = rng.randrange(len(fields))
        desc = "drop field %d %r" % (a + 1, fields[a])
        out = " ".join(fields[:a] + fields[a + 1:])
    if out == fen:
        return None
    return kind, desc, out


def py_verdict(fen):
    try:
        chess.Board(fen)
        return "1", "valid"
    except Exception as exc:  # python-chess raises on a malformed FEN
        return "0", type(exc).__name__


def main():
    r_out, mut_out = sys.argv[1], sys.argv[2]
    n_mut = int(sys.argv[3]) if len(sys.argv) > 3 else 20000
    rng = random.Random(SEED)

    R = random_games(rng, 145)
    with open(r_out, "w") as fh:
        for fen in R:
            fh.write(fen + "\n")

    G = [ln.strip() for ln in open("/tmp/G.fens") if ln.strip()]
    pool = [("G", f) for f in G] + [("R", f) for f in R]

    written = 0
    attempts = 0
    with open(mut_out, "w") as fh:
        while written < n_mut and attempts < n_mut * 20:
            attempts += 1
            src, fen = pool[rng.randrange(len(pool))]
            m = mutate(rng, fen)
            if m is None:
                continue
            kind, desc, out = m
            pv, why = py_verdict(out)
            fh.write("\t".join([str(written + 1), src, kind, desc, out, pv, why]) + "\n")
            written += 1
    print("R positions:", len(R))
    print("G positions:", len(G))
    print("mutated FENs written:", written)
    print("from G:", sum(1 for _ in open(mut_out) if "\tG\t" in _))
    print("from R:", sum(1 for _ in open(mut_out) if "\tR\t" in _))


if __name__ == "__main__":
    main()
