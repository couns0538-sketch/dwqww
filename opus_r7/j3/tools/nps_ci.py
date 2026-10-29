#!/usr/bin/env python3
"""R7 J3: paired NPS gain with a 95% t-interval from nps_opts_ab.py JSON files (several files are pooled per set).
usage: nps_ci.py <a.json> [b.json ...] --ref off --sets tt aa
For each set and depth: per-round ratio set/ref of wall and CPU-time NPS (same round = same process order slot),
mean gain, 95% CI (t, n - 1 degrees of freedom), n."""
import json
import math
import statistics
import sys

T95 = {4: 2.776, 9: 2.262, 14: 2.145, 19: 2.093, 24: 2.064, 29: 2.045}
args = sys.argv[1:]
files = [a for a in args if a.endswith(".json")]
ref = args[args.index("--ref") + 1]
si = args.index("--sets") + 1
sets = []
while si < len(args) and not args[si].startswith("--"):
    sets.append(args[si])
    si += 1
pooled = {}
for fn in files:
    d = json.load(open(fn, encoding="utf-8"))
    for s in sets:
        if s not in d["raw"] or ref not in d["raw"]:
            continue
        for depth, rows in d["raw"][s].items():
            refrows = d["raw"][ref][depth]
            for a, b in zip(rows, refrows):
                assert a["nodes"] == b["nodes"], (fn, s, depth)
                pooled.setdefault((s, depth), []).append((a["wall_nps"] / b["wall_nps"], a["cpu_nps"] / b["cpu_nps"]))
for (s, depth), rs in sorted(pooled.items()):
    n = len(rs)
    t = T95.get(n - 1, 1.96)
    out = []
    for k, label in ((0, "wall"), (1, "cpu")):
        logs = [math.log(r[k]) for r in rs]
        m = statistics.mean(logs)
        se = statistics.stdev(logs) / math.sqrt(n) if n > 1 else float("nan")
        out.append(f"{label} {100 * (math.exp(m) - 1):+.2f}% [{100 * (math.exp(m - t * se) - 1):+.2f}, {100 * (math.exp(m + t * se) - 1):+.2f}]")
    print(f"{s} vs {ref} d{depth} n={n}: " + "; ".join(out))
