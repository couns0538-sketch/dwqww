#!/usr/bin/env python3
"""Compare a measure.py transcript with the partner's nodes-then-fen rows."""
import sys
from pathlib import Path


def nodes_of_transcript(path: Path) -> list[int]:
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
    return nodes


def nodes_of_partner(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rows.append(int(line.split()[0]))
    return rows


def main() -> None:
    mine = nodes_of_transcript(Path(sys.argv[1]))
    theirs = nodes_of_partner(Path(sys.argv[2]))
    if len(mine) != len(theirs):
        raise SystemExit(f"length {len(mine)} vs {len(theirs)}")
    differ = sum(1 for a, b in zip(mine, theirs) if a != b)
    print(
        f"{Path(sys.argv[1]).name} vs {Path(sys.argv[2]).name} "
        f"positions {len(mine)} differ {differ} of {len(mine)} "
        f"sum {sum(mine)} vs {sum(theirs)}"
    )


if __name__ == "__main__":
    main()
