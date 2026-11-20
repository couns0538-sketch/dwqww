#!/usr/bin/env python3
"""Compare my partner-build rows with exe B and with the partner's claimed rows."""
import sys
from pathlib import Path


def load_mine(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        index, nodes = line.split()[:2]
        rows.append(int(nodes))
    return rows


def load_claimed(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        rows.append(int(parts[1]))
    return rows


def report(name, left, right):
    n = min(len(left), len(right))
    differ = sum(1 for i in range(n) if left[i] != right[i])
    print(f"{name} left_n {len(left)} right_n {len(right)} compared {n} differ {differ}")
    print(f"{name} left_sum {sum(left)} right_sum {sum(right)}")


def main():
    mine_off = load_mine(sys.argv[1])
    base = load_mine(sys.argv[2])
    mine_on = load_mine(sys.argv[3])
    claimed = load_claimed(sys.argv[4])
    report("off_vs_B", mine_off, base)
    report("on_vs_claimed", mine_on, claimed)
    report("on_vs_B", mine_on, base)


if __name__ == "__main__":
    main()
