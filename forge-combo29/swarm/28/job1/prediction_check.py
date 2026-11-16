#!/usr/bin/env python3
"""prediction_check.py — score job1/prediction.txt against the measured raw files.

Ranges come from the prediction file; each is pasted here so the verdict is computed, not typed.
"""
import os
import sys


def pct(values, q):
    s = sorted(values)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def load(path, limit=None):
    walls = []
    with open(path) as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 6 and p[5] == "ok":
                walls.append(float(p[2]))
    return walls


def main() -> int:
    d = sys.argv[1]
    a = load(os.path.join(d, "outA/mt50.txt"))
    b = load(os.path.join(d, "outB/mt50.txt"))
    m5 = load(os.path.join(d, "outA/mt500.txt"))
    w1 = load(os.path.join(d, "outA/wt1000.txt"))
    w10 = load(os.path.join(d, "outA/wt10000.txt"))
    both50 = a + b
    rows = [
        ("P1", "movetime 50 run A median", pct(a, 50), 51.5, 45, 70, "ms"),
        ("P2", "movetime 50 run B median", pct(b, 50), 51.5, 45, 70, "ms"),
        ("P3", "A vs B median difference", abs(pct(a, 50) - pct(b, 50)), 0.4, 0, 3, "ms"),
        ("P4", "movetime 50 largest (both runs)", max(both50), 56, 50, 110, "ms"),
        ("P5", "movetime 50 over limit of 400", sum(1 for x in both50 if x > 50), 3, 0, 40, "n"),
        ("P6", "movetime 500 median", pct(m5, 50), 502, 460, 570, "ms"),
        ("P7", "movetime 500 largest", max(m5), 512, 500, 700, "ms"),
        ("P8", "movetime 500 over limit", sum(1 for x in m5 if x > 500), 0, 0, 20, "n"),
        ("P9", "wt1000 median", pct(w1, 50), 45, 25, 90, "ms"),
        ("P10", "wt1000 largest", max(w1), 55, 40, 150, "ms"),
        ("P11", "wt1000 over wtime/30+winc(43.3)", sum(1 for x in w1 if x > 43.3), 0, 0, 25, "n"),
        ("P12", "wt10000 median", pct(w10, 50), 350, 150, 600, "ms"),
        ("P13", "wt10000 largest", max(w10), 380, 250, 900, "ms"),
        ("P14", "wt10000 over 433.3", sum(1 for x in w10 if x > 433.3), 0, 0, 25, "n"),
    ]
    print("| id | measurement | predicted | measured | kill range | verdict |")
    print("|---|---|---|---|---|---|")
    for pid, name, got, pred, lo, hi, unit in rows:
        verdict = "SURVIVES" if lo <= got <= hi else "**KILLED**"
        gs = f"{got:.2f}" if isinstance(got, float) else str(got)
        print(f"| {pid} | {name} | {pred} {unit} | {gs} {unit} | {lo}..{hi} | {verdict} |")
    p15 = pct(a, 50) < pct(m5, 50) and pct(w1, 50) < pct(w10, 50)
    print(f"| P15 | median grows with budget | true | {str(p15).lower()} | true | "
          f"{'SURVIVES' if p15 else '**KILLED**'} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
