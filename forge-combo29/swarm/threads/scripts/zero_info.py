#!/usr/bin/env python3
"""How often does a correctly-driven threaded search return ZERO info lines?

Why this matters beyond its own size: the audit's only reliable detector for a broken
piped harness is "an `info depth` line count of zero" (findings trap 3a, 60 of 60).
If a correctly-driven Threads>1 search can also produce zero info lines, then that
detector has a false-positive class, and a harness that filters on it will throw away
real threaded results -- or, worse, accept a piped run because one position happened
to emit a line.

This script drives the engine interactively (never pipes, always reads to `bestmove`)
so the zero cannot be an EOF abort (trap 1/3a). It reports, per thread count and
budget, the count of searches with zero `info depth` lines, and -- for the same
fixture -- a Threads 1 control that must be 0.

Usage: python3 zero_info.py <exe> <fens> <out.json> [reps]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine  # noqa: E402

THREADS = (1, 2, 4, 8)
BUDGETS = (1000, 5000, 10000, 50000)


def main():
    exe = os.path.abspath(sys.argv[1])
    fens = [l.strip() for l in open(sys.argv[2]) if l.strip()]
    out_path = sys.argv[3]
    reps = int(sys.argv[4]) if len(sys.argv) > 4 else 3
    rows = []
    for th in THREADS:
        e = Engine(exe, {"Hash": 64, "Threads": th}, timeout=600.0)
        for budget in BUDGETS:
            total = zero = 0
            examples = []
            for fen in fens:
                for _ in range(reps):
                    e.ucinewgame()
                    e.position(fen)
                    info, best, wall = e.go(f"nodes {budget}", timeout=600.0)
                    total += 1
                    if not [l for l in info if l.startswith("info depth")]:
                        zero += 1
                        if len(examples) < 3:
                            examples.append({"fen": fen, "bestmove": best, "wall": round(wall, 4)})
            rows.append({"threads": th, "budget": budget, "searches": total,
                         "zero_info": zero, "examples": examples})
            print(f"T{th:<2} N={budget:<7} zero-info {zero}/{total}"
                  + (f"   e.g. {examples[0]['bestmove']} on {examples[0]['fen'][:30]}" if examples else ""),
                  flush=True)
        e.close()
        print(flush=True)
    with open(out_path, "w") as fh:
        json.dump({"rows": rows, "reps": reps, "exe": exe,
                   "exe_sha256": os.popen(f"sha256sum {exe}").read().split()[0]}, fh, indent=2)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
