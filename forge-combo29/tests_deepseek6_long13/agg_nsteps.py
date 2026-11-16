#!/usr/bin/env python3
"""agg_nsteps.py -- aggregate NSTEPS v1 lines into kimi5's job-8 agg layout (exact format match).
Usage: agg_nsteps.py NSTEPS_CAPTURE_FILE"""
import sys

PRE = {"gate": 7, "rzt": 7, "rzr": 7, "rzn": 7, "rfp": 42, "nlt": 7, "nlr": 7, "nlv": 7,
       "nleb": 42, "nlnd": 21, "nlnr": 7, "nlnm": 7, "pce": 7, "pcc": 7, "pcr": 7, "pcn": 7}
REG = {"rz": 14, "rfp": 84, "nl": 14, "nleb": 84, "nlnd": 42, "pc": 14}
acc = {k: [0] * n for k, n in PRE.items()}
regacc = {k: [0] * n for k, n in REG.items()}
k4t_lines = k4c_lines = split_lines = 0
k4t_mine = k4t_engine = k4c_mine = k4c_engine = 0
seen = [0, 0, 0, 0]
ended1 = wide = pnodes = 0
lines = 0
for line in open(sys.argv[1]):
    line = line.strip()
    if not line.startswith("info string NSTEPS v1"):
        continue
    lines += 1
    toks = line[len("info string NSTEPS v1 "):].split()
    i = 0
    inreg = False
    cur = None
    got = 0
    while i < len(toks):
        t = toks[i]
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
            inreg = True; cur = None
            seen[0] += int(toks[i + 2]); seen[1] += int(toks[i + 3])
            seen[2] += int(toks[i + 4]); seen[3] += int(toks[i + 5])
            ended1 += int(toks[i + 7]); wide += int(toks[i + 9]); pnodes += int(toks[i + 11])
            i += 12; continue
        lengths = REG if inreg else PRE
        if t in lengths:
            cur = t; got = 0; i += 1; continue
        if cur is not None and got < lengths[cur] and t.lstrip("-").isdigit():
            (regacc if inreg else acc)[cur][got] += int(t)
            got += 1
            i += 1
            continue
        i += 1
print(f"lines_summed {lines}")
print(f"K4 lines with k4t viol: {k4t_lines}; k4c viol: {k4c_lines}; splitviol: {split_lines}")
print(f"k4t mine {k4t_mine} engine {k4t_engine}; k4c mine {k4c_mine} engine {k4c_engine}")
for k in ["gate", "rzt", "rzr", "rzn", "rfp", "nlt", "nlr", "nlv", "nleb", "nlnd", "nlnr", "nlnm", "pce", "pcc", "pcr", "pcn"]:
    print(k + " " + " ".join(str(x) for x in acc[k]))
print(f"splitviol {split_lines}")
gsum = sum(acc["gate"]); rt = sum(acc["rzt"]); rr = sum(acc["rzr"]); rf = sum(acc["rfp"])
nt = sum(acc["nlt"]); nr = sum(acc["nlr"]); nv = sum(acc["nlv"])
pe = sum(acc["pce"]); pc = sum(acc["pcc"]); pr = sum(acc["pcr"])
print(f"TOTALS gate {gsum} razor_try {rt} razor_ret {rr} rfp_ret {rf} null_try {nt} null_ret {nr} null_verif {nv} pc_entry {pe} pc_caps {pc} pc_ret {pr}")
print("rfp margin-class totals: " + " ".join(
    f"<{[1.25, 1.5, 2, 3][i]}={sum(acc['rfp'][d * 6 + i] for d in range(7))}" for i in range(4)) +
    " " + f">=3={sum(acc['rfp'][d * 6 + 4] for d in range(7))} m<=0={sum(acc['rfp'][d * 6 + 5] for d in range(7))}")
print("null eb-class totals: " + " ".join(
    f"<{[25,50,100,200,400][i]}={sum(acc['nleb'][d*6+i] for d in range(7))}" for i in range(5)) +
    f" >=400={sum(acc['nleb'][d*6+5] for d in range(7))}")
print("null nd-class totals: " + f"qsearch={sum(acc['nlnd'][d*3+0] for d in range(7))} 1-2={sum(acc['nlnd'][d*3+1] for d in range(7))} 3+={sum(acc['nlnd'][d*3+2] for d in range(7))}")
if seen != [0, 0, 0, 0] or pnodes:
    print("seen " + " ".join(map(str, seen)))
    print(f"ended1 {ended1}")
    print(f"wide {wide}")
    print(f"pnodes {pnodes}")
    print("rz " + " ".join(str(x) for x in regacc["rz"]))
    print("rfpg " + " ".join(str(x) for x in regacc["rfp"]))
    print("nl " + " ".join(str(x) for x in regacc["nl"]))
    print("nlebg " + " ".join(str(x) for x in regacc["nleb"]))
    print("nlndg " + " ".join(str(x) for x in regacc["nlnd"]))
    print("pcg " + " ".join(str(x) for x in regacc["pc"]))
