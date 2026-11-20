#!/usr/bin/env python3
"""o_table.py A.txt [B.txt ...]: sum, first three node counts, and (if 2+ files) positions that differ from the first file."""
import sys


def rows(path):
    nodes = []
    current = None
    last_info = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("# position "):
            if current is not None:
                if last_info is None or " nodes " not in last_info:
                    raise SystemExit(f"STOP no nodes info for position {current} in {path}")
                nodes.append(int(last_info.split(" nodes ")[1].split()[0]))
            current = int(line.split()[2])
            last_info = None
        elif line.startswith("info ") and current is not None:
            last_info = line
        elif line.startswith("bestmove ") and current is not None:
            pass
    if current is not None:
        if last_info is None or " nodes " not in last_info:
            raise SystemExit(f"STOP no nodes info for position {current} in {path}")
        nodes.append(int(last_info.split(" nodes ")[1].split()[0]))
    return nodes


def main():
    tables = [(p, rows(p)) for p in sys.argv[1:]]
    base = tables[0][1]
    for path, nodes in tables:
        if len(nodes) != 200:
            raise SystemExit(f"STOP {path} has {len(nodes)} positions")
        differ = sum(1 for a, b in zip(base, nodes) if a != b)
        print(
            f"{path} sum {sum(nodes)} first {nodes[0]} {nodes[1]} {nodes[2]} differ_from_first {differ}"
        )


if __name__ == "__main__":
    main()
