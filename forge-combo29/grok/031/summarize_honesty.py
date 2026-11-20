#!/usr/bin/env python3
"""Print the honesty node lines from the raw bench and perft transcripts."""
import sys
from pathlib import Path


def main() -> int:
    folder = Path(sys.argv[1])
    tag = sys.argv[2]
    for name in ("bench11", "bench13", "bench16", "perft5"):
        text = (folder / f"honesty_{tag}_{name}.txt").read_text().splitlines()
        if name.startswith("bench"):
            chosen = [line for line in text if line.startswith("info string bench ")]
        else:
            chosen = [line for line in text if line.startswith("nodes ")]
        print(f"{tag} {name}")
        for line in chosen:
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
