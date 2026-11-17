#!/usr/bin/env python3
"""tie_test.py : tests the TIE BRANCH in margins.py by executing the block AS WRITTEN in that file.

23-F225: `winner = a if sa > sc else c` credits an equal score to c, and the c-count then
reads that tie as evidence for the 250000 budget. This test extracts the comparison block
from margins.py itself (not a copy), so it fails if the file is reverted.

Exits nonzero if a tie is credited to either candidate."""
import re, sys, textwrap, os

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "margins.py")).read()
m = re.search(r"(    if sa > sc:\n(?:        .*\n|    else:\n        .*\n|    elif sc > sa:\n        .*\n)+)", src)
if not m:
    # accept the OLD single-line form too, so the test reports the defect rather than erroring
    m2 = re.search(r"(    winner = a if sa > sc else c\n)", src)
    if not m2:
        print("FAIL: could not locate the comparison block in margins.py"); sys.exit(2)
    block = m2.group(1)
    print("NOTE: margins.py still contains the OLD tie-collapsing form.")
else:
    block = m.group(1)

block = textwrap.dedent(block)
def run(sa, sc):
    a, c = "a_move", "c_move"
    ns = {"sa": sa, "sc": sc, "a": a, "c": c}
    exec(block, ns)
    return ns["winner"]

fails = []
def check(label, sa, sc, want):
    got = run(sa, sc)
    ok = got == want
    print("  %-40s sa=%-5s sc=%-5s -> winner=%-6s want=%-6s %s"
          % (label, sa, sc, got, want, "OK" if ok else "**FAIL**"))
    if not ok: fails.append(label)

print("TIE CASES (the branch that was silently collapsing):")
check("equal scores", 40, 40, "tie")
check("equal negative scores", -70, -70, "tie")
check("both zero", 0, 0, "tie")
print("STRICT CASES (must still work):")
check("a higher", 65, 48, "a_move")
check("c higher", 48, 65, "c_move")
print()
if fails:
    print("VERDICT: FAIL (%d)" % len(fails))
    print("A tie credited to a candidate is counted as that candidate being better.")
    sys.exit(1)
print("VERDICT: PASS - ties are their own outcome and cannot be counted for either side")
sys.exit(0)
