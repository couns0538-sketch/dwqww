#!/usr/bin/env python3
"""kimi5 job 34 known answers A and B.
A: the logging copy's rows (depth, nodes, bestmove, hp27, hp27_nodes) equal job 33's
   s3_all1024_soft.jsonl on 1,200 of 1,200, and its HP33 sums equal job 33's.
B: counted from the F LOG LINES of <tag>.fp.log (this script prints how many lines it read):
   fired 11633; pivW 10444; pivW+staleW 6991; pivM 5063; pivM+staleM 3408; none 458.
Usage: compare_ka_j34.py <j33.jsonl> <j34.jsonl> <fp.log>
"""
import json
import sys

J33, J34, FP = sys.argv[1], sys.argv[2], sys.argv[3]

rows33 = [json.loads(l) for l in open(J33)]
rows34 = [json.loads(l) for l in open(J34)]
print(f"A: job33 rows {len(rows33)}, job34 rows {len(rows34)}")
n_eq = 0
first_diffs = []
for a, b in zip(rows33, rows34):
    same = all(a[k] == b[k] for k in ("depth", "nodes", "bestmove", "hp27", "hp27_nodes")) and a["hp33"] == b["hp33"]
    if same:
        n_eq += 1
    elif len(first_diffs) < 5:
        first_diffs.append((a["index"], {k: (a[k], b[k]) for k in ("depth", "nodes", "bestmove", "hp27", "hp27_nodes") if a[k] != b[k]}))
print(f"A: rows equal on {n_eq} of {len(rows34)}")
for d in first_diffs:
    print("A: first differ:", d)
sums33 = [sum(r["hp33"][i] for r in rows33) for i in range(19)]
sums34 = [sum(r["hp33"][i] for r in rows34) for i in range(19)]
names = "eligible fired pivM pivW pivC none mNeg wNeg cNeg sumM sumW sumC firedStaleM firedStaleW pivWstaleW pivMstaleM eligStaleNzW eligStaleNzM mismatch".split()
exp = {"eligible": 2401588, "fired": 11633, "pivM": 5063, "pivW": 10444, "pivC": 3363, "none": 458,
       "pivWstaleW": 6991, "pivMstaleM": 3408}
ok = True
for i, n in enumerate(names):
    mark = ""
    if n in exp:
        mark = f" (pin {exp[n]}: {'OK' if sums34[i] == exp[n] else 'FAIL'})"
        ok &= sums34[i] == exp[n]
    if sums33[i] != sums34[i] or mark.endswith("FAIL"):
        ok = False
    print(f"A: HP33 {n:14s} j33={sums33[i]:>12} j34={sums34[i]:>12}{mark}")
print("A:", "PASS" if ok and n_eq == len(rows34) else "FAIL")

n_lines = 0
fired = pivw = pivw_stale = pivm = pivm_stale = none = 0
for line in open(FP):
    if " info string F " not in line:
        continue
    n_lines += 1
    fired += 1
    p = line.split(" p=")[1].split()[0]
    s = line.split(" s=")[1].split()[0]
    pm, pw, pc = p[0] == "1", p[1] == "1", p[2] == "1"
    sm, sw = s[0] == "1", s[1] == "1"
    if pw:
        pivw += 1
        if sw:
            pivw_stale += 1
    if pm:
        pivm += 1
        if sm:
            pivm_stale += 1
    if not (pm or pw or pc):
        none += 1
print(f"B: F lines read {n_lines}: fired {fired} (pin 11633), pivW {pivw} (10444), "
      f"pivW+staleW {pivw_stale} (6991), pivM {pivm} (5063), pivM+staleM {pivm_stale} (3408), none {none} (458)")
bp = (fired == 11633 and pivw == 10444 and pivw_stale == 6991 and pivm == 5063 and pivm_stale == 3408 and none == 458)
print("B:", "PASS" if bp else "FAIL")
