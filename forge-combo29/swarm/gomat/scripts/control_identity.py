#!/usr/bin/env python3
"""Check that the CONTROL ablation build is behaviourally the BASE engine.

The gate-defaults block injected by variants.py is a source change even when no
gate is enabled, so "control == base" is an assertion that has to be measured,
not assumed. This runs a fixed request set against both binaries and requires
identical bestmove, score, depth and node count on every one.

If this fails, every ablation delta in the report is contaminated and the report
must not be published.

Usage: control_identity.py --base build/forge --control /tmp/ab/control/build/forge
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402

# Deliberately mixed: sparse endgames (mate-rich), openings, a drawn root, and
# a position with one legal move. Depth and mate requests on both.
FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "8/5k2/8/6K1/1Q6/8/8/8 w - - 0 1",
    "k7/8/8/8/8/3R4/6K1/6R1 w - - 0 1",
    "8/8/8/4k3/8/4K3/8/8 w - - 0 1",
    "8/8/1Rr4k/8/8/7K/8/3Q4 w - - 0 1",
    "6k1/5ppp/8/8/8/8/8/4K2R w - - 0 1",
]
CMDS = ["go depth 1", "go depth 3", "go depth 5", "go depth 7",
        "go mate 1", "go mate 2", "go mate 3", "go mate 4"]


def probe(exe: str) -> list[dict]:
    out = []
    with Engine(exe, {"OwnBook": "false"}) as eng:
        for fen in FENS:
            for cmd in CMDS:
                eng.newgame()
                eng.setpos(fen)
                res = eng.go(cmd, timeout=120)
                out.append({
                    "fen": fen, "cmd": cmd, "bestmove": res.bestmove,
                    "score": res.last_score, "depth": res.last_depth,
                    "nodes": res.last_nodes, "info_lines": len(res.info_depths),
                })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="build/forge")
    ap.add_argument("--control", default="/tmp/ab/control/build/forge")
    ap.add_argument("--out")
    args = ap.parse_args()

    a = probe(args.base)
    b = probe(args.control)
    diffs = [(x, y) for x, y in zip(a, b) if x != y]
    print(f"requests: {len(a)}")
    print(f"differing: {len(diffs)}")
    for x, y in diffs[:10]:
        print(f"  {x['fen']} / {x['cmd']}\n    base    {x}\n    control {y}")
    if args.out:
        json.dump({"base": a, "control": b}, open(args.out, "w"), indent=1)
    if diffs:
        print("\nCONTROL IS NOT THE BASE ENGINE. Ablation deltas would be contaminated.")
        return 1
    print("\nCONTROL build is bit-identical to the base engine on all requests "
          "(bestmove, score, depth, node count).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
