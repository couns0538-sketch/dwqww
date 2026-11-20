#!/usr/bin/env python3
"""Compare node-count rows. Prints one line per check. Reads files in this folder."""

import sys
from pathlib import Path


def load(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(int(line.split()[1]))
    return rows


def main():
    folder = Path(__file__).resolve().parent
    pairs = [
        ("off_O", "B_O_depth12.nodes", "P_off_O_depth12.nodes"),
        ("off_G", "B_G_depth12.nodes", "P_off_G_depth12.nodes"),
        ("on_O", "B_O_depth12.nodes", "P_on_O_depth12.nodes"),
    ]
    for label, left_name, right_name in pairs:
        left = load(folder / left_name)
        right = load(folder / right_name)
        differ = sum(a != b for a, b in zip(left, right))
        print(f"{label} n {len(right)} differ {differ} sum {sum(right)}")
        if label == "on_O":
            shown = 0
            for index, (a, b) in enumerate(zip(left, right)):
                if a == b:
                    continue
                print(f"on_diff_pos {index} base {a} on {b}")
                shown += 1
                if shown >= 8:
                    break
    return 0


if __name__ == "__main__":
    sys.exit(main())
