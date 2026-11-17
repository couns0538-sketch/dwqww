#!/usr/bin/env python3
"""Interleaved repeatability for the two forms that reach the same limit value.

`go movetime 0` and `go movetime abc` both set `limits.movetime_ms = 0`, so they
must produce the same distribution. Measuring them in separate blocks would let
a machine-load trend masquerade as a difference between the forms, so this runs
them alternately and reports both, plus a third arm (`go movetime 1`) that
should sit between "0 means stop" and a real budget.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from go_probe import MIDGAME_WHITE, run_cell, verdict  # noqa: E402

BUILD = "base@6b98f217 (g++ 13.3.0, sha256 e06310ec)"
ARMS = ["go movetime 0", "go movetime abc", "go movetime 1"]


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/base/forge"
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    tally = {arm: collections.Counter() for arm in ARMS}
    for r in range(rounds):
        for arm in ARMS:
            c = run_cell(exe, arm, MIDGAME_WHITE, False, 20.0, build=BUILD)
            tally[arm][(verdict(c), c.bestmove, c.max_depth, c.last_nodes)] += 1
        if (r + 1) % 10 == 0:
            print(f"  {r + 1} rounds", file=sys.stderr, flush=True)
    report = []
    for arm in ARMS:
        outcomes = [
            {"count": n, "verdict": v, "bestmove": bm, "max_depth": d, "last_nodes": nodes}
            for (v, bm, d, nodes), n in tally[arm].most_common()
        ]
        print(f"\n{arm}  ({rounds} fresh processes, interleaved)")
        for o in outcomes:
            print(f"   {o['count']:>2}x  {o['verdict']:18s} bm={o['bestmove']} depth={o['max_depth']} nodes={o['last_nodes']}")
        report.append({"go": arm, "repeats": rounds, "distinct_outcomes": len(outcomes), "outcomes": outcomes, "build": BUILD})
    out = Path(__file__).resolve().parent.parent / "evidence" / "movetime_zero_interleaved.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print("\ndistinct outcome counts:", {r["go"]: r["distinct_outcomes"] for r in report})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
