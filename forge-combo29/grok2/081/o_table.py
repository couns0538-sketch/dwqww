#!/usr/bin/env python3
"""Print the three O-run sums from the raw row files. Nothing is typed by hand."""
import pathlib
import sys


def load(path):
    nodes = []
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        number, count, _info = line.split("\t", 2)
        nodes.append((int(number), int(count)))
    if [n for n, _ in nodes] != list(range(1, len(nodes) + 1)):
        sys.exit(f"{path}: position numbers are not 1..{len(nodes)}")
    return [count for _, count in nodes]


def main():
    base, off, on = (load(path) for path in sys.argv[1:4])
    differ_off = sum(1 for a, b in zip(base, off) if a != b)
    differ_on = sum(1 for a, b in zip(base, on) if a != b)
    print(f"positions {len(base)} {len(off)} {len(on)}")
    print(f"B sum {sum(base)} first {base[0]} {base[1]} {base[2]}")
    print(f"OFF sum {sum(off)} first {off[0]} {off[1]} {off[2]} differ {differ_off}")
    print(f"ON sum {sum(on)} first {on[0]} {on[1]} {on[2]} differ {differ_on}")


if __name__ == "__main__":
    main()
