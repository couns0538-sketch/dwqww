#!/usr/bin/env python3
"""Read a depth_sum raw transcript and print one nodes row per search, then the sum."""
import sys

def main():
    path = sys.argv[1]
    rows = []
    last_nodes = None
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            text = line.rstrip("\n")
            if text.startswith(">> "):
                continue
            if text.startswith("info ") and " nodes " in text:
                parts = text.split()
                for index, part in enumerate(parts):
                    if part == "nodes" and index + 1 < len(parts):
                        last_nodes = int(parts[index + 1])
            elif text.startswith("bestmove ") and last_nodes is not None:
                rows.append(last_nodes)
                last_nodes = None
    total = sum(rows)
    print(f"positions {len(rows)}")
    print(f"sum {total}")
    for index, nodes in enumerate(rows, start=1):
        print(f"{index} {nodes}")


if __name__ == "__main__":
    main()
