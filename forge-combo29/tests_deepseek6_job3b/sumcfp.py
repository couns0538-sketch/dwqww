#!/usr/bin/env python3
"""sumcfp.py -- sum the per-go cfp lines of one run and print the totals.

Usage: sumcfp.py CFPFILE [CFPFILE...]
Prints, per file: rows summed, cand[0..15], ind[0..15], prn[0..15], over, gy, gn, bp,
and the deficit table per L (bins 0..31). Refuses a file with MISSING lines."""
import sys

def parse(path):
    n = 0
    cand = [0]*16; ind = [0]*16; prn = [0]*16
    over = gy = gn = bp = 0
    deficit = [[0]*32 for _ in range(16)]
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        if line == "MISSING":
            print(f"{path}: MISSING cfp line at row {n}")
            raise SystemExit(3)
        if not line.startswith("cfp "):
            print(f"{path}: unexpected line: {line[:60]}")
            raise SystemExit(3)
        n += 1
        for part in line[4:].split(" "):
            k, _, v = part.partition("=")
            if k == "cand":
                vals = [int(x) for x in v.split(",")]
                cand = [a + b for a, b in zip(cand, vals)]
            elif k == "ind":
                vals = [int(x) for x in v.split(",")]
                ind = [a + b for a, b in zip(ind, vals)]
            elif k == "prn":
                vals = [int(x) for x in v.split(",")]
                prn = [a + b for a, b in zip(prn, vals)]
            elif k == "over":
                over += int(v)
            elif k == "gy":
                gy += int(v)
            elif k == "gn":
                gn += int(v)
            elif k == "bp":
                bp += int(v)
            elif k.startswith("d") and k[1:].isdigit():
                L = int(k[1:])
                if not (0 <= L < 16):
                    raise SystemExit(f"bad L {L}")
                for b, x in enumerate(v.split(",")):
                    deficit[L][b] += int(x)
            else:
                raise SystemExit(f"unknown cfp key {k!r} in {path}")
    return n, cand, ind, prn, over, gy, gn, bp, deficit

for path in sys.argv[1:]:
    n, cand, ind, prn, over, gy, gn, bp, deficit = parse(path)
    print(f"== {path}: rows {n}")
    print("cand  " + " ".join(f"L{i}={cand[i]}" for i in range(16) if cand[i] or prn[i] or ind[i]))
    print("ind   " + " ".join(f"L{i}={ind[i]}" for i in range(16) if ind[i]))
    print("prn   " + " ".join(f"L{i}={prn[i]}" for i in range(16) if prn[i]) + ("" if any(prn) else " (all 0)"))
    print(f"over {over} gy {gy} gn {gn} bp {bp}")
    tot = sum(sum(r) for r in deficit)
    print(f"deficit total {tot}; per L: " + " ".join(
        f"L{i}={sum(deficit[i])}" for i in range(16) if sum(deficit[i])))
    for i in range(16):
        if sum(deficit[i]):
            print(f"  L{i} bins: " + " ".join(f"b{b}={deficit[i][b]}" for b in range(32) if deficit[i][b]))
