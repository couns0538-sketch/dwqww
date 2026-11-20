#!/usr/bin/env python3
"""Read a search_set raw transcript and print position nodes, the sum, and the first three."""
import sys
from pathlib import Path

def nodes_of(chunk: list[str]) -> int | None:
    found = None
    for line in chunk:
        if line.startswith("### ") or line.startswith(">>> "):
            continue
        parts = line.split()
        if "nodes" in parts:
            i = parts.index("nodes")
            if i + 1 < len(parts) and parts[i + 1].isdigit():
                found = int(parts[i + 1])
    return found

def main() -> int:
    path = Path(sys.argv[1])
    lines = path.read_text().splitlines(keepends=True)
    rows = []
    chunk = None
    for line in lines:
        if line.startswith(">>> go depth"):
            chunk = []
            continue
        if chunk is None:
            continue
        if line.startswith("bestmove "):
            n = nodes_of(chunk)
            if n is None:
                raise SystemExit("missing nodes before bestmove " + str(len(rows) + 1))
            rows.append(n)
            chunk = None
            continue
        chunk.append(line)
    if not rows:
        raise SystemExit("no searches in " + str(path))
    print("positions", len(rows))
    print("sum", sum(rows))
    print("first3", rows[0], rows[1], rows[2])
    for i, n in enumerate(rows, start=1):
        print(f"{i}\t{n}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
