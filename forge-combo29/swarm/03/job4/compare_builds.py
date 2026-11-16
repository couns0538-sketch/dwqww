#!/usr/bin/env python3
"""compare_builds.py BASEFILE PCFILE OUT : compare two engine_perft JSON files value by value.

Fails loudly if either side is empty or the key sets differ, so a missing file cannot look like agreement.
"""
import json
import sys

bf, pf, out = sys.argv[1], sys.argv[2], sys.argv[3]
b = json.load(open(bf))
p = json.load(open(pf))
br, pr = b["results"], p["results"]
if not br or not pr:
    sys.exit(f"FAIL: empty results (base {len(br)} records, pc {len(pr)} records)")
keys_b, keys_p = set(br), set(pr)
if keys_b != keys_p:
    sys.exit(f"FAIL: position sets differ (base {len(keys_b)}, pc {len(keys_p)}, "
             f"only-base {len(keys_b-keys_p)}, only-pc {len(keys_p-keys_b)})")
diff, n, sums_b, sums_p = [], 0, {}, {}
for idx in sorted(keys_b, key=int):
    for dep in sorted(br[idx], key=int):
        vb, vp = br[idx].get(dep), pr[idx].get(dep)
        if not isinstance(vb, int) or not isinstance(vp, int):
            sys.exit(f"FAIL: non-integer at idx {idx} depth {dep}: base={vb!r} pc={vp!r}")
        n += 1
        sums_b[dep] = sums_b.get(dep, 0) + vb
        sums_p[dep] = sums_p.get(dep, 0) + vp
        if vb != vp:
            diff.append((idx, dep, vb, vp))
if n == 0:
    sys.exit("FAIL: compared nothing")
lines = [f"base exe: {b['exe']}  options: {b.get('options_sent')}",
         f"pc   exe: {p['exe']}  options: {p.get('options_sent')}",
         f"positions: {len(keys_b)}   (position, depth) values compared: {n}",
         f"values identical: {n-len(diff)}",
         f"values different: {len(diff)}",
         "", "| depth | base sum | pc r15 sum | identical |", "|---|---|---|---|"]
for dep in sorted(sums_b, key=int):
    lines.append(f"| {dep} | {sums_b[dep]} | {sums_p.get(dep)} | "
                 f"{'yes' if sums_b[dep]==sums_p.get(dep) else 'NO'} |")
lines.append("")
for row in diff[:100]:
    lines.append(f"DIFF idx={row[0]} depth={row[1]} base={row[2]} pc={row[3]}")
open(out, "w").write("\n".join(lines) + "\n")
print("\n".join(lines[:12]))
