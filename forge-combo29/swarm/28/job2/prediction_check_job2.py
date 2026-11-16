#!/usr/bin/env python3
"""prediction_check_job2.py — score job2/prediction.txt against the raw tsv files."""
import os
import sys


def pct(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def load(d, w, i):
    wall, legal, ok = [], 0, 0
    with open(os.path.join(d, f"w{w}_i{i}.tsv")) as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            wall.append(float(p[1]))
            if p[5] == "True":
                legal += 1
            if p[4] == "ok":
                ok += 1
    return wall, legal, ok


def main() -> int:
    d = sys.argv[1]
    cells = {(w, i): load(d, w, i) for w in (100, 30, 10, 1, 0) for i in (0, 10)}
    rows = []

    def add(pid, name, got, pred, lo, hi, unit):
        rows.append((pid, name, pred, got, f"{lo}..{hi}", unit))

    add("P1", "wtime 10 winc 0 median", round(pct(cells[(10, 0)][0], 50), 2), 1.5, 0.5, 20, "ms")
    add("P2", "wtime 1 winc 0 median", round(pct(cells[(1, 0)][0], 50), 2), 1.5, 0.5, 20, "ms")
    add("P3", "wtime 0 winc 0 median", round(pct(cells[(0, 0)][0], 50), 2), 1.5, 0.5, 20, "ms")
    over10 = sum(1 for x in cells[(10, 0)][0] if x > 10)
    add("P4", "wtime 10 winc 0 over 10 ms", over10, 0, 0, 10, "n")
    add("P5", "wtime 30 winc 0 median", round(pct(cells[(30, 0)][0], 50), 2), 2.0, 0.5, 30, "ms")
    add("P6", "wtime 30 winc 0 largest", round(max(cells[(30, 0)][0]), 2), 20, 2, 200, "ms")
    add("P7", "wtime 100 winc 0 median", round(pct(cells[(100, 0)][0], 50), 2), 4.0, 1, 60, "ms")
    over100 = sum(1 for x in cells[(100, 0)][0] if x > 100)
    add("P8", "wtime 100 winc 0 over 100 ms", over100, 0, 0, 10, "n")
    add("P9", "wtime 100 winc 10 median", round(pct(cells[(100, 10)][0], 50), 2), 7.0, 1, 60, "ms")
    add("P10", "wtime 30 winc 10 median", round(pct(cells[(30, 10)][0], 50), 2), 3.5, 0.5, 40, "ms")
    tot = sum(len(v[0]) for v in cells.values())
    legal = sum(v[1] for v in cells.values())
    ok = sum(v[2] for v in cells.values())
    add("P11", "legal bestmove, all cells (%)", round(100.0 * legal / tot, 1), 100.0, 100.0, 100.0, "%")
    add("P12", "answered, all cells (%)", round(100.0 * ok / tot, 1), 100.0, 100.0, 100.0, "%")
    zero_ok = cells[(0, 0)][2]
    add("P13", "wtime 0 answered (yes=1)", 1 if zero_ok == len(cells[(0, 0)][0]) else 0, 1, 1, 1, "bool")

    print("| id | measurement | predicted | measured | kill range | verdict |")
    print("|---|---|---|---|---|---|")
    for pid, name, pred, got, rng, unit in rows:
        lo, hi = (float(x) for x in rng.split(".."))
        verdict = "SURVIVES" if lo <= float(got) <= hi else "**KILLED**"
        print(f"| {pid} | {name} | {pred} {unit} | {got} {unit} | {rng} | {verdict} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
