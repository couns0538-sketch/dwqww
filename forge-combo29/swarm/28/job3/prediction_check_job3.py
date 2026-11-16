#!/usr/bin/env python3
"""prediction_check_job3.py — score job3/prediction.txt against the raw tsv files."""


def pct(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def load(d, mtg):
    wall = []
    with open(f"{d}/mtg{mtg}.tsv") as fh:
        next(fh)
        for line in fh:
            wall.append(float(line.rstrip("\n").split("\t")[1]))
    return wall


def main() -> int:
    import sys
    d = sys.argv[1]
    w = {m: load(d, m) for m in (1, 2, 40, 50, 51)}
    rows = [
        ("P1", "movestogo 1 median", round(pct(w[1], 50), 1), 600, 400, 820, "ms"),
        ("P2", "movestogo 1 largest", round(max(w[1]), 1), 800, 600, 1000, "ms"),
        ("P3", "movestogo 2 median", round(pct(w[2], 50), 1), 380, 250, 820, "ms"),
        ("P4", "movestogo 2 largest", round(max(w[2]), 1), 800, 500, 1000, "ms"),
        ("P5", "movestogo 40 median", round(pct(w[40], 50), 1), 27, 10, 100, "ms"),
        ("P6", "movestogo 40 largest", round(max(w[40]), 1), 97, 40, 1000, "ms"),
        ("P8", "movestogo 1 median fraction of clock", round(pct(w[1], 50) / 1000, 3), 0.60, 0.40, 0.82, "f"),
        ("P9", "any search over the 1000 ms clock", sum(1 for m in w for x in w[m] if x > 1000), 0, 0, 2, "n"),
    ]
    print("| id | measurement | predicted | measured | kill range | verdict |")
    print("|---|---|---|---|---|---|")
    for pid, name, got, pred, lo, hi, unit in rows:
        ok = lo <= float(got) <= hi
        print(f"| {pid} | {name} | {pred} {unit} | {got} {unit} | {lo}..{hi} | "
              f"{'SURVIVES' if ok else '**KILLED**'} |")
    p7 = pct(w[1], 50) > pct(w[2], 50) > pct(w[40], 50)
    print(f"| P7 | mtg1 > mtg2 > mtg40 median | true | {str(p7).lower()} | true | "
          f"{'SURVIVES' if p7 else '**KILLED**'} |")
    a, b = pct(w[50], 50), pct(w[51], 50)
    rel = abs(a - b) / max(a, b)
    p10 = rel <= 0.05
    print(f"| P10 | mtg50 vs mtg51 median differ <= 5 % | true | {a:.1f} vs {b:.1f} = {rel*100:.1f} % | "
          f"<=5 % | {'SURVIVES' if p10 else '**KILLED**'} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
