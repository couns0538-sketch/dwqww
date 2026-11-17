#!/usr/bin/env python3
"""Did the bail DECIDE any game? Paired comparison on identical openings.

Q2 asks "of the games that reach one, how many were decided by it". A per-position
cost distribution does not answer that: a 300 cp swing in an already-decided game
decides nothing. This plays the SAME opening prefix twice -- once with the shipped
base build, once with the bail-disarmed instrument -- and compares the outcomes. Both
games are deterministic at fixed depth, so every difference is attributable to the
bail and nothing else.

ADJUDICATION is python-chess at claim_draw=False (real game-over only) plus a ply cap.
Games that hit the cap are recorded as such and counted separately, never folded into
win/loss.

The comparison is reported as a paired table: same prefix, base result vs nobail
result, plus whether the two games diverged at all (they always will, once one bails
and the other searches). What matters is the RESULT column.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from predicates import is_drawn_root  # noqa: E402
from uci import Engine  # noqa: E402
from play_all import make_prefix  # noqa: E402

# Evidence root: override with FORGE_EXPOSURE_ROOT. Defaults to the parent of scripts/.
ROOT = os.environ.get("FORGE_EXPOSURE_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BUILDS = {"base": os.path.join(ROOT, "build-base", "forge"),
          "patched": os.path.join(ROOT, "build-patched", "forge"),
          "nobail": os.path.join(ROOT, "build-nobail", "forge")}


def play(build: str, depth: int, prefix: list[str], max_plies: int) -> dict:
    eng = Engine(BUILDS[build])
    board = chess.Board()
    for uci in prefix:
        board.push_uci(uci)
    plies = 0
    firings = 0
    first_firing_ply = None
    while plies < max_plies:
        fired, _ = is_drawn_root(board)
        if fired:
            firings += 1
            if first_firing_ply is None:
                first_firing_ply = len(board.move_stack)
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
    if board.is_checkmate():
        res = "loss_for_side_to_move" if board.turn == chess.WHITE else "win_for_white"
        result = "0-1" if board.turn == chess.WHITE else "1-0"
    elif board.is_game_over(claim_draw=False):
        result = "1/2-1/2"
    else:
        result = "cap"
    return {
        "build": build,
        "plies": plies,
        "n_moves": len(board.move_stack),
        "moves": [m.uci() for m in board.move_stack],
        "firings": firings,
        "first_firing_ply": first_firing_ply,
        "result": result,
        "term": ("checkmate" if board.is_checkmate() else
                 "stalemate" if board.is_stalemate() else
                 "seventyfive" if board.is_seventyfive_moves() else
                 "fivefold" if board.is_fivefold_repetition() else "cap"),
    }


def pair(args) -> dict:
    depth, prefix, max_plies, game = args
    out = {"game": game, "prefix": prefix}
    for build in ("base", "nobail"):
        out[build] = play(build, depth, prefix, max_plies)
    out["base_reached_firing"] = out["base"]["firings"] > 0
    out["same_result"] = out["base"]["result"] == out["nobail"]["result"]
    out["base_result"] = out["base"]["result"]
    out["nobail_result"] = out["nobail"]["result"]
    # Did the games diverge at the first firing?
    out["diverged"] = out["base"]["moves"] != out["nobail"]["moves"]
    return out


def decisive_to_draw_split(reached: list[dict]) -> dict:
    """Of the decisive->draw games, how many had the bailing side winning vs losing?

    `first_firing_ply` is `len(board.move_stack)` at the firing, so an even count means
    White was to move there. Comparing that with the base result says whether the side
    that bailed went on to win or lose the base game.
    """
    won = lost = 0
    for r in reached:
        if r["base_result"] not in ("1-0", "0-1") or r["nobail_result"] != "1/2-1/2":
            continue
        firing_ply = r["base"]["first_firing_ply"]
        if firing_ply is None:
            continue
        bailing_is_white = (firing_ply % 2 == 0)
        base_won_white = (r["base_result"] == "1-0")
        if bailing_is_white == base_won_white:
            won += 1
        else:
            lost += 1
    return {"n": won + lost, "bailing_side_won_base": won, "bailing_side_lost_base": lost}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--games", type=int, default=100)
    ap.add_argument("--max-plies", type=int, default=300)
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    args = ap.parse_args()

    import random
    rng = random.Random(args.seed)
    work = []
    for i in range(args.games):
        plen = rng.randint(3, 8)
        prefix = make_prefix(rng, plen)
        work.append((args.depth, prefix, args.max_plies, i))

    rows = []
    with mp.Pool(args.jobs) as pool:
        for row in pool.imap_unordered(pair, work, chunksize=1):
            rows.append(row)
            if len(rows) % 20 == 0:
                print(f"  {len(rows)}/{args.games}", flush=True)
    rows.sort(key=lambda r: r["game"])

    reached = [r for r in rows if r["base_reached_firing"]]
    changed = [r for r in reached if not r["same_result"]]
    summary = {
        "depth": args.depth, "games": len(rows), "max_plies": args.max_plies,
        "games_reaching_firing": len(reached),
        "games_whose_result_changed": len(changed),
        "change_rate_among_reached": (len(changed) / len(reached)) if reached else None,
        "change_rate_all_games": len(changed) / len(rows) if rows else None,
        "results_base": {k: sum(1 for r in rows if r["base_result"] == k)
                         for k in ("1-0", "0-1", "1/2-1/2", "cap")},
        "results_nobail": {k: sum(1 for r in rows if r["nobail_result"] == k)
                           for k in ("1-0", "0-1", "1/2-1/2", "cap")},
        # Decompose the decisive -> draw cases by WHO was to move at the firing. Without
        # this split the direction of the association is easy to over-read: "the bail
        # concedes" predicts that the side which bailed lost, and that holds for only
        # part of the group.
        "decisive_to_draw_split": decisive_to_draw_split(reached),
        "rows": rows,
    }
    with open(args.out, "w") as fh:
        json.dump(summary, fh, indent=1)
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
