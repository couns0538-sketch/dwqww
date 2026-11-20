#!/usr/bin/env python3
"""Read a uci_search.py raw log and print node rows from the engine's own lines."""
import sys
from pathlib import Path


def nodes_before_bestmove(chunk: list[str]) -> int:
    found = None
    for line in chunk:
        if line.startswith(">>"):
            continue
        parts = line.split()
        if "nodes" not in parts:
            continue
        if "lowerbound" in parts or "upperbound" in parts:
            found = int(parts[parts.index("nodes") + 1])
            continue
        found = int(parts[parts.index("nodes") + 1])
    if found is None:
        raise SystemExit("no nodes line before bestmove")
    return found


def main() -> int:
    text = Path(sys.argv[1]).read_text().splitlines()
    label = sys.argv[2] if len(sys.argv) > 2 else Path(sys.argv[1]).name
    rows = []
    i = 0
    while i < len(text):
        if text[i].startswith(">> go "):
            chunk = []
            i += 1
            while i < len(text) and not text[i].startswith("bestmove "):
                chunk.append(text[i])
                i += 1
            if i >= len(text) or not text[i].startswith("bestmove "):
                raise SystemExit("go without bestmove")
            rows.append(nodes_before_bestmove(chunk))
        i += 1
    print(f"{label} positions {len(rows)} sum {sum(rows)}")
    if rows:
        shown = " ".join(str(n) for n in rows[:3])
        print(f"{label} first3 {shown}")
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    if out is not None:
        out.write_text("\n".join(str(n) for n in rows) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
