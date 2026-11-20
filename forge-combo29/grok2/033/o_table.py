#!/usr/bin/env python3
"""o_table.py RAW [RAW ...]  reads raw engine transcripts and prints one row per position."""
import re
import sys


def rows(path):
    nodes = []
    last_info = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None:
                sys.exit(f"STOP: bestmove with no info line in {path}")
            m = re.search(r" nodes (\d+)", last_info)
            if not m:
                sys.exit(f"STOP: last info has no nodes in {path}: {last_info}")
            nodes.append(int(m.group(1)))
            last_info = None
    return nodes


def show(label, path, base=None):
    got = rows(path)
    print(f"{label} file {path} positions {len(got)} sum {sum(got)}")
    if len(got) >= 3:
        print(f"{label} first {got[0]} {got[1]} {got[2]}")
    if base is not None:
        differ = sum(1 for a, b in zip(base, got) if a != b)
        print(f"{label} differ {differ}")
    for i, n in enumerate(got, 1):
        print(f"{label} {i} {n}")
    return got


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: o_table.py label=path ...")
    base = None
    for arg in sys.argv[1:]:
        label, path = arg.split("=", 1)
        got = show(label, path, base)
        if base is None:
            base = got


if __name__ == "__main__":
    main()
