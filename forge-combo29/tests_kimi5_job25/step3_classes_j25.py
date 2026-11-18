#!/usr/bin/env python3
"""kimi5 job 25 step 3 classes: per-class counts under base and each setting, and the
change, for O and G. Reads the A25C lines of rows_count (same sums as step3_sum_j25.py,
which printed how many it summed)."""
import glob

SLOT = ["tests", "ext1", "ext2", "mcut", "extm2", "extm1", "none",
        "ttLow", "ttUpp", "ttExa", "rfpRet", "rfRet", "rfNoPv", "rfTtGd", "rfCorr", "rfToday"]

def sums(tag, st):
    path = f"rows_count/{tag}_{st}_d12_full.txt"
    tot = [0] * 16
    n = 0
    with open(path) as f:
        for line in f:
            if line.startswith("A25C"):
                p = line.split()
                for i in range(16):
                    tot[i] += int(p[1 + i])
                n += 1
    return n, tot

CLASSES = [("tests", 0), ("ext1+2", None), ("ext1", 1), ("ext2", 2), ("mcut", 3),
           ("ext-2", 4), ("ext-1", 5), ("none", 6), ("ttLow", 7), ("ttUpp", 8),
           ("ttExa", 9), ("rfpRet", 10)]

for st in ("G", "O"):
    nbase, base = sums("base", st)
    print(f"== set {st} (base searches {nbase}) ==")
    print(f"{'class':7s} " + " ".join(f"{t:>10s}" for t in ("base", "fhb1", "fhb2", "fhb4", "fhb7")))
    data = {"base": base}
    for t in ("fhb1", "fhb2", "fhb4", "fhb7"):
        data[t] = sums(t, st)[1]
    for name, idx in CLASSES:
        row = []
        for t in ("base", "fhb1", "fhb2", "fhb4", "fhb7"):
            v = data[t][1] + data[t][2] if idx is None else data[t][idx]
            row.append(v)
        line = f"{name:7s} " + " ".join(f"{v:>10d}" for v in row)
        print(line)
        chg = " ".join(f"{(row[i+1]-row[0])/row[0]*100:+8.1f}%" for i in range(4))
        print(f"{'chg%':7s} " + chg)
    n_r, rfp = sums("rfp3", st)
    print(f"rfp3 ({n_r} searches): today={rfp[15]} returned={rfp[11]} ({rfp[11]/rfp[15]*100:.1f}%) "
          f"noPv={rfp[12]} ({rfp[12]/rfp[15]*100:.2f}%) ttGuard={rfp[13]} ({rfp[13]/rfp[15]*100:.2f}%) "
          f"corr={rfp[14]} ({rfp[14]/rfp[15]*100:.2f}%)")
    print()
