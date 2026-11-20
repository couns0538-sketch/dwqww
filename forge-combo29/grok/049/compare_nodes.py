#!/usr/bin/env python3
"""Compare node rows. Prints mismatches and the on-switch difference count."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def load(name):
    rows = []
    for line in (ROOT / name).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("SUM") or line.startswith("COUNT"):
            continue
        index, nodes = line.split()
        rows.append((int(index), int(nodes)))
    return rows


def compare(left_name, right_name, label):
    left = load(left_name)
    right = load(right_name)
    if len(left) != len(right):
        print(f"{label} LENGTH {len(left)} {len(right)}")
        return
    differ = [(a[0], a[1], b[1]) for a, b in zip(left, right) if a[1] != b[1]]
    print(f"{label} positions {len(left)} differ {len(differ)} same {len(left) - len(differ)}")
    if differ[:5]:
        print(f"{label} first_diffs {differ[:5]}")


def main():
    compare("o_b_d12.nodes", "o_p_off_d12.nodes", "O_off_vs_B")
    compare("g_b_d12.nodes", "g_p_off_d12.nodes", "G_off_vs_B")
    compare("o_b_d12.nodes", "o_p_on_d12.nodes", "O_on_vs_B")
    on = load("o_p_on_d12.nodes")
    base = load("o_b_d12.nodes")
    print(f"O_on_sum {sum(n for _, n in on)}")
    print(f"O_B_sum {sum(n for _, n in base)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
