#!/usr/bin/env python3
"""Read O-run transcripts and print sums, the first three node counts, and diffs."""
import sys
from pathlib import Path


def nodes_per_position(path):
    counts = []
    last = None
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("info depth ") and " nodes " in line:
            parts = line.split()
            last = int(parts[parts.index("nodes") + 1])
        elif line.startswith("bestmove "):
            if last is None:
                sys.exit(f"STOP {path} bestmove with no info depth")
            counts.append(last)
            last = None
    if last is not None:
        sys.exit(f"STOP {path} ended during a search")
    return counts


def main():
    specs = [
        ("o1_B", 9500069, (41311, 24872, 28574)),
        ("o2_P_off", 9500069, (41311, 24872, 28574)),
        ("o3_P_on", 9845650, (23395, 31504, 35958)),
    ]
    folder = Path(sys.argv[1])
    base = None
    for name, expect_sum, expect_three in specs:
        counts = nodes_per_position(folder / f"{name}.txt")
        total = sum(counts)
        three = tuple(counts[:3])
        print(f"{name} positions {len(counts)} sum {total} first {three[0]} {three[1]} {three[2]}")
        print(f"{name} expect_sum {expect_sum} sum_ok {total == expect_sum} first_ok {three == expect_three}")
        if name == "o1_B":
            base = counts
        else:
            differ = sum(1 for a, b in zip(base, counts) if a != b)
            print(f"{name} differ_from_o1 {differ}")
        if name == "o2_P_off":
            print(f"{name} identical_to_o1 {counts == base}")


if __name__ == "__main__":
    main()
