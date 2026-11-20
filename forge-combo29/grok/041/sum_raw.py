#!/usr/bin/env python3
"""Read a depth_set raw transcript and print position node counts.

Usage: sum_raw.py <raw.txt> [expected_depth]
Prints one row per finished search: index depth nodes
then SUM <n> and FIRST3 <a> <b> <c>
"""
import re
import sys

depth_nodes = re.compile(r"^info depth (\d+)\b.*\bnodes (\d+)\b")


def main() -> None:
    lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
    want = int(sys.argv[2]) if len(sys.argv) > 2 else None
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        current.append(line)
        if line.startswith("bestmove "):
            blocks.append(current)
            current = []
    rows: list[tuple[int, int, int]] = []
    for index, block in enumerate(blocks):
        found = None
        for line in block:
            match = depth_nodes.match(line)
            if match:
                found = (int(match.group(1)), int(match.group(2)))
        if found is None:
            print(f"{index} MISSING")
            continue
        depth, nodes = found
        mark = ""
        if want is not None and depth != want:
            mark = " DEPTH_MISMATCH"
        print(f"{index} {depth} {nodes}{mark}")
        rows.append((index, depth, nodes))
    total = sum(nodes for _, _, nodes in rows)
    print(f"COUNT {len(rows)}")
    print(f"SUM {total}")
    first = [str(nodes) for _, _, nodes in rows[:3]]
    print("FIRST3 " + " ".join(first))


if __name__ == "__main__":
    main()
