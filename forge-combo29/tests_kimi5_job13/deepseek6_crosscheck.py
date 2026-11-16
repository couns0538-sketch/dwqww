#!/usr/bin/env python3
"""kimi5 job 13: independent cross-check of deepseek6's job-1 O rows
(branch for-fable-and-opus/deepseek6-work, folder tests_deepseek6_job1/).
Reads the files with `git show FETCH_HEAD:...` (FETCH_HEAD = the fetched tip of that
branch), never copies them. (a) Sums ONE O rows file and prints the sum (must equal
deepseek6's table cell). (b) For every one of the 35 settings compares its runs/O_*_-c
and +c rows against runs/O_S14.rows position by position (nodes): prints how many of
200 positions differ. A 'live' claim needs >= 1 differing position in at least one of
the two runs; a 'dead' claim needs 0 in both.
"""
import subprocess
import sys

PREFIX = "FETCH_HEAD:forge-combo29/tests_deepseek6_job1"


def rows(path):
    out = subprocess.run(["git", "show", f"{PREFIX}/{path}"], capture_output=True,
                         text=True, check=True).stdout
    nodes = {}
    for line in out.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        idx, _, rest = line.partition("|")
        n, _, _bm = rest.partition("|")
        nodes[int(idx.strip())] = int(n.strip())
    return nodes


SETTINGS = [  # name, value under S14 (or default), c
    ("LmrQuietBase", 93, 8), ("LmrQuietDivisor", 205, 12), ("LmrNoisyBase", 13, 6),
    ("LmrNoisyDivisor", 333, 20), ("NullMoveBase", 5, 1), ("NullMoveDepthDivisor", 3, 1),
    ("NullMoveEvalDivisor", 200, 20), ("RfpDepth", 8, 1), ("RfpMargin", 72, 6),
    ("RfpImproving", 40, 6), ("RazorBase", 150, 20), ("RazorMultiplier", 350, 25),
    ("FutilityDepth", 7, 1), ("FutilityBase", 100, 12), ("FutilityMultiplier", 110, 10),
    ("LmpBase", 8, 1), ("HistoryPruneMultiplier", 2220, 200), ("SeeQuietMultiplier", 24, 3),
    ("SeeNoisyMultiplier", 150, 12), ("SingularDepth", 6, 1), ("SingularMargin", 2, 1),
    ("IirDepth", 2, 1), ("ProbcutDepth", 5, 1), ("ProbcutMargin", 180, 15),
    ("QsFutilityMargin", 160, 14), ("QsSeeMargin", 40, 6), ("AspirationDelta", 18, 2),
    ("HistoryBonusQuadratic", 24, 3), ("HistoryBonusLinear", 54, 6),
    ("HistoryBonusMax", 2212, 180), ("LmrHistoryDivisor", 5643, 500),
    ("LmrCutoffThreshold", 3, 1), ("MaterialCorrectionWeight", 100, 10),
    ("CaptureFutilityMultiplier", 250, 25), ("CaptureFutilityDepth", 6, 1),
]

one = rows("runs/O_QsSeeMargin_34.rows")
s = sum(one.values())
print(f"(a) my own sum of runs/O_QsSeeMargin_34.rows over {len(one)} positions = {s} "
      f"(deepseek6's table cell: 9,500,069) -> {'EQUAL' if s == 9500069 else 'MISMATCH'}")

base = rows("O_S14_base.rows")
print(f"base O_S14_base.rows: {len(base)} positions, my sum = {sum(base.values())}")
print("(b) positions with node count differing from S14, of 200:")
bad = 0
for name, value, c in SETTINGS:
    lo, hi = value - c, value + c
    verdict = []
    for tag, v in (("m", lo), ("p", hi)):
        try:
            r = rows(f"runs/O_{name}_{v}.rows")
        except subprocess.CalledProcessError:
            print(f"  {name}: runs/O_{name}_{v}.rows MISSING")
            bad += 1
            continue
        diff = sum(1 for i in base if base[i] != r.get(i))
        verdict.append(f"{tag}({v}): {diff} differ")
    print(f"  {name:28s} {verdict[0]:16s} {verdict[1]:16s}")
sys.exit(0 if bad == 0 else 1)
