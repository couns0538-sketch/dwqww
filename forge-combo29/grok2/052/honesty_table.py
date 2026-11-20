#!/usr/bin/env python3
"""Print the honesty node counts from the raw engine transcripts."""
import sys


def last_matching(path, predicate):
    found = None
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            text = line.rstrip("\n")
            if predicate(text):
                found = text
    if found is None:
        raise SystemExit(f"STOP: no matching line in {path}")
    return found


def bench_nodes(path):
    line = last_matching(path, lambda text: text.startswith("info string bench "))
    parts = line.split()
    depth = parts[parts.index("depth") + 1]
    nodes = parts[parts.index("nodes") + 1]
    print(f"file {path}")
    print(f"line {line}")
    print(f"depth {depth} nodes {nodes}")
    return int(nodes)


def perft_nodes(path):
    line = last_matching(path, lambda text: text.startswith("nodes "))
    nodes = line.split()[1]
    print(f"file {path}")
    print(f"line {line}")
    print(f"nodes {nodes}")
    return int(nodes)


def main():
    expected = {
        "bench11": 312866,
        "bench13": 862329,
        "bench16": 3024920,
        "perft5": 4865609,
    }
    kind = sys.argv[1]
    path = sys.argv[2]
    if kind.startswith("bench"):
        got = bench_nodes(path)
    elif kind == "perft5":
        got = perft_nodes(path)
    else:
        raise SystemExit(f"bad kind {kind}")
    want = expected[kind]
    print(f"expected {want}")
    print(f"match {got == want}")
    if got != want:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
