#!/usr/bin/env python3
"""agg_nsteps.py -- aggregate NSTEPS v1 lines into kimi5's job-8 agg layout (exact format match).
Usage: agg_nsteps.py NSTEPS_CAPTURE_FILE"""
import sys

ARRS = {"gate": 7, "rzt": 7, "rzr": 7, "rzn": 7, "rfp": 42, "nlt": 7, "nlr": 7, "nlv": 7,
        "nleb": 42, "nlnd": 21, "nlnr": 7, "nlnm": 7, "pce": 7, "pcc": 7, "pcr": 7, "pcn": 7,
        "rz": 14, "rfpg": 84, "nl": 14, "nlebg": 84, "nlndg": 42, "pcg": 14}
PROBE_LABELS = {"seen", "ended1", "wide", "pnodes", "rz", "rfpg", "nl", "nlebg", "nlndg", "pcg"}
acc = {k: [0] * n for k, n in ARRS.items()}
k4t_lines = k4c_lines = split_lines = 0
k4t_mine = k4t_engine = k4c_mine = k4c_engine = 0
seen = None
ended1 = wide = pnodes = 0
lines = 0
for line in open(sys.argv[1]):
    line = line.strip()
    if not line.startswith("info string NSTEPS v1"):
        continue
    lines += 1
    toks = line[len("info string NSTEPS v1 "):].split()
    i = 0
    cur = None
    got = 0
    while i < len(toks):
        t = toks[i]
        if t in ARRS:
            cur = t; got = 0; i += 1; continue
        if t == "k4t":
            k4t_mine += int(toks[i + 1]); k4t_engine += int(toks[i + 2])
            if toks[i + 3] != "0": k4t_lines += 1
            i += 4; continue
        if t == "k4c":
            k4c_mine += int(toks[i + 1]); k4c_engine += int(toks[i + 2])
            if toks[i + 3] != "0": k4c_lines += 1
            i += 4; continue
        if t == "splitviol":
            if toks[i + 1] != "0": split_lines += 1
            i += 2; continue
        if t == "reg":
            # reg seen s1 s2 s3 s4 ended1 E wide W pnodes P rz ...
            seen = [int(x) for x in toks[i + 2:i + 6]]
            ended1 = int(toks[i + 7]); wide = int(toks[i + 9]); pnodes = int(toks[i + 11])
            i += 12; continue
        if cur is not None and got < ARRS[cur] and t.lstrip("-").isdigit():
            acc[cur][got] += int(t)
            got += 1
            i += 1
            continue
        i += 1
print(f"lines_summed {lines}")
print(f"K4 lines with k4t viol: {k4t_lines}; k4c viol: {k4c_lines}; splitviol: {split_lines}")
print(f"k4t mine {k4t_mine} engine {k4t_engine}; k4c mine {k4c_mine} engine {k4c_engine}")
for k in ["gate", "rzt", "rzr", "rzn", "rfp", "nlt", "nlr", "nlv", "nleb", "nlnd", "nlnr", "nlnm", "pce", "pcc", "pcr", "pcn"]:
    print(k + " " + " ".join(str(x) for x in acc[k]))
print("splitviol 0" if split_lines == 0 else f"splitviol {split_lines}")
if seen is not None:
    print("seen " + " ".join(map(str, seen)))
    print(f"ended1 {ended1}")
    print(f"wide {wide}")
    print(f"pnodes {pnodes}")
    for k in ["rz", "rfpg", "nl", "nlebg", "nlndg", "pcg"]:
        print(k + " " + " ".join(str(x) for x in acc[k]))
