#!/usr/bin/env python3
"""analyse_job2.py -- reads the raw files and prints, per set, every position's last-pv score, its node count,
and its bestmove. Every number printed here is read from the committed raw files.
"""
import re

SETS = ["KvK", "KNvK", "KBvK", "KNNvK", "fifty0", "fifty98", "fifty99", "threefold"]


def blocks(path):
    cur = None
    for line in open(path):
        line = line.rstrip("\n")
        if line.startswith("### pos "):
            cur = {"head": line, "lines": []}
        elif line.startswith("### end"):
            if cur:
                yield cur
            cur = None
        elif cur is not None:
            cur["lines"].append(line)
    if cur:
        yield cur


def info(b):
    pv = [l for l in b["lines"] if re.search(r"\binfo\b.*\bpv\b", l)]
    bm = [l for l in b["lines"] if l.startswith("bestmove")]
    if pv:
        last = pv[-1]
        m = re.search(r"score (mate|cp) (-?\d+)", last)
        nm = re.search(r"\bnodes (\d+)", last)
        depth = re.search(r"depth (\d+)", last)
        return (m.group(1) + " " + m.group(2) if m else "?", nm.group(1) if nm else "?",
                depth.group(1) if depth else "?", last, bm[0] if bm else "(none)")
    return ("none", "0" if not pv else "?", "-", "(no info line)", bm[0] if bm else "(none)")


print("| set | pos | score | nodes | depth | bestmove |")
print("|---|---|---|---|---|---|")
per_set = {}
for name in SETS:
    rows = []
    for b in blocks(f"out/{name}.raw.txt"):
        sc, nodes, depth, last, bm = info(b)
        pos = b["head"].split()[2]
        rows.append((pos, sc, nodes, depth, bm, last))
        print(f"| {name} | {pos} | {sc} | {nodes} | {depth} | {bm} |")
    per_set[name] = rows

print()
print("SUMMARY per set")
print("| set | n | distinct scores | all cp 0? | any mate? | total nodes | bestmoves missing |")
print("|---|---|---|---|---|---|---|")
for name in SETS:
    rows = per_set[name]
    scores = [r[1] for r in rows]
    allzero = all(s == "cp 0" for s in scores)
    anymate = any(s.startswith("mate") for s in scores)
    tot = sum(int(r[2]) for r in rows if r[2].isdigit())
    missing = sum(1 for r in rows if r[4] == "(none)")
    print(f"| {name} | {len(rows)} | {sorted(set(scores))} | {allzero} | {anymate} | {tot} | {missing} |")
