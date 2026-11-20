#!/usr/bin/env python3
"""Compare two measure_depth .rows files position by position."""
import sys

def load(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        header = handle.readline()
        if not header.startswith("index\t"):
            raise SystemExit("bad header " + path)
        for line in handle:
            index, nodes, depth, fen = line.rstrip("\n").split("\t", 3)
            rows.append((int(index), int(nodes), int(depth), fen))
    return rows

def main():
    left_path, right_path = sys.argv[1], sys.argv[2]
    left, right = load(left_path), load(right_path)
    if len(left) != len(right):
        raise SystemExit(f"length {len(left)} != {len(right)}")
    differ = 0
    depth_mismatch = 0
    fen_mismatch = 0
    for a, b in zip(left, right):
        if a[3] != b[3]:
            fen_mismatch += 1
        if a[2] != b[2]:
            depth_mismatch += 1
        if a[1] != b[1]:
            differ += 1
    print(f"positions={len(left)}")
    print(f"node_differ={differ}")
    print(f"node_same={len(left) - differ}")
    print(f"depth_mismatch={depth_mismatch}")
    print(f"fen_mismatch={fen_mismatch}")
    print(f"left_sum={sum(r[1] for r in left)}")
    print(f"right_sum={sum(r[1] for r in right)}")

if __name__ == "__main__":
    main()
