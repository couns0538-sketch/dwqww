#!/usr/bin/env python3
"""Print O-run sums from raw engine transcripts. Never type the table by hand.

  python3 summarize_o.py <run.txt> [<baseline.txt>]
"""
import sys


def nodes_per_position(path: str) -> list[int]:
    counts = []
    last_info = None
    seen_bestmove = 0
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove"):
            seen_bestmove += 1
            if last_info is None or " nodes " not in last_info:
                sys.exit(f"STOP: bestmove {seen_bestmove} in {path} has no info nodes line")
            parts = last_info.split()
            counts.append(int(parts[parts.index("nodes") + 1]))
            last_info = None
    if len(counts) != 200:
        sys.exit(f"STOP: {path} has {len(counts)} positions, expected 200")
    return counts


def main() -> None:
    runs = [(path, nodes_per_position(path)) for path in sys.argv[1:]]
    base = runs[0][1]
    for path, counts in runs:
        differ = sum(1 for a, b in zip(counts, base) if a != b)
        print(
            f"{path} sum {sum(counts)} first {counts[0]} {counts[1]} {counts[2]} differ_from_first_file {differ}"
        )


if __name__ == "__main__":
    main()
