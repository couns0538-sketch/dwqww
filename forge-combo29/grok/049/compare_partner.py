#!/usr/bin/env python3
"""Compare my partner depth rows with seat 099's published rows and with exe B.

Partner rows are 'index nodes move fen...'. Mine are 'index nodes' plus SUM/COUNT.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def load_mine(name):
    rows = []
    for line in (ROOT / name).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("SUM") or line.startswith("COUNT"):
            continue
        index, nodes = line.split()[:2]
        rows.append(int(nodes))
    return rows


def load_partner(name):
    rows = []
    for line in (ROOT / name).read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        parts = line.split()
        rows.append(int(parts[1]))
    return rows


def report(label, left, right):
    n = min(len(left), len(right))
    differ = sum(1 for i in range(n) if left[i] != right[i])
    print(f"{label} left {len(left)} right {len(right)} compared {n} differ {differ} same {n - differ}")
    shown = 0
    for i in range(n):
        if left[i] != right[i]:
            print(f"  pos {i} left {left[i]} right {right[i]}")
            shown += 1
            if shown >= 5:
                break


def main():
    base = load_mine("o_b_d12.nodes")
    off = load_mine("partner_off_O.nodes")
    on = load_mine("partner_on_O.nodes")
    theirs = load_partner("partner099_on_O.rows.txt")
    report("off_vs_B", off, base)
    report("on_vs_partner_rows", on, theirs)
    report("on_vs_B", on, base)
    print(f"on_sum {sum(on)} partner_sum {sum(theirs)} B_sum {sum(base)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
