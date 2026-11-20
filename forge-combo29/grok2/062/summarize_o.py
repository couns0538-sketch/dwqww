#!/usr/bin/env python3
"""summarize_o.py RAW [RAW ...]

Reads engine transcripts. One row per bestmove: position number and the nodes
of the last info line before that bestmove. Prints the rows, the sum, and the
first three. With two or more files, also prints how many positions differ
from the first file.
"""
import sys


def nodes_of(line):
    parts = line.split()
    indexes = [i for i, part in enumerate(parts) if part == "nodes"]
    if not indexes or indexes[-1] + 1 >= len(parts):
        sys.exit(f"STOP: no nodes token in last info line: {line!r}")
    return int(parts[indexes[-1] + 1])


def rows_of(path):
    rows = []
    last_info = None
    saw_info = False
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("info "):
                last_info = line
                saw_info = True
            elif line.startswith("bestmove"):
                if not saw_info or last_info is None:
                    sys.exit(f"STOP: bestmove without an info line in {path} at position {len(rows) + 1}")
                rows.append(nodes_of(last_info))
                last_info = None
                saw_info = False
    if not rows:
        sys.exit(f"STOP: no bestmove in {path}")
    return rows


def show(path, rows):
    print(f"file {path}")
    print(f"positions {len(rows)}")
    for number, nodes in enumerate(rows, start=1):
        print(f"{number} {nodes}")
    print(f"sum {sum(rows)}")
    print("first " + " ".join(str(n) for n in rows[:3]))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    series = [(path, rows_of(path)) for path in sys.argv[1:]]
    base_path, base_rows = series[0]
    show(base_path, base_rows)
    for path, rows in series[1:]:
        print("---")
        show(path, rows)
        if len(rows) != len(base_rows):
            sys.exit(f"STOP: {path} has {len(rows)} positions, {base_path} has {len(base_rows)}")
        differ = sum(1 for a, b in zip(base_rows, rows) if a != b)
        print(f"differ_from_first {differ}")


if __name__ == "__main__":
    main()
