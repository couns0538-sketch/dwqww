#!/usr/bin/env python3
"""compare.py ENGFILE OUTFILE DIFFOUT : per-position, per-depth comparison engine vs python-chess.
Prints a markdown table; writes every difference to DIFFOUT with the FEN."""
import json, sys

ef, pf, diffout = sys.argv[1], sys.argv[2], sys.argv[3]
e = json.load(open(ef)); p = json.load(open(pf))
fens = [l.strip() for l in open(e["fens"]) if l.strip()]
bad_pairs, bad_pos, missing = [], {}, 0
sums = {d: [0, 0] for d in range(1, e["maxdepth"] + 1)}
with open(diffout, "w") as df:
    for i, fen in enumerate(fens):
        pe = p["results"].get(str(i), {})
        if pe.get("refused"):
            df.write(f"PYREFUSED\t{i}\t{fen}\t{pe['refused']}\n")
            continue
        for d in range(1, e["maxdepth"] + 1):
            a = e["results"].get(str(i), {}).get(str(d))
            b = pe.get(str(d))
            if a is None or b is None:
                missing += 1
                df.write(f"MISSING\t{i}\td{d}\tengine={a} py={b}\t{fen}\n")
                continue
            sums[d][0] += a; sums[d][1] += b
            if a != b:
                bad_pairs.append((i, d, a, b))
                bad_pos.setdefault(i, []).append(d)
                df.write(f"DIFF\t{i}\td{d}\tengine={a} py={b}\tdelta={a-b}\t{fen}\n")
print(f"positions: {len(fens)}")
print(f"python-chess refused FENs: {len(p['refused'])}")
print(f"positions with >=1 differing depth: {len(bad_pos)}")
print(f"differing (position, depth) pairs: {len(bad_pairs)}")
print(f"missing measurements: {missing}")
print(f"engine crashes/restarts: {len(e['restarts'])}")
print(f"engine error lines: {len(e['errors'])}")
print()
print("| depth | engine sum | python-chess sum | equal |")
print("|---|---|---|---|")
for d in sorted(sums):
    print(f"| {d} | {sums[d][0]} | {sums[d][1]} | {'yes' if sums[d][0]==sums[d][1] else 'NO'} |")
print()
print(f"mean engine perft(1) branching factor: {sums[1][0]/len(fens):.3f}")
if e["restarts"]:
    print("\nRESTARTS:")
    for r in e["restarts"]:
        print(r)
if e["errors"]:
    print("\nERRORS (first 20):")
    for r in e["errors"][:20]:
        print(r)
