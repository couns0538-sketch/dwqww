#!/usr/bin/env python3
"""lowtime_table.py OUTDIR [OUTDIR2] — the job 2 table, computed from the .tsv files only."""
import glob
import os
import sys


def pct(v, q):
    if not v:
        return float("nan")
    s = sorted(v)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main() -> int:
    dirs = sys.argv[1:]
    rows = []
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, "w*_i*.tsv"))):
            name = os.path.basename(path)[:-4]
            wtime = int(name.split("_")[0][1:])
            winc = int(name.split("_")[1][1:])
            wall, eng_t, legal, stat = [], [], 0, 0
            with open(path) as fh:
                next(fh)
                for line in fh:
                    p = line.rstrip("\n").split("\t")
                    wall.append(float(p[1]))
                    eng_t.append(float(p[2]) if p[2] else 0.0)
                    if p[5] == "True":
                        legal += 1
                    if p[4] == "ok":
                        stat += 1
            rows.append(dict(dir=d, name=name, wtime=wtime, winc=winc, n=len(wall),
                             med=pct(wall, 50), p99=pct(wall, 99), mx=max(wall),
                             over=sum(1 for w in wall if w > wtime),
                             eng_over=sum(1 for t in eng_t if t > wtime),
                             legal=legal, ok=stat))
    print("| run | wtime | winc | n | median ms | p99 ms | largest ms | over wtime | engine time > wtime | "
          "legal bestmove | answered |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['name']} | {r['wtime']} | {r['winc']} | {r['n']} | {r['med']:.2f} | {r['p99']:.2f} | "
              f"{r['mx']:.2f} | {r['over']} | {r['eng_over']} | {r['legal']}/{r['n']} | {r['ok']}/{r['n']} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
