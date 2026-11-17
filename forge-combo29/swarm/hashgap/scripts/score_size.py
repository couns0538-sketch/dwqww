"""Second pass over the threshold data: how big is the score disagreement, and is
the budget where it starts ordinary or absurd?

A score that differs by 1 cp and a score that differs by 80 cp are not the same
finding. Both are reported separately rather than averaged into one number.
"""

import json
import sys
from collections import Counter

PATH = sys.argv[1] if len(sys.argv) > 1 else "../evidence/threshold.jsonl"

rows = [json.loads(line) for line in open(PATH) if line.strip()]
by_key = {(r["fen"], r["budget"], r["hash"]): r for r in rows}
fens = sorted({r["fen"] for r in rows})
budgets = sorted({r["budget"] for r in rows})

print("## Score-difference size, Hash 16 vs Hash 64\n")
print("| budget | n | 0 cp | 1-4 cp | 5-19 cp | 20-49 cp | >=50 cp | median |max| |")
print("|---|---|---|---|---|---|---|---|")

for budget in budgets:
    deltas = []
    for fen in fens:
        a = by_key[(fen, budget, 16)]
        b = by_key[(fen, budget, 64)]
        if a["score"] is None or b["score"] is None:
            continue
        if a["score"][0] != b["score"][0]:
            # cp vs mate is its own class of disagreement, not a centipawn delta.
            deltas.append(9999)
            continue
        deltas.append(abs(a["score"][1] - b["score"][1]))

    buckets = Counter()
    for delta in deltas:
        if delta == 0:
            buckets["0"] += 1
        elif delta < 5:
            buckets["1-4"] += 1
        elif delta < 20:
            buckets["5-19"] += 1
        elif delta < 50:
            buckets["20-49"] += 1
        else:
            buckets[">=50"] += 1

    ordered = sorted(deltas)
    median = ordered[len(ordered) // 2] if ordered else 0
    worst = ordered[-1] if ordered else 0
    worst_text = "mate-vs-cp" if worst == 9999 else str(worst)
    print(f"| {budget} | {len(deltas)} | {buckets['0']} | {buckets['1-4']} | "
          f"{buckets['5-19']} | {buckets['20-49']} | {buckets['>=50']} | "
          f"{median} | {worst_text} |")

# ---------------------------------------------------------------------------
# What budget is "ordinary"? Measured nps, not assumed.

print("\n## Is the diverging budget ordinary? Measured speed on this machine\n")
import subprocess
import time

binary = sys.argv[2] if len(sys.argv) > 2 else "/home/ubuntu/build-trace/forge"
probe = subprocess.run(
    [binary],
    input="bench 13\nquit\n",
    capture_output=True,
    text=True,
)
nps = None
for line in probe.stdout.splitlines():
    if "bench depth" in line:
        parts = line.split()
        if "nps" in parts:
            nps = int(parts[parts.index("nps") + 1])
print(f"bench nps on this machine: {nps}")

if nps:
    print("\n| wall time | nodes the engine would search | Hash 16 vs 64 move differs? |")
    print("|---|---|---|")
    for seconds in (0.1, 0.25, 0.5, 1.0, 2.0, 5.0):
        nodes = int(nps * seconds)
        # Nearest measured budget at or below this node count.
        eligible = [b for b in budgets if b <= nodes]
        budget = max(eligible) if eligible else None
        if budget is None:
            print(f"| {seconds}s | {nodes} | below the smallest measured budget |")
            continue
        move_diff = sum(
            1 for fen in fens
            if by_key[(fen, budget, 16)]["bestmove"] != by_key[(fen, budget, 64)]["bestmove"]
        )
        print(f"| {seconds}s | {nodes} | {move_diff}/{len(fens)} at the {budget} row |")
