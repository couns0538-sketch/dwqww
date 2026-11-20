#!/usr/bin/env python3
"""Compare two harness tsv files position by position."""
import pathlib
import sys

def load(path: pathlib.Path) -> list[tuple[int, str, str]]:
    rows = []
    for line in path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        index, nodes, best, fen = line.split("\t", 3)
        rows.append((int(nodes), best, fen))
    return rows

def main() -> None:
    left = load(pathlib.Path(sys.argv[1]))
    right = load(pathlib.Path(sys.argv[2]))
    n = min(len(left), len(right))
    differ = 0
    first = []
    for i in range(n):
        if left[i][0] != right[i][0] or left[i][1] != right[i][1]:
            differ += 1
            if len(first) < 5:
                first.append(f"{i}\t{left[i][0]}\t{right[i][0]}\t{left[i][1]}\t{right[i][1]}")
    print(f"LEFT {sys.argv[1]} N {len(left)} SUM {sum(r[0] for r in left)}")
    print(f"RIGHT {sys.argv[2]} N {len(right)} SUM {sum(r[0] for r in right)}")
    print(f"COMPARED {n}")
    print(f"DIFFER {differ}")
    print(f"SAME {n - differ}")
    print("FIRST_DIFFS index left_nodes right_nodes left_move right_move")
    for row in first:
        print(row)

if __name__ == "__main__":
    main()
