#!/usr/bin/env python3
"""plant_verdict.py — did the harness CATCH each planted fault? (Opus Rule 1)

Compares the harness's own columns between the real run and the two plants:
  illegal : the zero is "400/400 legal". The plant answers `bestmove a1a8` to every go, so the
            `bestmove_legal` column must show False. CAUGHT iff at least one False appears.
  overrun : the zero is "0 over wtime". The plant sleeps 300 ms under a 100 ms clock, so `wall_ms`
            must exceed 100 on the w100 rows. CAUGHT iff at least one such row exists.
The harness code (lowtime.py) is byte-identical for real and plant; only the exe path differs.
"""
import glob
import os
import sys


def load(path):
    rows = []
    with open(path) as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            rows.append(p)
    return rows


def main() -> int:
    root = sys.argv[1]
    real = os.path.join(root, "out")
    print("| plant | what the harness measured | count | the zero it must break | caught |")
    print("|---|---|---|---|---|")

    # illegal plant
    ill = os.path.join(root, "out_plant", "illegal")
    files = sorted(glob.glob(os.path.join(ill, "w*.tsv")))
    bad = tot = 0
    for path in files:
        for row in load(path):
            tot += 1
            if row[5] == "False":
                bad += 1
    print(f"| illegal bestmove (fake answers a1a8) | bestmove_legal == False | {bad}/{tot} | "
          f"400/400 legal | {'YES' if bad else 'NO'} |")

    # overrun plant
    over = os.path.join(root, "out_plant", "overrun")
    rows_over = tot_over = 0
    for path in sorted(glob.glob(os.path.join(over, "w*.tsv"))):
        wtime = int(os.path.basename(path).split("_")[0][1:])
        for row in load(path):
            tot_over += 1
            if float(row[1]) > max(wtime, 1):
                rows_over += 1
    print(f"| time overrun (fake sleeps 300 ms) | wall_ms > wtime | {rows_over}/{tot_over} | "
          f"0 over wtime | {'YES' if rows_over else 'NO'} |")

    # the real run, same columns, for comparison
    realrows = tot_real = realbad = realover = 0
    for path in sorted(glob.glob(os.path.join(real, "w*.tsv"))):
        wtime = int(os.path.basename(path).split("_")[0][1:])
        for row in load(path):
            tot_real += 1
            if row[5] == "False":
                realbad += 1
            if float(row[1]) > max(wtime, 1):
                realover += 1
    print(f"| REAL engine, same harness | bestmove_legal False | {realbad}/{tot_real} | - | - |")
    print(f"| REAL engine, same harness | wall_ms > wtime | {realover}/{tot_real} | - | - |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
