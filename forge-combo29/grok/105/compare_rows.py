#!/usr/bin/env python3
"""Compare node columns of two .rows files. Prints a one-line result."""
import pathlib
import sys


def load(path: pathlib.Path) -> dict:
    rows = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split()
        rows[int(parts[0])] = int(parts[1])
    return rows


def main() -> None:
    left = load(pathlib.Path(sys.argv[1]))
    right = load(pathlib.Path(sys.argv[2]))
    keys = sorted(set(left) | set(right))
    differ = [key for key in keys if left.get(key) != right.get(key)]
    print(
        f"left={sys.argv[1]} right={sys.argv[2]} n={len(keys)} "
        f"differ={len(differ)} of {len(keys)}"
    )
    if differ[:8]:
        print("first_diffs " + " ".join(str(key) for key in differ[:8]))


if __name__ == "__main__":
    main()
