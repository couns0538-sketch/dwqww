#!/usr/bin/env python3
"""Reproduce the original "0 drawn roots in 4,600 random games" null, and show WHY.

The report's exposure figure came from random play. This script plays the same kind of
corpus -- random legal moves -- and counts drawn roots with the SAME three predicates
used everywhere else in this audit. It is not here to dispute the count; it is here to
show the count is uninformative, by measuring the thing that makes it uninformative:

  * how the random games END (they mate or shuffle into a claim long before the
    engine's guard could fire on its own terms);
  * the distribution of the halfmove counter at game end (how far from 100);
  * how many games ever produced a position with halfmove >= 100, a threefold, or
    engine-insufficient material.

The point is the population, not the count: a null from a corpus that cannot reach the
condition is vacuous, and the way to show it is to measure the distance to the
condition rather than to assert it.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from predicates import is_drawn_root, reason  # noqa: E402
import os

# Evidence root: override with FORGE_EXPOSURE_ROOT. Defaults to the parent of scripts/.
ROOT = os.environ.get("FORGE_EXPOSURE_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def one_game(args) -> dict:
    seed, max_plies = args
    rng = random.Random(seed)
    board = chess.Board()
    plies = 0
    firings = []
    max_hm = 0
    saw_hm_100 = False
    saw_threefold = False
    saw_insufficient = False
    while plies < max_plies:
        fired, p = is_drawn_root(board)
        max_hm = max(max_hm, p["halfmove_value"])
        if p["halfmove"]:
            saw_hm_100 = True
        if p["threefold"]:
            saw_threefold = True
        if p["insufficient"]:
            saw_insufficient = True
        if fired:
            firings.append({"ply": plies, "reason": reason(p), "halfmove": p["halfmove_value"]})
        if board.is_game_over(claim_draw=False):
            break
        board.push(rng.choice(list(board.legal_moves)))
        plies += 1
    return {
        "seed": seed, "plies": plies, "firings": firings, "n_firings": len(firings),
        "max_halfmove": max_hm,
        "saw_halfmove_100": saw_hm_100,
        "saw_threefold_position": saw_threefold,
        "saw_insufficient_position": saw_insufficient,
        "term": ("checkmate" if board.is_checkmate() else
                 "stalemate" if board.is_stalemate() else
                 "seventyfive" if board.is_seventyfive_moves() else
                 "fivefold" if board.is_fivefold_repetition() else "cap"),
        "material_at_end": len(board.piece_map()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=4600)
    ap.add_argument("--max-plies", type=int, default=200)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import multiprocessing as mp
    work = [(i, args.max_plies) for i in range(args.games)]
    rows = []
    with mp.Pool() as pool:
        for r in pool.imap_unordered(one_game, work, chunksize=50):
            rows.append(r)
    rows.sort(key=lambda r: r["seed"])
    plies = sum(r["plies"] for r in rows)
    firings = sum(r["n_firings"] for r in rows)
    terms = collections.Counter(r["term"] for r in rows)
    maxh = [r["max_halfmove"] for r in rows]
    out = {
        "games": len(rows), "max_plies": args.max_plies, "plies": plies,
        "firings": firings,
        "games_with_firing": sum(1 for r in rows if r["n_firings"]),
        "games_ever_reaching_halfmove_100": sum(1 for r in rows if r["saw_halfmove_100"]),
        "games_ever_seeing_a_threefold_position": sum(1 for r in rows if r["saw_threefold_position"]),
        "games_ever_seeing_insufficient_material": sum(1 for r in rows if r["saw_insufficient_position"]),
        "max_halfmove_over_all_games": max(maxh),
        "median_max_halfmove": sorted(maxh)[len(maxh) // 2],
        "terms": dict(terms),
        "rows": rows,
    }
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
