#!/usr/bin/env python3
"""o_table.py B.raw OFF.raw ON.raw
Prints sum, first three, and how many ON rows differ from B. Reads raw engine output only.
"""
import re
import sys


def rows(path):
    last = None
    found = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info "):
            last = line
        elif line.startswith("bestmove"):
            if last is None:
                sys.exit(f"STOP: bestmove {len(found) + 1} in {path} has no info line")
            match = re.search(r" nodes (\d+)", last)
            if not match:
                sys.exit(f"STOP: last info before bestmove {len(found) + 1} in {path} has no nodes: {last}")
            found.append(int(match.group(1)))
            last = None
    return found


def show(name, nums):
    print(f"{name} n={len(nums)} sum={sum(nums)} first={nums[0]} {nums[1]} {nums[2]}")


def main():
    b, off, on = (rows(p) for p in sys.argv[1:4])
    if not (len(b) == len(off) == len(on) == 200):
        sys.exit(f"STOP: expected 200 rows, got {len(b)} {len(off)} {len(on)}")
    show("B", b)
    show("OFF", off)
    show("ON", on)
    off_diff = sum(x != y for x, y in zip(b, off))
    on_diff = sum(x != y for x, y in zip(b, on))
    print(f"OFF positions differing from B: {off_diff}")
    print(f"ON positions differing from B: {on_diff}")


if __name__ == "__main__":
    main()
