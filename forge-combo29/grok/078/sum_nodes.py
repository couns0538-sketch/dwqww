#!/usr/bin/env python3
"""Sum depth-N node counts from a depth_nodes.py raw log. Prints a table."""
import argparse
import sys
from pathlib import Path


def blocks(text: str) -> list[list[str]]:
    parts: list[list[str]] = []
    current: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("# POS "):
            if current is not None:
                parts.append(current)
            current = [line]
        elif current is not None:
            current.append(line)
    if current is not None:
        parts.append(current)
    return parts


def nodes_of(block: list[str], depth: int) -> int | None:
    found = None
    needle = f"info depth {depth} "
    for line in block:
        if line.startswith(needle) and " nodes " in line:
            parts = line.split()
            found = int(parts[parts.index("nodes") + 1])
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    text = Path(args.raw).read_text()
    rows = []
    missing = 0
    for block in blocks(text):
        got = nodes_of(block, args.depth)
        if got is None:
            missing += 1
            rows.append(None)
        else:
            rows.append(got)
    present = [n for n in rows if n is not None]
    total = sum(present)
    print(f"label {args.label}")
    print(f"positions {len(rows)}")
    print(f"missing {missing}")
    print(f"sum {total}")
    for index, value in enumerate(rows[:3]):
        print(f"first{index + 1} {value}")
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
