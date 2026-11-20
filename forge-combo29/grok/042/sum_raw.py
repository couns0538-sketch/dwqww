#!/usr/bin/env python3
"""Print node sums from a measure.py transcript. Reads the raw file only."""
import sys
from pathlib import Path


def sums(path: Path) -> None:
    nodes = []
    pending = []
    in_go = False
    for line in path.read_text().splitlines():
        if line.startswith(">>> go "):
            in_go = True
            pending = []
            continue
        if not in_go:
            continue
        if line.startswith(">>>"):
            in_go = False
            pending = []
            continue
        pending.append(line)
        if line.startswith("bestmove "):
            found = None
            for item in pending:
                if " nodes " not in item:
                    continue
                fields = item.split()
                if "nodes" in fields:
                    found = int(fields[fields.index("nodes") + 1])
            if found is None:
                raise SystemExit(f"{path}: bestmove without nodes")
            nodes.append(found)
            in_go = False
            pending = []
    first = " ".join(str(n) for n in nodes[:3])
    print(f"{path.name} positions {len(nodes)} sum {sum(nodes)} first {first}")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        sums(Path(arg))
