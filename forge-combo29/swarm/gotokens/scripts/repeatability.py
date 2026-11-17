#!/usr/bin/env python3
"""Repeatability of the 0-ms clock forms.

`go movetime 0`, `go movetime abc` and `go movetime -1` all reach
`limits.movetime_ms == 0`, which search.cpp turns into `hard_limit_ms_ = 1`.
Whether the root check `elapsed_ms() >= hard_limit_ms_` fires BEFORE or AFTER
setup therefore decides between "first legal move, zero info lines" and "a real
shallow search" -- two different wire outcomes for one limit value.

A matrix row that reports one of those as though it were the answer is reporting
a race. This measures the distribution instead: N fresh processes per command.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from go_probe import MIDGAME_WHITE, run_cell, verdict  # noqa: E402

BUILD = "base@6b98f217 (g++ 13.3.0, sha256 e06310ec)"

COMMANDS = [
    "go movetime 0",
    "go movetime abc",
    "go movetime -1",
    "go movetime 1",
    "go movetime 100",
    "go wtime 0",
    "go wtime abc",
    "go depth 5 nodes 0",
    "go nodes 0",
]


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/base/forge"
    repeats = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    out_dir = Path(__file__).resolve().parent.parent / "evidence"
    report = []
    for command in COMMANDS:
        outcomes = collections.Counter()
        detail = []
        for _ in range(repeats):
            c = run_cell(exe, command, MIDGAME_WHITE, False, 20.0, build=BUILD)
            key = (verdict(c), c.bestmove, c.max_depth, c.last_nodes, c.info_depth_lines)
            outcomes[key] += 1
            detail.append(key)
        print(f"\n{command}   ({repeats} fresh processes)", flush=True)
        for (v, bm, d, n, lines), count in outcomes.most_common():
            print(f"   {count:>2}x  {v:18s} bm={bm} depth={d} nodes={n} lines={lines}", flush=True)
        report.append(
            {
                "go": command,
                "repeats": repeats,
                "outcomes": [
                    {
                        "count": count,
                        "verdict": v,
                        "bestmove": bm,
                        "max_depth": d,
                        "last_nodes": n,
                        "info_depth_lines": lines,
                    }
                    for (v, bm, d, n, lines), count in outcomes.most_common()
                ],
                "build": BUILD,
            }
        )
    (out_dir / "repeatability.json").write_text(json.dumps(report, indent=2) + "\n")
    print("\nstable:", [r["go"] for r in report if len(r["outcomes"]) == 1], flush=True)
    print("UNSTABLE:", [r["go"] for r in report if len(r["outcomes"]) > 1], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
