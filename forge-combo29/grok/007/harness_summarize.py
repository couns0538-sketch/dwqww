#!/usr/bin/env python3
"""Print count, sum, and the first three node counts of one or more rows files."""
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: harness_summarize.py ROWS.tsv ...", file=sys.stderr)
        return 2
    for path in sys.argv[1:]:
        nodes = []
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            nodes.append(int(line.split("\t")[1]))
        first = " ".join(str(value) for value in nodes[:3])
        print(f"{path} count {len(nodes)} sum {sum(nodes)} first {first}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
