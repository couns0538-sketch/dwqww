#!/usr/bin/env python3
"""Print node sums from measure_depth.py row files. Reads the raw files only."""
import sys
from pathlib import Path


def load(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, rest = line.split("\t", 2)
        rows.append((int(index), int(nodes), rest))
    return rows


def main() -> None:
    paths = [Path(arg) for arg in sys.argv[1:]]
    if len(paths) == 1:
        rows = load(paths[0])
        total = sum(nodes for _, nodes, _ in rows)
        first = [nodes for _, nodes, _ in rows[:3]]
        print(f"file={paths[0].name} n={len(rows)} sum={total} first3={first[0]}/{first[1]}/{first[2]}")
        return
    if len(paths) != 2:
        raise SystemExit("usage: sum_nodes.py FILE   or   sum_nodes.py A B")
    a = load(paths[0])
    b = load(paths[1])
    if len(a) != len(b):
        raise SystemExit(f"length {len(a)} != {len(b)}")
    differ = 0
    for (ia, na, _), (ib, nb, _) in zip(a, b):
        if ia != ib:
            raise SystemExit(f"index {ia} != {ib}")
        if na != nb:
            differ += 1
    print(
        f"a={paths[0].name} sum={sum(n for _, n, _ in a)} "
        f"b={paths[1].name} sum={sum(n for _, n, _ in b)} "
        f"n={len(a)} differ={differ}"
    )


if __name__ == "__main__":
    main()
