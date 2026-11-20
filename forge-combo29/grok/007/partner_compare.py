#!/usr/bin/env python3
"""Compare my rows tsv with the partner's space-separated O rows.

My file: index, nodes, move (tab), index starting at 1.
Partner file: index, nodes, depth, cp, score, move, fen (space), index starting at 0.
Comparison is by position order, on the node count.
"""
import sys
from pathlib import Path


def main() -> int:
    mine = []
    for line in Path(sys.argv[1]).read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        mine.append(int(parts[1]))
    theirs = []
    for line in Path(sys.argv[2]).read_text().splitlines():
        if not line.strip():
            continue
        theirs.append(int(line.split()[1]))
    if len(mine) != len(theirs):
        print(f"length mine {len(mine)} partner {len(theirs)}")
        return 1
    differ = sum(1 for a, b in zip(mine, theirs) if a != b)
    print(
        f"positions {len(mine)} differ {differ} equal {len(mine) - differ} "
        f"my_sum {sum(mine)} partner_sum {sum(theirs)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
