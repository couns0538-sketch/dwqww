#!/usr/bin/env python3
"""kimi5 job 21 Step 3 totals: parse every 'LMRD v1' line in the given _full.txt
files, print per-run totals and how many searches (lines) were summed.
Classes per line: quiet Q caps C then tm2/tm1/t0/tp1/tp2 each m,a,r,f,s
(moves, reduced score above alpha, re-searches run, re-searches failing alpha,
same reduced depth despite t != 0)."""
import glob
import sys

names = ["tm2", "tm1", "t0", "tp1", "tp2"]

def parse_file(path):
    tot = {"quiet": 0, "caps": 0, "n": 0,
           **{f"{n}_{k}": 0 for n in names for k in ("m", "a", "r", "f", "s")}}
    with open(path) as fh:
        for line in fh:
            if "LMRD v1" not in line:
                continue
            p = line.split()
            i = p.index("quiet")
            tot["quiet"] += int(p[i + 1])
            tot["caps"] += int(p[i + 3])
            j = i + 4
            for n in names:
                assert p[j] == n, (path, line)
                m, a, r, f, s = (int(x) for x in p[j + 1].split(","))
                tot[f"{n}_m"] += m
                tot[f"{n}_a"] += a
                tot[f"{n}_r"] += r
                tot[f"{n}_f"] += f
                tot[f"{n}_s"] += s
                j += 2
            tot["n"] += 1
    return tot

for path in sorted(sys.argv[1:]):
    t = parse_file(path)
    print(f"{path}: searches summed = {t['n']}")
    print(f"  quiet in block {t['quiet']}   eligible captures {t['caps']}")
    for n in names:
        m, a, r, f, s = (t[f"{n}_{k}"] for k in ("m", "a", "r", "f", "s"))
        rate = (1000.0 * a / m) if m else 0.0
        print(f"  {n}: moves {m}  above {a} ({rate:.1f}/1000)  research {r}  refail {f}  same_depth {s}")
    nz = sum(t[f"{n}_m"] for n in ("tm2", "tm1", "tp1", "tp2"))
    print(f"  moves with t != 0: {nz} (share of eligible {nz / t['caps']:.4f})" if t["caps"] else "  caps 0")
