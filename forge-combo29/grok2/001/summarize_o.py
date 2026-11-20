#!/usr/bin/env python3
"""Read o_*.txt transcripts and print sums, first three node counts, and diffs."""
import pathlib
import sys


def rows(path):
    nodes = []
    last = None
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        if not line.startswith("<< "):
            continue
        body = line[3:]
        if body.startswith("info ") and " nodes " in body:
            parts = body.split()
            last = int(parts[parts.index("nodes") + 1])
        elif body.startswith("bestmove "):
            if last is None:
                sys.exit(f"STOP no info nodes before bestmove in {path}")
            nodes.append(last)
            last = None
    return nodes


def main():
    base = rows(sys.argv[1])
    print(f"positions {len(base)} sum {sum(base)} first {base[0]} {base[1]} {base[2]}")
    for path in sys.argv[2:]:
        got = rows(path)
        differ = sum(a != b for a, b in zip(base, got))
        if len(got) != len(base):
            differ = -1
        print(
            f"{path} positions {len(got)} sum {sum(got)} first {got[0]} {got[1]} {got[2]} differ {differ}"
        )


if __name__ == "__main__":
    main()
