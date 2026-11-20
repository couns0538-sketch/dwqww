#!/usr/bin/env python3
"""Compare nodes from a raw transcript to a partner TSV of index, nodes, score, fen."""
import sys
from pathlib import Path

from summarize_nodes import rows_of


def partner_nodes(path: Path) -> list[int]:
    nodes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("index"):
            continue
        parts = line.split("\t")
        nodes.append(int(parts[1]))
    return nodes


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare_to_tsv.py RAW TSV", file=sys.stderr)
        return 2
    mine = rows_of(Path(sys.argv[1]).read_text(encoding="utf-8"))
    theirs = partner_nodes(Path(sys.argv[2]))
    print(f"raw_count\t{len(mine)}")
    print(f"tsv_count\t{len(theirs)}")
    if len(mine) != len(theirs):
        print("length_mismatch\tyes")
        return 1
    differ = 0
    for index, (row, other) in enumerate(zip(mine, theirs), start=1):
        if row[1] != other:
            differ += 1
            if differ <= 15:
                print(f"diff\t{index}\traw={row[1]}\ttsv={other}")
    print(f"differ\t{differ}")
    print(f"same\t{len(mine) - differ}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
