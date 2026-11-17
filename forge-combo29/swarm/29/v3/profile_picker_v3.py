#!/usr/bin/env python3
"""Which LINE of the picker costs most on the v3 path? Line-level callgrind attribution of bench 13 under PC20+net.

The function-level profile (29-F58) says pick_best 10.24 % + next 6.71 % + introsort 3.80 %. This asks WHERE inside
them, so a patch can target a line rather than a function. Requires a portable -g build (callgrind cannot decode
AVX-512), same flags as the lock build otherwise.
"""
import re, subprocess, sys
OUT = sys.argv[1]
rep = subprocess.run(["callgrind_annotate","--auto=yes","--threshold=99",OUT],capture_output=True,text=True).stdout
open("/tmp/v3ann.txt","w").write(rep)
pat=re.compile(r'^\s*([0-9][0-9,]*)\s+\(\s*([0-9.]+)%\)\s{2,}(.*)$')
KEYS=("int score = main[move.from]","score += (*cont1)","score += (*cont2)","score += (*cont4)",
      "moves_[count_++] = Scored","push_scored","seeded_","if (score > best_score)","best_score = score",
      "std::swap(moves_[index_]","_mm256_permutevar8x32","_mm_max_epi32","chunk_max","std::sort(","__introsort_loop",
      "switch (stage_)","while (index_ < count_)")
rows=[]
for line in rep.splitlines():
    m=pat.match(line)
    if not m: continue
    src=m.group(3).strip()
    if src.startswith("=>"): continue
    if any(k in src for k in KEYS):
        rows.append((int(m.group(1).replace(',','')), src[:92]))
seen=set(); uniq=[]
for v,s in rows:
    if (v,s) in seen: continue
    seen.add((v,s)); uniq.append((v,s))
print("| instructions | picker line |")
print("|---|---|")
for v,s in sorted(uniq, reverse=True)[:14]:
    print(f"| {v:,} | {s} |")
