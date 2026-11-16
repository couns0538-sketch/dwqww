#!/usr/bin/env python3
"""cfpsum.py -- sum a job-3b counters file and print how many lines it summed.

Usage: cfpsum.py COUNTERSFILE
Prints one line per lmr_depth L: "L <L> cand <n> in_depth <n> pruned <n>", then
"lines <N>" and the two arithmetic checks. One committed command, as job 3b asks.
"""
import re
import sys

PAIR = re.compile(r"\b([cdp])(\d+) (\d+)\b")
SMALL = re.compile(r"\bsmall (\d+)\b")
MISS = re.compile(r"\bmiss (\d+)\b")
BIN = re.compile(r"\bb(\d+)((?:\s+\d+)+)")


def main():
    if len(sys.argv) != 2:
        print("usage: cfpsum.py COUNTERSFILE", file=sys.stderr)
        return 64
    cand = [0] * 16
    ind = [0] * 16
    prn = [0] * 16
    bins = [[0] * 33 for _ in range(16)]
    small = miss = lines = 0
    with open(sys.argv[1], encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or "cfp" not in line:
                continue
            lines += 1
            for kind, idx, val in PAIR.findall(line):
                i, v = int(idx), int(val)
                if i > 15:
                    continue
                if kind == "c":
                    cand[i] += v
                elif kind == "d":
                    ind[i] += v
                else:
                    prn[i] += v
            m = SMALL.search(line)
            if m:
                small += int(m.group(1))
            m = MISS.search(line)
            if m:
                miss += int(m.group(1))
            for idx, vals in BIN.findall(line):
                i = int(idx)
                if i > 15:
                    continue
                for k, v in enumerate(vals.split()):
                    if k < 33:
                        bins[i][k] += int(v)
    for i in range(16):
        print("L %2d cand %9d in_depth %9d pruned %9d" % (i, cand[i], ind[i], prn[i]))
    print("lines %d" % lines)
    print("pruned total %d" % sum(prn))
    print("pruned with too small a deficit %d" % small)
    print("not pruned though the gate says yes %d" % miss)
    tot = sum(prn)
    if tot:
        share = sum(prn[0:3]) * 100.0 / tot
        print("share of prunes at L <= 2: %.1f %%" % share)
    largest = max([i for i in range(16) if prn[i] > 0], default=-1)
    print("largest L with pruned > 0: %d" % largest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
