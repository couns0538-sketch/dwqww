#!/usr/bin/env python3
"""case7_analyse.py - statistics over a finished game-driver JSON.

Kept separate from the driver so the analysis can be re-run on a saved match
without replaying it, and so the numbers in FINDINGS.md/CLOCK_TABLE.md have a
command that regenerates them from the committed data.

Checks the plan formula against EVERY move of the match:
  hard = min((clock - overhead) * TmHardPercent/100, soft * TmHardSoftMultiple)
  soft = (clock - overhead)/TmSoftDivisor + increment * TmIncrementPercent/100
with the defaults 22 / 75 / 60 / 5 and Move Overhead 10.

Run:  python3 case7_analyse.py case7_20_1000_100.json
"""

from __future__ import annotations

import collections
import json
import sys

import ucilib

OVERHEAD = 10
SOFT_DIV = 22
INC_PCT = 75
HARD_PCT = 60
MULT = 5


def plan(clock, increment):
    available = max(1, clock - OVERHEAD)
    soft = available // SOFT_DIV + increment * INC_PCT // 100
    hard = min(available * HARD_PCT // 100, soft * MULT)
    return max(1, min(soft, available)), max(1, min(hard, available))


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "case7_20_1000_100.json"
    with open(path) as handle:
        data = json.load(handle)
    games = data["per_game"]
    increment = data["config"]["inc_ms"]
    check = ucilib.Checker("case 7 analysis: %s" % path)

    plies = sum(game["plies"] for game in games)
    check.add(
        "every configured game is present",
        len(games) == data["config"]["games"],
        "%d of %d games" % (len(games), data["config"]["games"]),
    )
    check.add(
        "ZERO forfeits",
        not [g for g in games if g["outcome"] == "forfeit"],
        "0 forfeits over %d games / %d plies" % (len(games), plies),
    )
    check.add(
        "ZERO hangs",
        not [g for g in games if g["hang"]],
        "0 games without a bestmove",
    )
    check.add(
        "ZERO illegal bestmoves",
        not [g for g in games if g["outcome"] == "illegal_bestmove"],
        "0 illegal over %d plies" % plies,
    )
    check.add(
        "ZERO refused positions",
        not [g for g in games if g["invalid_fen_seen"]],
        "0 invalid-FEN diagnostics over %d positions" % plies,
    )

    moves = []
    for game in games:
        for move in game["moves"]:
            if move["clock_before_ms"] > 0:
                moves.append(move)
    ratios = sorted(move["charged_ms"] / move["clock_before_ms"] for move in moves)
    check.add(
        "no move used more than its remaining clock",
        ratios[-1] <= 1.0,
        "max used/available %.4f over %d moves (p99 %.4f, median %.4f)"
        % (ratios[-1], len(ratios), ratios[int(len(ratios) * 0.99)], ratios[len(ratios) // 2]),
    )

    # The plan formula against every move.
    over = []
    closest = []
    for move in moves:
        _, hard = plan(move["clock_before_ms"], increment)
        over.append(move["charged_ms"] - hard)
        closest.append((move["charged_ms"] / hard, move["clock_before_ms"], move["charged_ms"], hard))
    over.sort()
    closest.sort()
    check.add(
        "no move exceeded the predicted hard limit by more than 25 ms",
        over[-1] <= 25,
        "worst overshoot %+.1f ms over %d moves" % (over[-1], len(over)),
    )
    check.add(
        "the closest moves DO reach the predicted hard limit (the formula is the binding one)",
        closest[-1][0] > 0.95,
        "closest %.3f of the predicted hard limit (clock %d, charged %.1f, hard %d)"
        % (closest[-1][0], closest[-1][1], closest[-1][2], closest[-1][3]),
    )

    # Floor by clock bucket: the number that matters for forfeit risk.
    buckets = collections.defaultdict(list)
    for move in moves:
        clock = move["clock_before_ms"]
        key = "<=200" if clock <= 200 else "201-400" if clock <= 400 else "401-700" if clock <= 700 \
              else "701-1000" if clock <= 1000 else ">1000"
        buckets[key].append(move["charged_ms"])
    bucket_rows = []
    for key in ["<=200", "201-400", "401-700", "701-1000", ">1000"]:
        values = buckets.get(key, [])
        if not values:
            continue
        values.sort()
        bucket_rows.append(
            {
                "clock_bucket_ms": key,
                "moves": len(values),
                "max_charged_ms": round(values[-1], 1),
                "median_charged_ms": round(values[len(values) // 2], 1),
            }
        )
    for row in bucket_rows:
        print(
            "     %-9s n=%4d  max %6.1f ms  median %6.1f ms"
            % (row["clock_bucket_ms"], row["moves"], row["max_charged_ms"], row["median_charged_ms"])
        )

    low = [move for move in moves if move["clock_before_ms"] <= 200]
    check.add(
        "the floor was exercised (moves were made at a clock of 200 ms or less)",
        len(low) >= 10,
        "%d of %d moves at <=200 ms" % (len(low), len(moves)),
    )

    summary = check.summary()
    ucilib.emit(
        {
            "source": path,
            "config": data["config"],
            "games": len(games),
            "total_plies": plies,
            "moves_measured": len(moves),
            "min_clock_ms": min(game["min_clock_ms"] for game in games),
            "margin": {
                "max_used_over_available": round(ratios[-1], 4),
                "p99_used_over_available": round(ratios[int(len(ratios) * 0.99)], 4),
                "median_used_over_available": round(ratios[len(ratios) // 2], 4),
            },
            "formula_check": {
                "worst_overshoot_ms": round(over[-1], 1),
                "closest_to_predicted_hard": round(closest[-1][0], 3),
            },
            "buckets": bucket_rows,
            "summary": summary,
        },
        path.replace(".json", "_analysis.json"),
    )
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
