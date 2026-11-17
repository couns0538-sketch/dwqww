#!/usr/bin/env python3
"""Verify the four combo29 honesty pins on THIS build before any measurement.

312,866 / 862,329 / 3,024,920 (bench net-on depths 11/13/16) and perft 5 4,865,609.

Uses the persistent-engine driver, not a printf pipe: findings §7 item 1 says a
pipe that closes stdin aborts the search and fabricates a bestmove with zero
info lines, so a pin read from a pipe would be a pin on nothing.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucipipe import Engine  # noqa: E402

WANT = {
    ("UseNNUE", "true", 11): 312_866,
    ("UseNNUE", "true", 13): 862_329,
    ("UseNNUE", "true", 16): 3_024_920,
}
WANT_PERFT5 = 4_865_609


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("exe", nargs="?", default="build/forge")
    ap.add_argument("--threads", default="1")
    args = ap.parse_args()

    fails = []
    with Engine(args.exe, {"Threads": args.threads}) as eng:
        for use_nnue in ("true", "false"):
            eng.send(f"setoption name UseNNUE value {use_nnue}")
            eng.sync()
            for depth in (11, 13, 16):
                eng.newgame()
                eng.send(f"bench {depth}")
                lines = eng.expect("info string bench depth", timeout=600)
                bench = lines[-1]
                tok = bench.split()
                nodes = int(tok[tok.index("nodes") + 1])
                want = WANT.get(("UseNNUE", use_nnue, depth))
                verdict = "MATCH" if want is None or nodes == want else "MISMATCH"
                print(f"UseNNUE={use_nnue:5s} bench {depth:2d}: nodes {nodes:>9,d}  "
                      f"want {('-' if want is None else format(want, ',')):>10s}  {verdict}")
                if want is not None and nodes != want:
                    fails.append((use_nnue, depth, nodes, want))

        eng.send("position startpos")
        eng.send("go perft 5")
        lines = eng.expect("nodes", timeout=900)
        perft = int(lines[-1].split()[1])
        ok = perft == WANT_PERFT5
        print(f"perft 5 startpos: {perft:,}  want {WANT_PERFT5:,}  "
              f"{'MATCH' if ok else 'MISMATCH'}")
        if not ok:
            fails.append(("perft5", 5, perft, WANT_PERFT5))

    if fails:
        print(f"\nPIN MISMATCH on this build: {fails}")
        return 1
    print("\nALL FOUR HONESTY PINS MATCH on this build (312,866 / 862,329 / 3,024,920 / perft5 4,865,609)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
