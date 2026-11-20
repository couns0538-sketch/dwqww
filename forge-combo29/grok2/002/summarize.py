#!/usr/bin/env python3
"""Read raw honesty and O-run transcripts. Print the table. Do not invent numbers.

Usage:
  summarize.py honesty OUTDIR TAG
  summarize.py orun A.txt B.txt
  summarize.py differ A.txt B.txt
"""
import re
import sys


def nodes_of_info(line):
    match = re.search(r" nodes (\d+)", line)
    return int(match.group(1)) if match else None


def honesty(path):
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    if "perft" in path:
        for line in reversed(lines):
            if line.startswith("nodes "):
                return int(line.split()[1])
        return None
    for line in lines:
        if line.startswith("info string bench "):
            match = re.search(r" nodes (\d+)", line)
            if match:
                return int(match.group(1))
    return None


def positions(path):
    rows = []
    current = None
    last_info = None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if line.startswith("# POS "):
            current = int(line.split()[2])
            last_info = None
            continue
        if current is None:
            continue
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove"):
            rows.append((current, nodes_of_info(last_info) if last_info else None, last_info))
            current = None
            last_info = None
    return rows


def cmd_honesty(argv):
    outdir, tag = argv
    print(f"tag {tag}")
    for name in ("bench11", "bench13", "bench16", "perft5"):
        path = f"{outdir}/{tag}_{name}.txt"
        print(f"{name} {honesty(path)} file {path}")


def cmd_orun(argv):
    for path in argv:
        rows = positions(path)
        nums = [n for _, n, _ in rows]
        missing = sum(1 for n in nums if n is None)
        total = sum(n for n in nums if n is not None)
        first = nums[:3]
        print(f"file {path}")
        print(f"positions {len(rows)} missing {missing} sum {total}")
        print("first3 " + " ".join("?" if n is None else str(n) for n in first))


def cmd_differ(argv):
    a, b = argv
    ra = {i: n for i, n, _ in positions(a)}
    rb = {i: n for i, n, _ in positions(b)}
    keys = sorted(set(ra) & set(rb))
    differ = [k for k in keys if ra[k] != rb[k]]
    print(f"compared {len(keys)} differ {len(differ)}")
    if differ[:20]:
        print("first_differ " + " ".join(str(k) for k in differ[:20]))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    kind = sys.argv[1]
    if kind == "honesty":
        cmd_honesty(sys.argv[2:])
    elif kind == "orun":
        cmd_orun(sys.argv[2:])
    elif kind == "differ":
        cmd_differ(sys.argv[2:])
    else:
        sys.exit(__doc__)
