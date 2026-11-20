#!/usr/bin/env python3
"""honesty_table.py: print the node line from each honesty raw file."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def main():
    for tag in ("B", "P"):
        for name in ("bench11", "bench13", "bench16", "perft5"):
            path = ROOT / f"honesty_{tag}_{name}.txt"
            text = path.read_text(encoding="utf-8").strip().splitlines()
            node_lines = [line for line in text if "nodes" in line]
            if not node_lines:
                sys.exit(f"{path} has no nodes line")
            print(f"{tag} {name} {node_lines[-1]}")


if __name__ == "__main__":
    main()
