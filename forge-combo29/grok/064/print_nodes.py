#!/usr/bin/env python3
"""Print a node-file sum and the first three counts. Paste this output."""
import pathlib
import sys


def rows(path: pathlib.Path) -> list[tuple[str, str]]:
    out = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, move, *_ = line.split("\t")
        out.append((index, nodes, move))
    return out


def main() -> int:
    for path_s in sys.argv[1:]:
        path = pathlib.Path(path_s)
        parsed = rows(path)
        total = sum(int(nodes) for _, nodes, _ in parsed)
        first = " ".join(nodes for _, nodes, _ in parsed[:3])
        print(f"{path.name} positions {len(parsed)} sum {total} first3 {first}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
