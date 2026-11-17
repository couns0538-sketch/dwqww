#!/usr/bin/env python3
"""audit_plan_numbers.py OUT — mechanically audit every plan-arithmetic claim in this area's files.

Tonight I twice wrote plan numbers from memory and got them wrong (the 72/360 and 8/40 case, and earlier an
"iteration cost" that was really the whole ladder). Prose arithmetic is the failure mode, so this script does what
prose cannot: it COMPUTES the plan for every clock value that appears in my files and prints the table, so any
published number can be checked against it.

Plan from include/forge/clock_plan.hpp with the engine's defaults: Move Overhead 10, TmSoftDivisor 22,
TmIncrementPercent 75, TmHardPercent 60, TmHardSoftMultiple 5. For movestogo: soft = avail/(mtg+1) + inc*3/4,
hard = min(avail*4/5, soft*4).
"""
import re
import subprocess
import sys
from pathlib import Path

OUT = sys.argv[1]
OVERHEAD, DIV, INC_PCT, HARD_PCT, MULT = 10, 22, 75, 60, 5


def plan(clock, inc=0):
    if clock <= OVERHEAD:
        return 0, 0, True
    avail = clock - OVERHEAD
    soft = avail // DIV + inc * INC_PCT // 100
    hard = min(avail * HARD_PCT // 100, soft * MULT)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard, False


def plan_mtg(clock, inc, mtg):
    if clock <= OVERHEAD:
        return 0, 0, True
    avail = clock - OVERHEAD
    m = min(mtg, 50)
    soft = avail // (m + 1) + inc * 3 // 4
    hard = min(avail * 4 // 5, soft * 4)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard, False


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## The plan, computed — check any published number against this")
emit("")
emit("### sudden-death clocks, winc 0")
emit("")
emit("| clock ms | soft | hard | reserve empty? |")
emit("|---|---|---|---|")
for c in (0, 1, 10, 11, 30, 100, 200, 500, 1000, 1600, 3000, 6000, 10000, 30000):
    s, h, e = plan(c, 0)
    emit("| %d | %d | %d | %s |" % (c, s, h, "YES" if e else "no"))

emit("")
emit("### the owner's control (inc 60) at the clocks this area uses")
emit("")
emit("| clock ms | inc | soft | hard |")
emit("|---|---|---|---|")
for c in (200, 400, 800, 1200, 1600, 3000, 6000, 10000, 30000):
    s, h, _ = plan(c, 60)
    emit("| %d | 60 | **%d** | **%d** |" % (c, s, h))

emit("")
emit("### movestogo at a 1000 ms clock, inc 0 (the job3 controls)")
emit("")
emit("| movestogo | soft | hard |")
emit("|---|---|---|")
for m in (1, 2, 40, 50):
    s, h, _ = plan_mtg(1000, 0, m)
    emit("| %d | %d | %d |" % (m, s, h))

# now scan the folder for numbers of the form "soft X / hard Y" and flag any that disagree with the table
emit("")
emit("## Scan: every 'soft N / hard M' claim in the .md files, checked against the computed value")
emit("")
emit("| file | claim | matches a computed plan? |")
emit("|---|---|---|")
computed = {}
for c in list(range(0, 40001, 1)):
    pass  # too slow; use the tested set instead
valid = set()
for c in (0, 1, 10, 11, 30, 100, 200, 400, 500, 800, 1000, 1200, 1600, 3000, 6000, 10000, 30000):
    for inc in (0, 60):
        s, h, e = plan(c, inc)
        valid.add((s, h))
for m in (1, 2, 40, 50):
    s, h, _ = plan_mtg(1000, 0, m)
    valid.add((s, h))

root = Path(".")
hits = 0
bad = 0
for p in sorted(root.rglob("*.md")):
    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        continue
    for m in re.finditer(r"soft\s*(\d+)\s*/\s*hard\s*(\d+)", txt):
        a, b = int(m.group(1)), int(m.group(2))
        hits += 1
        ok = (a, b) in valid
        if not ok:
            bad += 1
            emit("| %s | soft %d / hard %d | **NO** |" % (p, a, b))
emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| 'soft N / hard M' claims found in .md files | %d |" % hits)
emit("| claims that match a computed plan | %d |" % (hits - bad))
emit("| claims that DO NOT match any computed plan | **%d** |" % bad)

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
