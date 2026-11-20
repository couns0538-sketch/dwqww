#!/usr/bin/env python3
"""summarize_o.py DIR

Print honesty lines and the three O runs from the raw files in DIR.
"""
import sys


def nodes_of(line):
    parts = line.split()
    if "nodes" not in parts:
        raise SystemExit("no nodes token in: " + line)
    return int(parts[parts.index("nodes") + 1])


def last_info_nodes(path):
    text = open(path, encoding="utf-8").read().splitlines()
    rows = []
    current = []
    for line in text:
        if line.startswith("bestmove "):
            info = [item for item in current if item.startswith("info ")]
            if not info:
                raise SystemExit("no info line before bestmove in " + path)
            rows.append(nodes_of(info[-1]))
            current = []
        else:
            current.append(line)
    return rows


def honesty(path, expect_substr):
    lines = open(path, encoding="utf-8").read().splitlines()
    hit = [line for line in lines if expect_substr in line]
    print("%s %s" % (path, hit[-1] if hit else "MISSING"))


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: summarize_o.py DIR")
    d = sys.argv[1].rstrip("/")
    for label in ("B", "P"):
        for tag, expect in (
            ("bench11", "nodes 312866"),
            ("bench13", "nodes 862329"),
            ("bench16", "nodes 3024920"),
            ("perft5", "nodes 4865609"),
        ):
            honesty("%s/honesty_%s_%s.txt" % (d, label, tag), expect)
    b = last_info_nodes(d + "/o_B.txt")
    off = last_info_nodes(d + "/o_Poff.txt")
    on = last_info_nodes(d + "/o_Pon.txt")
    differ_off = sum(1 for x, y in zip(b, off) if x != y)
    differ_on = sum(1 for x, y in zip(b, on) if x != y)

    def show(name, rows, differ):
        print("%s n=%d sum=%d first=%d / %d / %d differ=%d" % (
            name, len(rows), sum(rows), rows[0], rows[1], rows[2], differ))

    show("B", b, 0)
    show("Poff", off, differ_off)
    show("Pon", on, differ_on)


if __name__ == "__main__":
    main()
