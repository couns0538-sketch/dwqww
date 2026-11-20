#!/usr/bin/env python3
"""Read a raw search transcript and print one node row per position plus the sum."""
import sys
from pathlib import Path


def rows_of(text: str) -> list[tuple[int, int, str]]:
    rows = []
    depth = None
    nodes = None
    score = ""
    for line in text.splitlines():
        if line.startswith("info depth "):
            parts = line.split()
            if "depth" in parts and "nodes" in parts and "score" in parts:
                depth = int(parts[parts.index("depth") + 1])
                nodes = int(parts[parts.index("nodes") + 1])
                score_at = parts.index("score")
                score = parts[score_at + 1] + " " + parts[score_at + 2]
        elif line.startswith("bestmove ") and depth is not None and nodes is not None:
            rows.append((depth, nodes, score))
            depth = None
            nodes = None
            score = ""
    return rows


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: summarize_nodes.py RAW", file=sys.stderr)
        return 2
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    rows = rows_of(text)
    total = 0
    for index, (depth, nodes, score) in enumerate(rows, start=1):
        total += nodes
        print(f"{index}\t{depth}\t{nodes}\t{score}")
    print(f"count\t{len(rows)}")
    print(f"sum\t{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
