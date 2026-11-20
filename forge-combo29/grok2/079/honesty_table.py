#!/usr/bin/env python3
"""Print honesty node counts from the raw files honesty.py wrote.

  python3 honesty_table.py <dir> <tag>
"""
import os
import re
import sys

EXPECTED = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}


def bench_nodes(text, depth):
    found = re.findall(rf"info string bench depth {depth} nodes (\d+)", text)
    if len(found) != 1:
        return None
    return int(found[0])


def perft_nodes(text):
    found = re.findall(r"(?m)^nodes (\d+)$", text)
    if len(found) != 1:
        return None
    return int(found[0])


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: honesty_table.py <dir> <tag>")
    directory, tag = sys.argv[1], sys.argv[2]
    rows = [
        ("bench11", 11, "bench"),
        ("bench13", 13, "bench"),
        ("bench16", 16, "bench"),
        ("perft5", 5, "perft"),
    ]
    ok = True
    for suffix, depth, kind in rows:
        path = os.path.join(directory, f"{tag}_{suffix}.txt")
        text = open(path, encoding="utf-8").read()
        nodes = bench_nodes(text, depth) if kind == "bench" else perft_nodes(text)
        want = EXPECTED[suffix]
        flag = "ok" if nodes == want else "MISS"
        if nodes != want:
            ok = False
        print(f"{tag} {suffix} nodes {nodes} expected {want} {flag}")
    print("honesty", "ok" if ok else "MISS")


if __name__ == "__main__":
    main()
