#!/usr/bin/env python3
"""o_table.py DIR
Read o_B.raw, o_P_off.raw, o_P_on.raw and print sums, first three, and diffs.
"""
import sys


def rows(path):
    nodes = []
    last_info = None
    in_go = False
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line == ">> go depth 12":
                in_go = True
                last_info = None
                continue
            if not in_go:
                continue
            if line.startswith("<< info "):
                last_info = line
                continue
            if line.startswith("<< bestmove "):
                if last_info is None or " nodes " not in last_info:
                    sys.exit(f"STOP: no info nodes before bestmove in {path}")
                parts = last_info.split()
                nodes.append(int(parts[parts.index("nodes") + 1]))
                in_go = False
                last_info = None
    return nodes


def show(label, nodes):
    print(f"{label} n={len(nodes)} sum={sum(nodes)} first={nodes[0]} {nodes[1]} {nodes[2]}")


def main():
    directory = sys.argv[1]
    base = rows(f"{directory}/o_B.raw")
    off = rows(f"{directory}/o_P_off.raw")
    on = rows(f"{directory}/o_P_on.raw")
    show("B", base)
    show("P_off", off)
    show("P_on", on)
    off_differ = sum(1 for a, b in zip(base, off) if a != b)
    on_differ = sum(1 for a, b in zip(base, on) if a != b)
    print(f"off_differ={off_differ} on_differ={on_differ}")
    print(f"off_len_match={len(base) == len(off) == 200} on_len_match={len(on) == 200}")


if __name__ == "__main__":
    main()
