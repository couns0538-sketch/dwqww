#!/usr/bin/env python3
"""o_table.py A.txt [B.txt ...]
Reads raw engine transcripts. One row per bestmove: position number and the
nodes field of the last info line before that bestmove. Prints sum, first
three, and (when a second file is given) how many positions differ from the
first file.
"""
import sys


def rows(path):
    last_info = None
    found = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None:
                sys.exit(f"STOP: bestmove with no info in {path} at game {len(found) + 1}")
            parts = last_info.split()
            try:
                nodes = int(parts[parts.index("nodes") + 1])
            except (ValueError, IndexError):
                sys.exit(f"STOP: last info has no nodes in {path} position {len(found) + 1}: {last_info}")
            found.append(nodes)
            last_info = None
    return found


def show(path, base):
    got = rows(path)
    print(f"file {path}")
    print(f"positions {len(got)}")
    print(f"sum {sum(got)}")
    if len(got) >= 3:
        print(f"first {got[0]} {got[1]} {got[2]}")
    if base is not None:
        n = min(len(base), len(got))
        differ = sum(1 for i in range(n) if base[i] != got[i])
        if len(base) != len(got):
            differ += abs(len(base) - len(got))
        print(f"differ {differ}")
    return got


def main():
    paths = sys.argv[1:]
    if not paths:
        sys.exit("usage: o_table.py A.txt [B.txt ...]")
    base = show(paths[0], None)
    for path in paths[1:]:
        show(path, base)


if __name__ == "__main__":
    main()
