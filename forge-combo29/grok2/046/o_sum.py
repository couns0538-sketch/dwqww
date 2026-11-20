#!/usr/bin/env python3
"""o_sum.py RAW [RAW ...]: last info nodes before each bestmove, then sum and first three."""
import sys


def rows(path):
    nodes = []
    last = None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if line.startswith("info ") and " nodes " in line:
            parts = line.split()
            if "nodes" in parts:
                i = parts.index("nodes")
                last = int(parts[i + 1])
        elif line.startswith("bestmove "):
            if last is None:
                sys.exit(f"STOP: bestmove without info nodes in {path}")
            nodes.append(last)
            last = None
    return nodes


def main():
    series = []
    for path in sys.argv[1:]:
        nodes = rows(path)
        series.append((path, nodes))
        head = " / ".join(str(n) for n in nodes[:3])
        print(f"{path}: n {len(nodes)} sum {sum(nodes)} first {head}")
    if len(series) >= 2:
        a, b = series[0][1], series[1][1]
        if len(a) == len(b):
            differ = sum(1 for x, y in zip(a, b) if x != y)
            print(f"differ {series[1][0]} vs {series[0][0]}: {differ}")
        else:
            print(f"differ length mismatch {len(a)} {len(b)}")
    if len(series) >= 3:
        a, c = series[0][1], series[2][1]
        if len(a) == len(c):
            differ = sum(1 for x, y in zip(a, c) if x != y)
            print(f"differ {series[2][0]} vs {series[0][0]}: {differ}")


if __name__ == "__main__":
    main()
