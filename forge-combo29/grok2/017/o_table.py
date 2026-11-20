#!/usr/bin/env python3
"""o_table.py RAW [RAW ...]: nodes of the last info-depth line before each bestmove."""
import re
import sys

NODE = re.compile(r"^info depth \d+.* nodes (\d+) ")


def rows(path):
    nodes = []
    last = None
    bestmoves = 0
    for line in open(path, encoding="utf-8"):
        m = NODE.match(line)
        if m:
            last = int(m.group(1))
        elif line.startswith("bestmove"):
            bestmoves += 1
            if last is None:
                sys.exit(f"STOP: {path} bestmove {bestmoves} had no info depth")
            nodes.append(last)
            last = None
    if bestmoves != 200:
        sys.exit(f"STOP: {path} has {bestmoves} bestmoves, want 200")
    return nodes


def show(tag, nodes):
    print(f"{tag} n={len(nodes)} sum={sum(nodes)} first={nodes[0]} {nodes[1]} {nodes[2]}")


def main():
    series = [(path, rows(path)) for path in sys.argv[1:]]
    for path, nodes in series:
        show(path, nodes)
    if len(series) >= 2:
        a, b = series[0][1], series[1][1]
        differ = sum(x != y for x, y in zip(a, b))
        print(f"differ {series[1][0]} vs {series[0][0]}: {differ}")
    if len(series) >= 3:
        a, c = series[0][1], series[2][1]
        differ = sum(x != y for x, y in zip(a, c))
        print(f"differ {series[2][0]} vs {series[0][0]}: {differ}")


if __name__ == "__main__":
    main()
