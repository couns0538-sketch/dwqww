#!/usr/bin/env python3
"""Print per-position nodes and their sum from a depth_run.py raw file."""
import re
import sys

nodes_re = re.compile(r"\bnodes (\d+)")


def main() -> None:
    path = sys.argv[1]
    text = open(path, encoding="utf-8").read().splitlines()
    rows = []
    current = None
    last_nodes = None
    for line in text:
        if line.startswith("### position "):
            current = int(line.split()[2])
            last_nodes = None
            continue
        if line.startswith(">>> go "):
            last_nodes = None
            continue
        if line.startswith("<<< ") and current is not None:
            body = line[4:]
            found = nodes_re.findall(body)
            if found and not body.startswith("bestmove"):
                last_nodes = int(found[-1])
            if body.startswith("bestmove ") and last_nodes is not None:
                rows.append((current, last_nodes))
                current = None
                last_nodes = None
    total = sum(n for _, n in rows)
    print(f"positions {len(rows)}")
    print(f"sum {total}")
    show = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    for index, nodes in rows[:show]:
        print(f"{index} {nodes}")
    if len(sys.argv) > 3 and sys.argv[3] == "all":
        for index, nodes in rows:
            print(f"{index} {nodes}")


if __name__ == "__main__":
    main()
