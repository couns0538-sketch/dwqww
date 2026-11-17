#!/usr/bin/env python3
"""Per-switch honesty-pin sweep.

A search heuristic is expected to move bench node counts: bench is a SEARCH, and
changing search changes the tree. That is not a pin violation, and calling it one
would drown the real signal.

The pin that a search switch cannot legitimately move is `perft`: perft walks
every legal move to a fixed depth and never consults evaluation, history,
pruning or the clock. A switch that moves perft has touched move generation or
the board, which is a correctness bug in a mechanism that has nothing to do with
a search heuristic.

So this sweep reports both, and grades them differently:
  * perft 5 must be 4,865,609 for every switch  -> PASS/FAIL
  * bench 11/16 are RECORDED, and the delta is reported, not graded.
It also re-checks the four pins on the baseline build, so "unchanged" is
anchored to a verified baseline rather than to the expected constants.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import driver  # noqa: E402
from audit import SWITCHES  # noqa: E402

PINS = {"bench11": 312866, "bench13": 862329, "bench16": 3024920}
PERFT5 = 4865609


def read_bench(engine: driver.Engine, depth: int) -> int | None:
    # `bench` prints an `info string bench depth N nodes M ...` line and no
    # bestmove, so it is read directly rather than through go_depth.
    engine.send(f"bench {depth}")
    lines = engine._read_until(lambda ls: any("info string bench" in l for l in ls), timeout=600)
    for line in lines:
        if "info string bench" in line:
            for token, value in zip(line.split()[3::2], line.split()[4::2]):
                if token == "nodes":
                    return int(value)
    return None


def read_perft(engine: driver.Engine) -> int | None:
    engine.send("position startpos")
    engine.send("go perft 5")
    lines = engine._read_until(lambda ls: any(l.startswith("nodes ") for l in ls), timeout=600)
    for line in lines:
        if line.startswith("nodes "):
            return int(line.split()[1])
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    rows = []
    for name in ["BASELINE"] + SWITCHES:
        options = {} if name == "BASELINE" else {name: "true"}
        with driver.Engine(args.engine, options=options, timeout=600) as engine:
            bench11 = read_bench(engine, 11)
            bench13 = read_bench(engine, 13)
            bench16 = read_bench(engine, 16)
            perft5 = read_perft(engine)
        row = {
            "switch": name,
            "bench11": bench11,
            "bench13": bench13,
            "bench16": bench16,
            "perft5": perft5,
            "bench11_delta": None if bench11 is None else bench11 - PINS["bench11"],
            "bench16_delta": None if bench16 is None else bench16 - PINS["bench16"],
            "perft5_moved": perft5 != PERFT5,
            "verdict": "PASS" if perft5 == PERFT5 else "**FAIL perft moved**",
        }
        rows.append(row)
        print(f"{name:22s} bench11={bench11} ({row['bench11_delta']:+d}) "
              f"bench16={bench16} ({row['bench16_delta']:+d}) perft5={perft5} {row['verdict']}",
              flush=True)

    base = rows[0]
    report = {
        "pins": {"bench11": PINS["bench11"], "bench13": PINS["bench13"],
                 "bench16": PINS["bench16"], "perft5": PERFT5},
        "baseline_reproduces_expected": (
            base["bench11"] == PINS["bench11"] and base["bench13"] == PINS["bench13"]
            and base["bench16"] == PINS["bench16"] and base["perft5"] == PERFT5
        ),
        "any_perft_moved": any(r["perft5_moved"] for r in rows),
        "rows": rows,
    }
    with open(os.path.join(args.out, "pins-per-switch.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    if not report["baseline_reproduces_expected"]:
        print("BASELINE DOES NOT REPRODUCE THE PINS — this build is not the audit base")
        return 1
    return 0 if not report["any_perft_moved"] else 1


if __name__ == "__main__":
    sys.exit(main())
