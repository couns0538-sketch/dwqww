#!/usr/bin/env python3
"""table1.py — build the job1 main table from the raw .txt files (never typed by hand)."""
import glob
import os
import sys


def pct(values, q):
    s = sorted(values)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def load(path):
    walls = []
    with open(path) as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 6 and p[5] == "ok":
                walls.append(float(p[2]))
    return walls


def main() -> int:
    root = sys.argv[1]
    spec = [("A1_mt50", "outA/mt50.txt", 50.0),
            ("B1_mt50", "outB/mt50.txt", 50.0),
            ("A_mt500", "outA/mt500.txt", 500.0),
            ("A_wt1000", "outA/wt1000.txt", 43.3),
            ("A_wt10000", "outA/wt10000.txt", 433.3)]
    print("| run | n | median | p99 | largest | limit ms | over limit |")
    print("|---|---|---|---|---|---|---|")
    store = {}
    for name, rel, limit in spec:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            print(f"| {name} | MISSING {rel} | | | | | |")
            continue
        w = load(path)
        store[name] = w
        over = sum(1 for x in w if x > limit)
        print(f"| {name} | {len(w)} | {pct(w,50):.1f} | {pct(w,99):.1f} | {max(w):.1f} | "
              f"{limit:.1f} | {over} |")
    if "A1_mt50" in store and "B1_mt50" in store:
        a, b = store["A1_mt50"], store["B1_mt50"]
        print()
        print(f"two movetime-50 runs: median A {pct(a,50):.2f}, median B {pct(b,50):.2f}, "
              f"difference {abs(pct(a,50)-pct(b,50)):.2f} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
