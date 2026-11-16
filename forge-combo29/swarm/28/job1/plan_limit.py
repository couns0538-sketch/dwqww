#!/usr/bin/env python3
"""plan_limit.py — compare measured wall times against the ENGINE'S OWN planned limits.

The limits are recomputed here from the source at 6b98f217, not measured:
  include/forge/clock_plan.hpp  plan_clock_budget(time, inc, mtg, overhead, soft_divisor,
                                                 inc_percent, hard_percent, hard_soft_multiple)
  defaults src/search.cpp: TmSoftDivisor 22, TmIncrementPercent 75, TmHardPercent 60, TmHardSoftMultiple 5
  Move Overhead default 10 (src/uci.cpp:152), applied as `movetime - overhead` for movetime
  (src/search.cpp:2192) and inside plan_clock_budget for clock searches.
A wall time above hard_ms is an overrun the engine itself promised not to make.
"""
import os
import sys

SOFT_DIV = 22
INC_PCT = 75
HARD_PCT = 60
HARD_MULT = 5
OVERHEAD = 10


def plan(time_ms, inc_ms, mtg=0):
    time = max(time_ms, 0)
    inc = max(inc_ms, 0)
    if time <= OVERHEAD:
        return 0, 0, True
    avail = time - OVERHEAD
    soft = avail // SOFT_DIV + inc * INC_PCT // 100
    hard = min(avail * HARD_PCT // 100, soft * HARD_MULT)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard, False


CONFIGS = {
    "mt50": lambda: (max(1, 50 - OVERHEAD), max(1, 50 - OVERHEAD)),
    "mt500": lambda: (max(1, 500 - OVERHEAD), max(1, 500 - OVERHEAD)),
    "wt1000": lambda: plan(1000, 10)[:2],
    "wt10000": lambda: plan(10000, 100)[:2],
}


def main() -> int:
    outdir = sys.argv[1]
    files = sys.argv[2:]
    print("| config | soft ms | hard ms | n | median | max | over soft | over HARD |")
    print("|---|---|---|---|---|---|---|---|")
    for name in files:
        path = os.path.join(outdir, name + ".txt")
        walls = []
        with open(path) as fh:
            next(fh)
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if len(p) >= 6 and p[5] == "ok":
                    walls.append(float(p[2]))
        soft, hard = CONFIGS[name]()
        walls.sort()
        over_soft = sum(1 for w in walls if w > soft + 1.0)
        over_hard = sum(1 for w in walls if w > hard + 1.0)
        print(f"| {name} | {soft} | {hard} | {len(walls)} | {walls[len(walls)//2]:.1f} | "
              f"{walls[-1]:.1f} | {over_soft} | {over_hard} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
