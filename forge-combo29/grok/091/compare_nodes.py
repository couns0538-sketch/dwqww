#!/usr/bin/env python3
"""Compare per-position node counts from two raw search transcripts."""
import pathlib
import sys

from sum_nodes import nodes_before_bestmove


def main():
    if len(sys.argv) != 3:
        print("usage: compare_nodes.py RAW_A RAW_B", file=sys.stderr)
        return 2
    a = nodes_before_bestmove(pathlib.Path(sys.argv[1]).read_text().splitlines())
    b = nodes_before_bestmove(pathlib.Path(sys.argv[2]).read_text().splitlines())
    n = min(len(a), len(b))
    differ = [i for i in range(n) if a[i] != b[i]]
    print(f"COUNT_A {len(a)}")
    print(f"COUNT_B {len(b)}")
    print(f"COMPARED {n}")
    print(f"EQUAL {n - len(differ)}")
    print(f"DIFFER {len(differ)}")
    if len(a) != len(b):
        print("LENGTH_MISMATCH")
    for i in differ[:20]:
        print(f"POS {i + 1} A {a[i]} B {b[i]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
