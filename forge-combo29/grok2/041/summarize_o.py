#!/usr/bin/env python3
"""summarize_o.py RAW [RAW ...]
Reads engine transcripts. One row per bestmove: position number and the nodes
field of the last info line before that bestmove. Prints sum, first three, and
how many positions differ from the first file.
"""
import re
import sys


def rows(path):
    found = []
    last_info = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None:
                sys.exit(f"STOP: bestmove with no info line in {path}")
            match = re.search(r" nodes (\d+)", last_info)
            if not match:
                sys.exit(f"STOP: no nodes on last info line in {path}: {last_info}")
            found.append(int(match.group(1)))
            last_info = None
    if not found:
        sys.exit(f"STOP: no positions in {path}")
    return found


def show(path, nodes):
    print(f"{path}")
    print(f"positions {len(nodes)}")
    print(f"sum {sum(nodes)}")
    print("first " + " / ".join(str(n) for n in nodes[:3]))


def main():
    series = [(path, rows(path)) for path in sys.argv[1:]]
    base = series[0][1]
    for path, nodes in series:
        show(path, nodes)
        differ = sum(1 for a, b in zip(base, nodes) if a != b)
        if len(nodes) != len(base):
            print(f"length differs from first file: {len(nodes)} vs {len(base)}")
        else:
            print(f"differ_from_first {differ}")
        print()


if __name__ == "__main__":
    main()
