#!/usr/bin/env python3
"""Compare my suite_nodes rows to a partner TSV (index, nodes, bestmove, fen)."""
import sys
from pathlib import Path


def mine(path: Path) -> list[tuple[str, str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith("SUM ") or not line.strip():
            continue
        index, nodes, _depth, fen = line.split(None, 3)
        rows.append((index, nodes, fen))
    return rows


def theirs(path: Path) -> list[tuple[str, str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("index") or line.startswith("SUM"):
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        rows.append((parts[0], parts[1], parts[3]))
    return rows


def main() -> int:
    left = mine(Path(sys.argv[1]))
    right = theirs(Path(sys.argv[2]))
    print(f"mine {len(left)} partner {len(right)}")
    n = min(len(left), len(right))
    differ = 0
    fen_mismatch = 0
    shown = 0
    for i in range(n):
        if left[i][2] != right[i][2]:
            fen_mismatch += 1
        if left[i][1] != right[i][1]:
            differ += 1
            if shown < 8:
                print(f"diff {left[i][0]} mine {left[i][1]} partner {right[i][1]}")
                shown += 1
    print(f"compared {n} fen_mismatch {fen_mismatch} differ {differ} equal {n - differ}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
