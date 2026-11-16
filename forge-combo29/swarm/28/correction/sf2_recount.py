#!/usr/bin/env python3
"""sf2_recount.py — S-F2 recounted against the ENGINE'S plan instead of my invented 43.3 ms.

S-F2 originally said 82 of 200 searches at `wtime 1000 winc 10` ran past `wtime/30 + winc` = 43.3 ms.
43.3 is MY reference, not the engine's: the engine's own plan is soft 52 ms, hard 260 ms
(include/forge/clock_plan.hpp with TmSoftDivisor 22, TmIncrementPercent 75, TmHardPercent 60).
This recounts the same raw file against all three thresholds so the reader can see which claim is
about the engine and which is about my yardstick.

Also the same for `wtime 10000 winc 100` (soft 529, hard 2645).
"""
import os
import statistics
import sys


def load(path):
    walls, eng = [], []
    with open(path) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            r = dict(zip(head, line.rstrip("\n").split("\t")))
            walls.append(float(r["wall_ms"]))
            if r.get("engine_time_ms"):
                eng.append(float(r["engine_time_ms"]))
    return walls, eng


def main() -> int:
    root = sys.argv[1]
    cases = [
        ("wtime 1000 winc 10 (job1/outA/wt1000.txt)", os.path.join(root, "job1/outA/wt1000.txt"),
         43.3, 52, 260),
        ("wtime 10000 winc 100 (job1/outA/wt10000.txt)", os.path.join(root, "job1/outA/wt10000.txt"),
         433.3, 529, 2645),
        ("wtime 100 winc 10 (job2/out/w100_i10.tsv)", os.path.join(root, "job2/out/w100_i10.tsv"),
         13.3, 11, 54),
    ]
    print("| case | n | median wall | over my wtime/30+winc | over engine SOFT | over engine HARD | "
          "median vs soft | median vs hard |")
    print("|---|---|---|---|---|---|---|---|")
    for label, path, mine, soft, hard in cases:
        if "job1" in path:
            walls, eng = [], []
            with open(path) as fh:
                next(fh)
                for line in fh:
                    p = line.rstrip("\n").split("\t")
                    if p[5] == "ok":
                        walls.append(float(p[2]))
        else:
            walls, eng = load(path)
        med = statistics.median(walls)
        print(f"| {label} | {len(walls)} | {med:.1f} | {sum(1 for w in walls if w > mine)} | "
              f"{sum(1 for w in walls if w > soft)} | {sum(1 for w in walls if w > hard)} | "
              f"{med/soft:.2f} | {med/hard:.2f} |")
    print()
    print("The 'over engine HARD' column is the only one that describes the engine breaking a bound it")
    print("set itself. 'over my wtime/30+winc' describes the engine ignoring a rule I invented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
