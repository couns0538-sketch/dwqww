#!/usr/bin/env python3
"""kimi5 job 34 controls C-SIGN and C-ALPHA (prints every count it uses).
C-SIGN: on the P records with RAISED 0 or 1, at D1: BEATS rate among RAISED=1 must be >= 3x the
rate among RAISED=0 (file 35: [1.5,3) -> CONTROL WEAK, go on; < 1.5 -> STOP). The same records
through the no-negate scratch run: ratio must fall below 1.5.
C-ALPHA: 200 F records with alpha replaced by -29000: BEATS on every one; with +29000: on none.
Usage: controls_j34.py <p_d1_glob.jsonl...> -- <nosign.jsonl> <f200.jsonl>
"""
import glob
import json
import sys

argv = sys.argv[1:]
sep = argv.index("--")
p_files, nosign_file, f200_file = argv[:sep], argv[sep + 1], argv[sep + 2]

def rate(recs):
    n = len(recs)
    b = sum(1 for r in recs if r["beats"])
    ns = sum(1 for r in recs if r["noscore"])
    return b, n, ns

p = []
for pat in p_files:
    for f in glob.glob(pat):
        p += [json.loads(l) for l in open(f)]
print(f"C-SIGN: P D1 records read {len(p)}")
p1 = [r for r in p if r["r"] == 1]
p0 = [r for r in p if r["r"] == 0]
b1, n1, ns1 = rate(p1)
b0, n0, ns0 = rate(p0)
r1 = b1 / n1 if n1 else 0
r0 = b0 / n0 if n0 else 0
ratio = r1 / r0 if r0 else float("inf")
print(f"C-SIGN (negate): RAISED=1 {b1}/{n1} = {r1:.4f} (noscore {ns1}); RAISED=0 {b0}/{n0} = {r0:.4f} (noscore {ns0}); ratio {ratio:.2f}")

q = [json.loads(l) for l in open(nosign_file)]
print(f"C-SIGN: P r01 no-negate records read {len(q)}")
q1 = [r for r in q if r["r"] == 1]
q0 = [r for r in q if r["r"] == 0]
c1, m1, _ = rate(q1)
c0, m0, _ = rate(q0)
s1 = c1 / m1 if m1 else 0
s0 = c0 / m0 if m0 else 0
sratio = s1 / s0 if s0 else float("inf")
print(f"C-SIGN (NO-negate): RAISED=1 {c1}/{m1} = {s1:.4f}; RAISED=0 {c0}/{m0} = {s0:.4f}; ratio {sratio:.2f}")

verdict = "PASS" if (ratio >= 3 and sratio < 1.5) else ("CONTROL WEAK" if ratio >= 1.5 and sratio < 1.5 else "FAIL")
print("C-SIGN:", verdict)

f = [json.loads(l) for l in open(f200_file)]
print(f"C-ALPHA: F D1 records read {len(f)}")
over = sum(1 for r in f if abs(r["value"]) >= 29000)
sel = [r for r in f if abs(r["value"]) < 29000]
lo = sum(1 for r in sel if r["value"] > -29000)
hi = sum(1 for r in sel if r["value"] > 29000)
print(f"C-ALPHA: records with |value| >= 29000 (mate-valued, excluded from the alpha replacement): {over}")
print(f"C-ALPHA: of the {len(sel)} rest: BEATS at alpha=-29000: {lo} (must be {len(sel)}); at alpha=+29000: {hi} (must be 0)")
print("C-ALPHA:", "PASS" if lo == len(sel) and hi == 0 else "FAIL")
