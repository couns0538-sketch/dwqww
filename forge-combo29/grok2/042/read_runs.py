#!/usr/bin/env python3
"""read_runs.py: print honesty nodes and O-run sums from raw engine transcripts.

  python3 read_runs.py honesty <transcript>
  python3 read_runs.py orun <transcript> [<baseline transcript>]

O-run rows are the nodes field of the last info line before each bestmove.
With a baseline, also prints how many positions differ.
"""
import sys


def nodes_of_info(line):
    parts = line.split()
    if "nodes" not in parts:
        sys.exit(f"STOP: info line has no nodes: {line}")
    return int(parts[parts.index("nodes") + 1])


def honesty(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    bench = [ln for ln in lines if ln.startswith("info string bench depth ")]
    perft = [ln for ln in lines if ln.startswith("nodes ")]
    if bench:
        ln = bench[-1]
        print(ln)
        print(f"nodes {nodes_of_info(ln)}")
        return
    if perft:
        print(perft[-1])
        return
    sys.exit(f"STOP: no bench or perft line in {path}")


def orun_nodes(path):
    rows = []
    last = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info "):
            last = line
        elif line.startswith("bestmove "):
            if last is None:
                sys.exit(f"STOP: bestmove with no info in {path}")
            rows.append(nodes_of_info(last))
            last = None
    if len(rows) != 200:
        sys.exit(f"STOP: {path} has {len(rows)} positions, expected 200")
    return rows


def orun(path, baseline):
    rows = orun_nodes(path)
    print(f"sum {sum(rows)}")
    print(f"first3 {rows[0]} {rows[1]} {rows[2]}")
    if baseline:
        base = orun_nodes(baseline)
        differ = sum(1 for a, b in zip(rows, base) if a != b)
        print(f"differ {differ}")
        same = differ == 0
        print(f"identical {same}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    if sys.argv[1] == "honesty":
        honesty(sys.argv[2])
    elif sys.argv[1] == "orun":
        orun(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        sys.exit(__doc__)
