#!/usr/bin/env python3
"""Print per-position nodes, the sum, and the first three from a raw search stdout."""
import pathlib
import sys


def nodes_before_bestmove(lines):
    rows = []
    last_nodes = None
    for line in lines:
        if line.startswith("info ") and " nodes " in line:
            parts = line.split()
            last_nodes = int(parts[parts.index("nodes") + 1])
        elif line.startswith("bestmove "):
            if last_nodes is None:
                raise SystemExit(f"bestmove without a nodes line: {line}")
            rows.append(last_nodes)
            last_nodes = None
    return rows


def main():
    if len(sys.argv) != 2:
        print("usage: sum_nodes.py RAW", file=sys.stderr)
        return 2
    lines = pathlib.Path(sys.argv[1]).read_text().splitlines()
    rows = nodes_before_bestmove(lines)
    for index, nodes in enumerate(rows, start=1):
        print(f"{index} {nodes}")
    total = sum(rows)
    first = " ".join(str(n) for n in rows[:3])
    print(f"COUNT {len(rows)}")
    print(f"SUM {total}")
    print(f"FIRST3 {first}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
