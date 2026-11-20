#!/usr/bin/env python3
"""Compare two depth_set transcripts position by position.

Usage: compare_raw.py <left.txt> <right.txt>
Prints equal, differ, left_only, right_only, and the first few differing indexes.
"""
import re
import sys

pattern = re.compile(r"^info depth (\d+)\b.*\bnodes (\d+)\b")


def rows(path: str) -> list[tuple[int, int]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        current.append(line)
        if line.startswith("bestmove "):
            blocks.append(current)
            current = []
    found: list[tuple[int, int]] = []
    for block in blocks:
        last = None
        for line in block:
            match = pattern.match(line)
            if match:
                last = (int(match.group(1)), int(match.group(2)))
        if last is None:
            found.append((-1, -1))
        else:
            found.append(last)
    return found


def main() -> None:
    left = rows(sys.argv[1])
    right = rows(sys.argv[2])
    n = min(len(left), len(right))
    differ = [i for i in range(n) if left[i] != right[i]]
    print(f"left {len(left)} right {len(right)}")
    print(f"equal {n - len(differ)}")
    print(f"differ {len(differ)}")
    print(f"left_only {max(0, len(left) - n)}")
    print(f"right_only {max(0, len(right) - n)}")
    for index in differ[:8]:
        print(f"{index} left {left[index][0]} {left[index][1]} right {right[index][0]} {right[index][1]}")


if __name__ == "__main__":
    main()
