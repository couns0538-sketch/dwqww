#!/usr/bin/env python3
"""o_table.py RAW [RAW_B]

Print one row per position: number and nodes of the last info line before
each bestmove. With a second raw file, also count positions whose nodes
differ from that file (same position number).
"""
import sys


def nodes_of(raw_path):
    text = open(raw_path, encoding="utf-8", errors="replace").read().splitlines()
    rows = []
    last_info = None
    for line in text:
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None or " nodes " not in last_info:
                raise SystemExit(f"STOP: no nodes on last info before bestmove {len(rows) + 1} in {raw_path}: {last_info}")
            parts = last_info.split()
            try:
                nodes = int(parts[parts.index("nodes") + 1])
            except (ValueError, IndexError) as exc:
                raise SystemExit(f"STOP: nodes parse {raw_path}: {last_info}") from exc
            rows.append(nodes)
            last_info = None
    if len(rows) != 200:
        raise SystemExit(f"STOP: {raw_path} has {len(rows)} positions")
    return rows


def show(path):
    rows = nodes_of(path)
    print(f"file {path}")
    print(f"sum {sum(rows)}")
    print(f"first3 {rows[0]} {rows[1]} {rows[2]}")
    return rows


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: o_table.py RAW [RAW_B]")
    rows = show(sys.argv[1])
    if len(sys.argv) > 2:
        base = nodes_of(sys.argv[2])
        differ = sum(1 for a, b in zip(rows, base) if a != b)
        print(f"differ_from {sys.argv[2]} {differ}")
        same = sum(1 for a, b in zip(rows, base) if a == b)
        print(f"equal {same}")


if __name__ == "__main__":
    main()
