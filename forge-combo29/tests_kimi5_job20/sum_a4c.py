#!/usr/bin/env python3
"""kimi5 job 20 Step 3 summer + counting==plain per-position check.
Sums the 'info string A4C v1' lines of every counter run's full.txt (prints how many
it summed), and checks the counting build's rows equal the plain build's per position
(nodes AND best move) for base, snd32, gcd32 on O and G (Step 1 jsons vs Step 3 jsons).
usage: sum_a4c.py <rowsdir>
"""
import json
import re
import sys

ROWS = sys.argv[1]
PAT = re.compile(
    r"info string A4C v1 sn (\d+),(\d+),(\d+) (\d+),(\d+),(\d+) (\d+),(\d+),(\d+) (\d+),(\d+),(\d+)"
    r" seeq (\d+) pick (\d+),(\d+),(\d+),(\d+),(\d+) flg (\d+),(\d+)")

def sum_run(tag):
    path = f"{ROWS}/{tag}_full.txt"
    tot = [0] * 20
    n = 0
    with open(path) as f:
        for line in f:
            m = PAT.search(line)
            if m:
                n += 1
                for i, v in enumerate(m.groups()):
                    tot[i] += int(v)
    return n, tot

print("== A4C totals (columns: sn_tested n/z/p, sn_pruned n/z/p, moved_pruned n/z/p, moved_saved n/z/p, seeq,")
print("    cap_tested, cap_bad, cap_changed, good_out, good_flagfalse, flg2167, flg2219) ==")
for tag in ["cbase_O_d12", "cbase_G_d12", "csnd32_O_d12", "csnd32_G_d12", "cgcd32_O_d12", "cgcd32_G_d12"]:
    n, t = sum_run(tag)
    sn_t = f"{t[0]},{t[1]},{t[2]}"
    sn_p = f"{t[3]},{t[4]},{t[5]}"
    sn_mp = f"{t[6]},{t[7]},{t[8]}"
    sn_ms = f"{t[9]},{t[10]},{t[11]}"
    print(f"{tag:15s} searches {n:4d} | sn {sn_t} pr {sn_p} mp {sn_mp} ms {sn_ms} seeq {t[12]} | "
          f"pick {t[13]},{t[14]},{t[15]},{t[16]},{t[17]} | flg {t[18]},{t[19]}")

print()
print("== counting build == plain build, per position (nodes AND best move) ==")
for s in ["base", "snd32", "gcd32"]:
    for setname, npos in [("O", 200), ("G", 353)]:
        with open(f"{ROWS}/{s}_{setname}_d12.json") as f:
            a = json.load(f)
        with open(f"{ROWS}/c{s}_{setname}_d12.json") as f:
            b = json.load(f)
        eq_n = sum(1 for x, y in zip(a["per_position"], b["per_position"]) if x == y)
        eq_b = sum(1 for x, y in zip(a["bestmove"], b["bestmove"]) if x == y)
        print(f"{s:6s} {setname}: nodes {eq_n}/{npos}, best moves {eq_b}/{npos}")
