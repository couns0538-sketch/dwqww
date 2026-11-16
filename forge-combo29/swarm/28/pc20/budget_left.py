#!/usr/bin/env python3
"""budget_left.py — does the PC build stop with budget it could have used?

For each position, from the observed ladder, estimate what the NEXT iteration would have cost, using that
position's own last growth ratio (not a global median), and compare with the soft plan:

    projected_next_finish = last_iter_finish + last_iter_cost * that_position's last growth ratio

Then classify each search:
  FITS        : projected_next_finish <= soft plan  -> the engine stopped although the next iteration
                would have finished inside its own budget (unused budget)
  DOES_NOT_FIT: projected_next_finish > soft plan   -> stopping there is correct

A build with many FITS rows is leaving depth on the table. This is the difference between "spends less
time" (a policy choice) and "stops early although the budget allowed more" (a defect).

Usage: budget_left.py LABEL WTIME
"""
import statistics
import sys


def load(path):
    rows = []
    with open(path) as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) < 6:
                continue
            visited = p[1]
            seq = []
            for tok in visited.split():
                d, t = tok.split(":")
                seq.append((int(d), float(t)))
            rows.append(seq)
    return rows


def main() -> int:
    label, wtime = sys.argv[1], int(sys.argv[2])
    soft = max(1, (wtime - 10) // 22)
    rows = load(f"ladder_{label}_w{wtime}.tsv")
    fits, nofit, unknown = [], [], []
    for i, seq in enumerate(rows, 1):
        if len(seq) < 3:
            unknown.append(i)
            continue
        (d_last, t_last) = seq[-1]
        prev_t = seq[-2][1]
        prev_prev_t = seq[-3][1]
        last_cost = t_last - prev_t
        prev_cost = prev_t - prev_prev_t
        if prev_cost <= 0:
            unknown.append(i)
            continue
        growth = last_cost / prev_cost
        proj = t_last + last_cost * growth
        (fits if proj <= soft else nofit).append((i, d_last, t_last, last_cost, growth, proj))
    print(f"build {label}, wtime {wtime}, soft plan {soft} ms, {len(rows)} positions")
    print()
    print(f"| class | count | median last depth | median last-iteration finish | median projected next "
          f"finish |")
    print("|---|---|---|---|---|")
    for name, group in (("FITS (budget left unused)", fits),
                        ("DOES NOT FIT (correct stop)", nofit)):
        if not group:
            print(f"| {name} | 0 | - | - | - |")
            continue
        print(f"| {name} | {len(group)} | {statistics.median([g[1] for g in group]):.0f} | "
              f"{statistics.median([g[2] for g in group]):.0f} | "
              f"{statistics.median([g[5] for g in group]):.0f} |")
    if unknown:
        print(f"| not classifiable (ladder too short) | {len(unknown)} | - | - | - |")
    print()
    if fits:
        print("Positions where the next iteration would have fitted inside the soft plan:")
        print()
        print("| index | last depth | last iter finished | last iter cost | growth | projected next | "
              "soft |")
        print("|---|---|---|---|---|---|---|")
        for g in sorted(fits, key=lambda x: -x[5])[:12]:
            print(f"| {g[0]} | {g[1]} | {g[2]:.0f} | {g[3]:.0f} | {g[4]:.2f}x | {g[5]:.0f} | {soft} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
