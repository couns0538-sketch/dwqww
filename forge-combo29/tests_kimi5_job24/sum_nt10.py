#!/usr/bin/env python3
"""kimi5 job 24 Step 3 summer: totals over ALL NT10C lines of the counting runs.
Prints how many searches it summed per run. Also checks the counting build's rows
against Step 1's rows (first known answer) and the structural known answers:
nc -> null tries with cut_node false are 0; t5 -> no refused cutoff at depth 6+,
no stored score between alpha and beta; base -> classes add up to totals.
Usage: sum_nt10.py <rows_count_dir> <rows_dir>"""
import json
import sys

RC, ROWS = sys.argv[1], sys.argv[2]

SLOTS = [
    "null tries cut=T", "null tries cut=F", "null >=beta cut=T", "null >=beta cut=F",
    "null returned cut=T", "null returned cut=F",
    "tt d1-5 ge agree", "tt d1-5 ge disagree", "tt d1-5 le agree", "tt d1-5 le disagree",
    "tt d6+ ge agree", "tt d6+ ge disagree", "tt d6+ le agree", "tt d6+ le disagree",
    "tt d1-5 between", "tt d6+ between",
    "refused ge d1", "refused ge d2", "refused ge d3", "refused ge d4", "refused ge d5",
    "refused le d1", "refused le d2", "refused le d3", "refused le d4", "refused le d5",
    "confirmed ge d1", "confirmed ge d2", "confirmed ge d3", "confirmed ge d4", "confirmed ge d5",
    "confirmed le d1", "confirmed le d2", "confirmed le d3", "confirmed le d4", "confirmed le d5",
    "refused between", "confirmed between", "refused depth outside 1..5",
]

def nt10_lines(tag):
    path = f"{RC}/cnt{tag}_d12_full.txt"
    lines = []
    with open(path) as f:
        for line in f:
            if line.startswith("NT10C "):
                lines.append([int(x) for x in line.split()[1:]])
    return lines

def nodes(tag, src):
    with open(f"{src}/{'cnt' if src == RC else ''}{tag}_d12.json".replace("cntcnt", "cnt")) as f:
        return json.load(f)["per_position"]

ok = True
print("== known answer 1: counting build counts the same nodes as Step 1 ==")
for tag in ("base_O", "base_G", "nc_O", "t5_O", "t5_G"):
    c = nodes(tag, RC)
    p = nodes(tag, ROWS)
    same = c == p
    ok &= same
    print(f"{'OK ' if same else 'DIFF'} cnt{tag}: {sum(c)} vs step1 {sum(p)} ({'equal on all ' + str(len(c)) if same else 'MISMATCH'})")

print("\n== NT10C totals (n searches printed per run) ==")
totals = {}
for tag in ("base_O", "base_G", "nc_O", "t5_O", "t5_G"):
    lines = nt10_lines(tag)
    for ln in lines:
        assert len(ln) == 40, f"bad NT10C width in {tag}: {len(ln)}"
    t = [sum(col) for col in zip(*lines)]
    totals[tag] = t
    print(f"cnt{tag}: summed {len(lines)} searches")
    print("   " + " ".join(f"{v}" for v in t))

print("\n== structural known answers ==")
nc_t = totals["nc_O"]
bad = [i for i, ln in enumerate(nt10_lines("nc_O")) if ln[1] != 0 or ln[3] != 0 or ln[5] != 0]
print(f"{'OK ' if not bad else 'FAIL'} nc O: null tries/ge_beta/returned with cut_node false are 0 in every search "
      f"(totals {nc_t[1]}/{nc_t[3]}/{nc_t[5]}; bad searches {len(bad)})")
ok &= not bad
for tag in ("t5_O", "t5_G"):
    t = totals[tag]
    print(f"{'OK ' if t[38] == 0 else 'FAIL'} {tag}: refused at depth outside 1..5 = {t[38]}; "
          f"{'OK ' if t[36] == 0 and t[37] == 0 else 'FAIL'} refused/confirmed between = {t[36]}/{t[37]}")
    ok &= t[38] == 0 and t[36] == 0 and t[37] == 0
for tag in ("base_O", "base_G"):
    t = totals[tag]
    taken = sum(t[6:16])
    print(f"{tag}: taken TT cutoffs total {taken} (classes 6..15 sum); between buckets {t[14]}/{t[15]}")
    ok &= t[14] == 0 and t[15] == 0
    nullt = t[0] + t[1]
    print(f"{tag}: null tries total {nullt} = cut-T {t[0]} + cut-F {t[1]}; "
          f">=beta {t[2] + t[3]} <= tries {nullt}: {'OK' if t[2] + t[3] <= nullt else 'FAIL'}; "
          f"returned {t[4] + t[5]} <= >=beta {t[2] + t[3]}: {'OK' if t[4] + t[5] <= t[2] + t[3] else 'FAIL'}")

print("\n== named cells ==")
for tag in ("base_O", "base_G", "nc_O", "t5_O", "t5_G"):
    t = totals[tag]
    print(f"cnt{tag}:")
    for i, name in enumerate(SLOTS):
        print(f"  [{i:2d}] {name:28s} {t[i]}")

print("\nOVERALL:", "ALL KNOWN ANSWERS HOLD" if ok else "A KNOWN ANSWER FAILED")
sys.exit(0 if ok else 1)
