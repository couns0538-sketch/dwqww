#!/usr/bin/env python3
"""Count every drawn root in engine games -- the population that reaches the guard.

Two rates are measured, and they are different questions:

  GAME rate   -- of N games, how many contain at least one position where the bail
                 fires. This is "is a consumer of this engine exposed".
  PLY  rate   -- firing positions per 1,000 plies played. This is "how often does a
                 long game walk into it", and it needs n because a bare count cannot
                 be distinguished from a rare event.

WHY THE GAME CONTINUES PAST A FIRING. An earlier version stopped at the first drawn
root, which makes "firings per 1,000 plies" identically equal to the game rate and
measures nothing about density. Games here run to a ply cap (or real game-over) with
every firing recorded, so both rates come from one run.

STOP RULE: `is_game_over(claim_draw=False)`. python-chess's claim rule ends a game at a
TWOFOLD (the side to move could claim by moving), one ply before the engine's guard --
which needs three occurrences -- could fire. With claim_draw=True the threefold arm is
truncated before it can be measured; that defect was observed directly (17 of 31 games
ended "claim" with the guard never having fired).

All counting uses the engine's own three predicates, reimplemented in predicates.py and
validated against the binary by oracle.py.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import random
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from predicates import is_drawn_root, reason, endgame_type  # noqa: E402
from uci import Engine  # noqa: E402

# Evidence root: override with FORGE_EXPOSURE_ROOT. Defaults to the parent of scripts/.
ROOT = os.environ.get("FORGE_EXPOSURE_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OPENINGS = [
    ([], "startpos"),
    (["e2e4"], "1.e4"), (["d2d4"], "1.d4"), (["c2c4"], "1.c4"), (["g1f3"], "1.Nf3"),
    (["b2b3"], "1.b3"), (["f2f4"], "1.f4"), (["g2g3"], "1.g3"), (["b1c3"], "1.Nc3"),
    (["e2e4", "e7e5"], "open game"), (["e2e4", "c7c5"], "Sicilian"),
    (["e2e4", "e7e6"], "French"), (["e2e4", "c7c6"], "Caro-Kann"),
    (["e2e4", "d7d6"], "Pirc"), (["e2e4", "g8f6"], "Alekhine"),
    (["e2e4", "d7d5"], "Scandinavian"), (["e2e4", "g7g6"], "Modern"),
    (["d2d4", "d7d5"], "closed game"), (["d2d4", "g8f6"], "Indian"),
    (["d2d4", "e7e6"], "QGD complex"), (["d2d4", "f7f5"], "Dutch"),
    (["d2d4", "d7d6"], "King's Indian"), (["c2c4", "e7e5"], "English, reversed"),
    (["c2c4", "c7c5"], "English, symmetric"), (["c2c4", "g8f6"], "English, Indian"),
    (["c2c4", "e7e6"], "English, QGD"), (["g1f3", "d7d5"], "Réti"),
    (["g1f3", "g8f6"], "Réti, double"), (["g1f3", "c7c5"], "Réti, Sicilian"),
    (["e2e4", "e7e5", "g1f3"], "Italian"), (["e2e4", "e7e5", "f1c4"], "Italian, Bc4"),
    (["d2d4", "d7d5", "c2c4"], "QGD"), (["d2d4", "g8f6", "c2c4"], "Indian, c4"),
    (["e2e4", "c7c5", "g1f3"], "Sicilian, Nf3"), (["c2c4", "e7e5", "b1c3"], "English, Nc3"),
]


def make_prefix(rng: random.Random, length: int) -> list[str]:
    """A random legal opening prefix -- the source of game-to-game diversity.

    WHY RANDOM PREFIXES RATHER THAN A LIST OF NAMED OPENINGS: the engine is fully
    deterministic at a fixed depth, so N games from one prefix are ONE game counted
    N times. A first version of this harness cycled a 35-entry opening list 200
    times and produced 35 distinct games with each reported as 200 -- a fake n. The
    prefixes here are drawn from a seeded RNG, so every game is a genuinely
    different game and the sample size is the number of prefixes.
    """
    board = chess.Board()
    moves = []
    for _ in range(length):
        options = list(board.legal_moves)
        if not options:
            break
        move = rng.choice(options)
        board.push(move)
        moves.append(move.uci())
    return moves


def play_game(args) -> dict:
    path, depth, prefix, prefix_len, seed, max_plies, game_id = args
    eng = Engine(path)
    board = chess.Board()
    for uci in prefix:
        board.push_uci(uci)

    firings = []
    plies = 0
    while plies < max_plies:
        fired, p = is_drawn_root(board)
        if fired:
            firings.append({
                "ply": plies,
                # The move count at this exact position. Recording it removes an
                # ambiguity that produced 35 bogus rows downstream: `plies` counts
                # ENGINE moves only and excludes the opening prefix, so a firing's
                # "ply" was not the length of the move list that reaches it.
                "n_moves": len(board.move_stack),
                "reason": reason(p),
                "halfmove": p["halfmove_value"],
                "legal": p["legal"],
                "fen": board.fen(),
                "endgame_type": endgame_type(board),
                "side": "white" if board.turn == chess.WHITE else "black",
                "material_total": sum(len(board.pieces(pt, c)) for pt in
                                      (chess.PAWN, chess.KNIGHT, chess.BISHOP,
                                       chess.ROOK, chess.QUEEN) for c in (True, False)),
            })
        if board.is_game_over(claim_draw=False):
            break
        moves = " ".join(m.uci() for m in board.move_stack)
        pos = ("position startpos moves " + moves) if moves else "position startpos"
        r = eng.search(pos, f"go depth {depth}")
        if not r["bestmove"] or r["bestmove"] == "(none)":
            break
        try:
            board.push_uci(r["bestmove"])
        except ValueError:
            break
        plies += 1
    eng.quit()
    return {
        "game": game_id,
        "seed": seed,
        "prefix": prefix,
        "prefix_len": prefix_len,
        "plies": plies,
        "moves": [m.uci() for m in board.move_stack],
        "firings": firings,
        "n_firings": len(firings),
        "term": ("checkmate" if board.is_checkmate() else
                 "stalemate" if board.is_stalemate() else
                 "seventyfive" if board.is_seventyfive_moves() else
                 "fivefold" if board.is_fivefold_repetition() else
                 "cap"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, required=True)
    ap.add_argument("--games", type=int, required=True)
    ap.add_argument("--max-plies", type=int, default=300)
    ap.add_argument("--build", default="base")
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--prefix-min", type=int, default=3)
    ap.add_argument("--prefix-max", type=int, default=8)
    args = ap.parse_args()

    path = os.path.join(ROOT, f"build-{args.build}", "forge")
    rng = random.Random(args.seed)
    work = []
    for i in range(args.games):
        prefix_len = rng.randint(args.prefix_min, args.prefix_max)
        prefix = make_prefix(rng, prefix_len)
        work.append((path, args.depth, prefix, prefix_len, args.seed, args.max_plies, i))

    rows = []
    with mp.Pool(args.jobs) as pool:
        for row in pool.imap_unordered(play_game, work, chunksize=1):
            rows.append(row)
            if len(rows) % 50 == 0:
                reached = sum(1 for r in rows if r["n_firings"])
                print(f"  {len(rows)}/{args.games} games, {reached} with >=1 firing",
                      flush=True)
    rows.sort(key=lambda r: r["game"])
    # Denominator for the ply rate: EVERY position the engine was asked about, i.e. the
    # opening prefix plus the engine moves. `plies` alone excludes the prefix and would
    # inflate the rate slightly; both are stored so the choice is visible.
    searched_positions = sum(len(r["moves"]) for r in rows)
    plies = sum(r["plies"] for r in rows)
    firings = sum(r["n_firings"] for r in rows)
    distinct = len({tuple(r["moves"]) for r in rows})
    out = {"build": args.build, "depth": args.depth, "games": len(rows),
           "distinct_games": distinct, "plies": plies,
           "searched_positions": searched_positions,
           "max_plies": args.max_plies, "firings": firings, "seed": args.seed,
           "games_with_firing": sum(1 for r in rows if r["n_firings"]),
           "rows": rows}
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: out[k] for k in
                      ("build", "depth", "games", "distinct_games", "plies",
                       "firings", "games_with_firing")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
