#!/usr/bin/env python3
"""o_rows.py RAW [RAW ...]
Reads harness transcripts. For each go, prints the position number and the
nodes of the last info line before bestmove. Then SUM. With two files, also
prints how many positions differ (file2 vs file1).
"""
import sys


def nodes_of(info_line):
    parts = info_line.split()
    if "nodes" not in parts:
        sys.exit(f"STOP: last info line has no nodes: {info_line}")
    return int(parts[parts.index("nodes") + 1])


def rows_of(path):
    rows = []
    in_go = False
    last_info = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith(">> "):
            cmd = line[3:]
            if cmd.startswith("go "):
                in_go = True
                last_info = None
            continue
        if not in_go:
            continue
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None:
                sys.exit(f"STOP: bestmove with no info line in {path}")
            rows.append(nodes_of(last_info))
            in_go = False
    return rows


def show(path):
    rows = rows_of(path)
    print(f"FILE {path}")
    for i, n in enumerate(rows, 1):
        print(f"{i} {n}")
    print(f"SUM {sum(rows)}")
    print(f"COUNT {len(rows)}")
    if len(rows) >= 3:
        print(f"FIRST3 {rows[0]} {rows[1]} {rows[2]}")
    return rows


def main():
    paths = sys.argv[1:]
    if not paths:
        sys.exit("usage: o_rows.py RAW [RAW ...]")
    parsed = [show(p) for p in paths]
    if len(parsed) == 2:
        a, b = parsed
        n = min(len(a), len(b))
        differ = sum(1 for i in range(n) if a[i] != b[i])
        print(f"DIFFER {differ} of {n}")
        print(f"EQUAL {differ == 0 and len(a) == len(b)}")


if __name__ == "__main__":
    main()
