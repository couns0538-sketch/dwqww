"""Summarise game records: termination, book exit ply, repetition, drawn-root book.

The checks this produces, and what each one can and cannot see:

  * "Every game terminates" is checked as: no `timeout`, no `engine_error`,
    no `illegal`, no `engine_no_move`, and no game that stopped only because it
    hit the ply cap. A ply-cap stop is reported separately rather than counted as
    a termination, because the engine did not end that game -- the harness did.
  * "No position repeats past the threefold rule" is checked against the actual
    repetition count of the final position, not merely against the termination
    label. A game labelled `threefold` whose count is 3 is correct; one with 4
    would mean the harness played on through a decided game.
  * Book exit ply is reported as a distribution, not a mean, because the whole
    question is whether the book has reach the graph says it has.
  * `book_on_drawn_root` counts plies where the book fired on a position that was
    ALREADY a repetition / 50-move / insufficient-material draw. That is the
    game-level form of trap 19a and it is reported as its own row so it is never
    folded into "the book played fine".
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter


def summarise(path: str) -> dict:
    games = json.load(open(path))
    n = len(games)
    if n == 0:
        return {"file": path, "games": 0, "error": "empty"}

    term = Counter(g["termination"] for g in games)
    exits = [g["exit_ply"] for g in games if g.get("exit_ply") is not None]
    plies = [g["plies"] for g in games]

    hard_failures = sum(term[k] for k in ("timeout", "engine_error", "illegal",
                                          "engine_no_move") if k in term)
    ply_cap = term.get("ply_cap", 0)

    # repetition sanity: no game may end with a position seen more than 3 times
    over_threefold = [g for g in games if g.get("max_repetition", 1) > 3]
    at_threefold = [g for g in games if g.get("max_repetition", 1) == 3]

    drawn_book = [g for g in games if g.get("book_on_drawn_root", 0) > 0]
    reentry = [g for g in games if g.get("book_reentry_plies", 0) > 0]
    ended_in_book = sum(1 for g in games if g.get("ended_in_book"))

    illegal_moves = sum(1 for g in games if g.get("illegal_engine_move"))

    return {
        "file": path,
        "tag": games[0].get("tag", ""),
        "engine": games[0].get("engine", ""),
        "book_depth": games[0].get("book_depth"),
        "book_variety": games[0].get("book_variety"),
        "games": n,
        "terminations": dict(term),
        "hard_failures": hard_failures,
        "ply_cap_hits": ply_cap,
        "all_terminated_by_rules_or_mate": hard_failures == 0 and ply_cap == 0,
        "illegal_engine_moves": illegal_moves,
        "games_ending_at_threefold_count": len(at_threefold),
        "games_over_threefold": len(over_threefold),
        "over_threefold_detail": [{"game": g["game"], "max_rep": g["max_repetition"],
                                   "termination": g["termination"]} for g in over_threefold],
        "book_exit_ply": {
            "min": min(exits) if exits else None,
            "max": max(exits) if exits else None,
            "mean": round(statistics.fmean(exits), 2) if exits else None,
            "median": statistics.median(exits) if exits else None,
            "distribution": dict(sorted(Counter(exits).items())),
        },
        "plies": {
            "min": min(plies), "max": max(plies),
            "mean": round(statistics.fmean(plies), 1), "median": statistics.median(plies),
        },
        "book_plies_total": sum(g.get("book_plies", 0) for g in games),
        "games_with_book_on_drawn_root": len(drawn_book),
        "book_on_drawn_root_events": sum(g.get("book_on_drawn_root", 0) for g in games),
        "book_on_drawn_root_detail": [
            {"game": g["game"], "events": g["book_on_drawn_detail"]} for g in drawn_book][:10],
        "games_that_reentered_book": len(reentry),
        "book_reentry_events": sum(g.get("book_reentry_plies", 0) for g in games),
        "games_ending_while_still_in_book": ended_in_book,
        "elapsed_s_total": round(sum(g.get("elapsed_s", 0) for g in games), 1),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    reports = [summarise(f) for f in args.files]
    json.dump(reports, open(args.out, "w"), indent=1)
    for r in reports:
        print(f"\n=== {r['tag'] or r['file']} ({r['games']} games, "
              f"depth {r['book_depth']}, variety {r['book_variety']}) ===")
        print(f"  terminations         : {r['terminations']}")
        print(f"  hard failures        : {r['hard_failures']}  ply-cap: {r['ply_cap_hits']}")
        print(f"  illegal engine moves : {r['illegal_engine_moves']}")
        print(f"  over threefold       : {r['games_over_threefold']}")
        print(f"  book exit ply        : {r['book_exit_ply']['distribution']} "
              f"(min {r['book_exit_ply']['min']}, max {r['book_exit_ply']['max']}, "
              f"median {r['book_exit_ply']['median']})")
        print(f"  book on drawn root   : {r['games_with_book_on_drawn_root']} games, "
              f"{r['book_on_drawn_root_events']} events")
        print(f"  re-entered book      : {r['games_that_reentered_book']} games, "
              f"{r['book_reentry_events']} events")
        print(f"  ended in book        : {r['games_ending_while_still_in_book']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
