#!/usr/bin/env python3
"""Compare one depth-sum raw file with the partner's O-on row file.

Partner rows are: index nodes bestmove fen
"""
import sys
from pathlib import Path

from table_depth import nodes_per_position


def partner_nodes(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        rows.append(int(parts[1]))
    return rows


def main() -> int:
    depth = int(sys.argv[1])
    mine = nodes_per_position(Path(sys.argv[2]).read_text(), depth)
    theirs = partner_nodes(Path(sys.argv[3]))
    n = min(len(mine), len(theirs))
    differ = sum(1 for i in range(n) if mine[i] != theirs[i])
    print(f"mine {len(mine)} sum {sum(mine)}")
    print(f"partner_rows {len(theirs)} sum {sum(theirs)}")
    print(f"compared {n}")
    print(f"differ {differ}")
    if len(mine) != len(theirs):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
