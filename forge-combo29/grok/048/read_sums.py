#!/usr/bin/env python3
"""Print node sums from measure_set raw files. Reads the engine output only."""
import sys
from pathlib import Path


def sums(path: Path, depth: int) -> tuple[int, int, list[int]]:
    lines = path.read_text().splitlines()
    try:
        start = lines.index("engine_output:") + 1
    except ValueError:
        start = 0
    rows: list[int] = []
    current: int | None = None
    for line in lines[start:]:
        if line.startswith("info depth "):
            parts = line.split()
            if "nodes" not in parts:
                continue
            try:
                shown = int(parts[2])
            except ValueError:
                continue
            if shown == depth:
                current = int(parts[parts.index("nodes") + 1])
        elif line.startswith("bestmove ") and current is not None:
            rows.append(current)
            current = None
    return len(rows), sum(rows), rows


def main() -> None:
    depth = 12
    for arg in sys.argv[1:]:
        path = Path(arg)
        count, total, rows = sums(path, depth)
        head = " ".join(str(n) for n in rows[:3])
        print(f"{path.name} positions {count} sum {total} first3 {head}")


if __name__ == "__main__":
    main()
