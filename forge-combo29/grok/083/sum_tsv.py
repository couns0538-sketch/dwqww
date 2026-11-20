#!/usr/bin/env python3
"""Print a node-sum table from search_set tsv files. Reads the files; does not retype numbers."""
import sys
from pathlib import Path


def rows(path: Path):
    out = []
    for line in path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        index, nodes, score, fen = line.split("\t", 3)
        out.append((int(index), int(nodes), score, fen))
    return out


def main() -> None:
    print("file\tpositions\tsum\tfirst3")
    for name in sys.argv[1:]:
        path = Path(name)
        data = rows(path)
        first = " ".join(str(nodes) for _, nodes, _, _ in data[:3])
        print(f"{path.name}\t{len(data)}\t{sum(nodes for _, nodes, _, _ in data)}\t{first}")


if __name__ == "__main__":
    main()
