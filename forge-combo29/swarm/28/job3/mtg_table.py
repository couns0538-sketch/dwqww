#!/usr/bin/env python3
"""mtg_table.py OUTDIR — the job 3 table from the .tsv files, plus the planned limits."""
import glob
import os
import sys

CLOCK = 1000
OVERHEAD = 10


def planned(mtg):
    avail = CLOCK - OVERHEAD
    m = min(mtg, 50)
    soft = avail // (m + 1)
    hard = min(avail * 4 // 5, soft * 4)
    return soft, hard


def pct(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main() -> int:
    d = sys.argv[1]
    print("| movestogo | planned soft ms | planned hard ms | n | median ms | p99 ms | largest ms | "
          "median fraction of the 1000 ms clock | over clock |")
    print("|---|---|---|---|---|---|---|---|---|")
    for path in sorted(glob.glob(os.path.join(d, "mtg*.tsv")),
                       key=lambda p: int(os.path.basename(p)[3:-4])):
        mtg = int(os.path.basename(path)[3:-4])
        wall = []
        with open(path) as fh:
            next(fh)
            for line in fh:
                p = line.rstrip("\n").split("\t")
                wall.append(float(p[1]))
        soft, hard = planned(mtg)
        print(f"| {mtg} | {soft} | {hard} | {len(wall)} | {pct(wall,50):.1f} | {pct(wall,99):.1f} | "
              f"{max(wall):.1f} | {pct(wall,50)/CLOCK:.3f} | {sum(1 for w in wall if w > CLOCK)} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
