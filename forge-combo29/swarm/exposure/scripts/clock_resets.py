#!/usr/bin/env python3
"""Why random play cannot reach the fifty-move arm of the guard.

The audit's central claim is that the report's random-play null is vacuous. The
reachability table in FINDINGS.md section 1 shows that no game in a 4,600-game random
corpus ever reached halfmove 100. This script explains the MECHANISM, because the
report's own explanation ("random play mates long before the counter fills") is not
what happens: most of those games hit the ply cap, not a mate.

The counter is reset by any capture or pawn move. Random play does both constantly, so
the halfmove clock never accumulates. Measured here directly.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import random
import statistics

import chess

from paths import glob_under_root, load_json, open_json_out


def one(args) -> dict:
    seed, max_plies = args
    rng = random.Random(seed)
    board = chess.Board()
    resets = 0
    plies = 0
    max_run = 0
    run = 0
    while plies < max_plies and not board.is_game_over(claim_draw=False):
        move = rng.choice(list(board.legal_moves))
        is_reset = (board.is_capture(move) or
                    board.piece_type_at(move.from_square) == chess.PAWN)
        if is_reset:
            resets += 1
            run = 0
        else:
            run += 1
            max_run = max(max_run, run)
        board.push(move)
        plies += 1
    return {"seed": seed, "plies": plies, "resets": resets, "max_quiet_run": max_run,
            "final_halfmove": board.halfmove_clock}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=300)
    ap.add_argument("--max-plies", type=int, default=200)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    with mp.Pool() as pool:
        rows = pool.map(one, [(i, args.max_plies) for i in range(args.games)], chunksize=10)
    resets = [r["resets"] for r in rows]
    runs = [r["max_quiet_run"] for r in rows]
    plies = [r["plies"] for r in rows]
    out = {
        "games": len(rows),
        "mean_plies": statistics.mean(plies),
        "mean_resets": statistics.mean(resets),
        "median_resets": statistics.median(resets),
        "mean_longest_quiet_run": statistics.mean(runs),
        "max_longest_quiet_run": max(runs),
        "guard_needs": 100,
        "shortfall_factor": 100 / statistics.mean(runs) if statistics.mean(runs) else None,
    }
    print(json.dumps(out, indent=2))
    if args.out:
        with open_json_out(args.out) as fh:
            json.dump({**out, "rows": rows}, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
