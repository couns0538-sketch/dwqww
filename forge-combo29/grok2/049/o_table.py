#!/usr/bin/env python3
"""o_table.py RAW1 RAW2 RAW3
Reads the three O-run transcripts. One row per bestmove: position number and the
nodes field of the last info line before that bestmove. Prints sums, the first
three, and how many of run 3 differ from run 1. Compares to the arm-9 table.
"""
import sys

EXPECT_1 = 9500069
EXPECT_1_HEAD = (41311, 24872, 28574)
EXPECT_3 = 9722445
EXPECT_3_HEAD = (19900, 22525, 42778)
EXPECT_3_DIFFER = 200


def nodes_of(raw_path):
    last_info = None
    out = []
    for line in open(raw_path, encoding="utf-8"):
        text = line.rstrip("\n")
        if text.startswith("info "):
            last_info = text
        elif text.startswith("bestmove"):
            if last_info is None:
                sys.exit(f"STOP: bestmove with no info line in {raw_path}")
            parts = last_info.split()
            if "nodes" not in parts:
                sys.exit(f"STOP: last info has no nodes in {raw_path}: {last_info}")
            out.append(int(parts[parts.index("nodes") + 1]))
            last_info = None
    return out


def show(label, nodes):
    head = nodes[:3]
    print(f"{label} n={len(nodes)} sum={sum(nodes)} first={head[0]} {head[1]} {head[2]}")


def main():
    a, b, c = (nodes_of(p) for p in sys.argv[1:4])
    show("B", a)
    show("Poff", b)
    show("Pon", c)
    same = sum(1 for x, y in zip(a, b) if x == y)
    differ = sum(1 for x, y in zip(a, c) if x != y)
    print(f"off_identical {same} of {len(a)}")
    print(f"on_differ {differ} of {len(a)}")
    ok1 = sum(a) == EXPECT_1 and tuple(a[:3]) == EXPECT_1_HEAD and len(a) == 200
    ok2 = a == b and len(b) == 200
    ok3 = sum(c) == EXPECT_3 and tuple(c[:3]) == EXPECT_3_HEAD and differ == EXPECT_3_DIFFER and len(c) == 200
    print(f"table_B {'MATCH' if ok1 else 'MISS'}")
    print(f"table_off {'MATCH' if ok2 else 'MISS'}")
    print(f"table_on {'MATCH' if ok3 else 'MISS'}")


if __name__ == "__main__":
    main()
