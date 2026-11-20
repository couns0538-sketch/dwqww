#!/usr/bin/env python3
"""read_o.py RAW [RAW ...]

Reads engine stdout. For each bestmove, takes the nodes field of the last
info line before it. Prints count, sum, first three, and (when two or more
files) how many positions differ from the first file.
"""
import re
import sys


def nodes_of(path):
    found = []
    last_info = None
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.startswith("info "):
            last_info = line.rstrip("\r\n")
        elif line.startswith("bestmove"):
            if last_info is None:
                sys.exit(f"STOP: {path} bestmove {len(found) + 1} has no info line")
            match = re.search(r"\bnodes (\d+)", last_info)
            if not match:
                sys.exit(f"STOP: {path} position {len(found) + 1} last info has no nodes: {last_info}")
            found.append(int(match.group(1)))
            last_info = None
    return found


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: read_o.py RAW [RAW ...]")
    series = [(path, nodes_of(path)) for path in sys.argv[1:]]
    base = series[0][1]
    for path, nodes in series:
        head = " / ".join(str(n) for n in nodes[:3])
        print(f"{path}: positions {len(nodes)} sum {sum(nodes)} first {head}")
        if nodes is not base:
            differ = sum(1 for a, b in zip(base, nodes) if a != b)
            extra = abs(len(base) - len(nodes))
            print(f"  differ_from_first {differ} length_mismatch {extra}")


if __name__ == "__main__":
    main()
