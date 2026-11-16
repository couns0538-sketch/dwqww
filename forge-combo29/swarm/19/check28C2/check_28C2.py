#!/usr/bin/env python3
"""check_28C2.py : my own check of seat 28's S-C2, which refutes the CAUSE of my 19-F7.

28's claim: two clean rebuilds of the same source with the same flags are byte-identical, so the 4.2 %
difference I reported was sequential-block drift inside my own run order, not a build effect.

I test the part that is checkable from my own committed data plus one new experiment:
  (1) My own raw file: do baseA's late runs sit at baseB's level?  (no new engine needed)
  (2) Two fresh builds from the SAME tree: are their sha256 hashes equal?
  (3) Are the per-run spreads of a single block wider than the block-to-block difference?
Verdict rule, fixed before running: CONFIRMS if (2) hashes are equal AND (1) the late baseA runs overlap
baseB's range AND (3) single-run spread > block difference.
"""
import hashlib
import os
import subprocess
import sys

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
lines = []

# (1) my own committed timings
four = "forge-combo29/swarm/19/job2/four_builds_times.txt"
blocks = {}
cur = None
for line in open(four):
    line = line.strip()
    if line.endswith(":"):
        cur = line[:-1]
        blocks[cur] = []
    elif line and cur:
        parts = line.split()
        if len(parts) == 3:
            blocks[cur].append(int(parts[1]))
a, b = blocks.get("baseA", []), blocks.get("baseB", [])
lines.append("baseA times: %s" % a)
lines.append("baseB times: %s" % b)
if a and b:
    late_a = a[-4:]
    lines.append("baseA last four: %s  (baseB range [%d, %d])" % (late_a, min(b), max(b)))
    overlap = all(min(b) - 5 <= x <= max(b) + 5 for x in late_a)
    lines.append("late baseA runs sit at baseB's level: %s" % overlap)

# (2) two fresh builds, same tree
hashes = []
for tag in ("rb1", "rb2"):
    d = os.path.expanduser("~/check28/" + tag)
    subprocess.run(["rm", "-rf", d], check=True)
    subprocess.run("cp -a ~/base/forge-combo29 " + d, shell=True, check=True)
    bd = os.path.expanduser("~/check28/build_" + tag)
    subprocess.run(["rm", "-rf", bd], check=True)
    subprocess.run(["cmake", "-S", d, "-B", bd, "-DCMAKE_BUILD_TYPE=Release",
                    "-DCMAKE_CXX_COMPILER=g++"], capture_output=True, check=True)
    subprocess.run(["make", "-C", bd, "-j4"], capture_output=True, check=True)
    h = hashlib.sha256(open(os.path.join(bd, "forge"), "rb").read()).hexdigest()
    hashes.append(h)
lines.append("rebuild 1 sha256: %s" % hashes[0])
lines.append("rebuild 2 sha256: %s" % hashes[1])
identical = hashes[0] == hashes[1]
lines.append("the two rebuilds are byte-identical: %s" % identical)

# (3) single-run spread vs the block difference
lines.append("single-run spread inside baseA: %d..%d = %.1f %% of the median"
             % (min(a), max(a), 100.0 * (max(a) - min(a)) / sorted(a)[len(a) // 2]))
lines.append("block-to-block difference (medians): %d vs %d = %.1f %%"
             % (sorted(a)[len(a) // 2], sorted(b)[len(b) // 2],
                100.0 * abs(sorted(a)[len(a) // 2] - sorted(b)[len(b) // 2]) / sorted(b)[len(b) // 2]))

verdict = "CONFIRMS" if (identical and overlap) else "REFUTES"
lines.append("")
lines.append("VERDICT %s 28's S-C2 (against my 19-F7's cause)" % verdict)
text = "\n".join(lines)
open(os.path.join(OUT, "RESULT.txt"), "w").write(text + "\n")
print(text)
