#!/usr/bin/env python3
"""Read an O-run raw transcript. Print count, node sum, first three, and
how many positions differ from a baseline raw file when one is given.

  read_orun.py RAW [BASELINE_RAW]
"""
import re
import sys

NODE = re.compile(r"^info depth \d+ .* nodes (\d+) ")


def nodes_of(path: str) -> list[int]:
    last = None
    found: list[int] = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        match = NODE.match(line)
        if match:
            last = int(match.group(1))
            continue
        if line.startswith("bestmove "):
            if last is None:
                sys.exit(f"STOP bestmove with no info depth in {path}")
            found.append(last)
            last = None
    if len(found) != 200:
        sys.exit(f"STOP {path} has {len(found)} positions")
    return found


def main() -> None:
    got = nodes_of(sys.argv[1])
    print(f"positions {len(got)}")
    print(f"sum {sum(got)}")
    print(f"first {got[0]} {got[1]} {got[2]}")
    if len(sys.argv) > 2:
        base = nodes_of(sys.argv[2])
        differ = sum(1 for a, b in zip(got, base) if a != b)
        print(f"differ {differ}")
        same = differ == 0
        print("identical" if same else "not_identical")


if __name__ == "__main__":
    main()
