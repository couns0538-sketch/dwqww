#!/usr/bin/env python3
"""Print bench and perft node counts from raw honesty transcripts.

Usage: python3 summarize_honesty.py <dir>
"""
import sys
from pathlib import Path

EXPECTED = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}


def nodes_of(path, kind):
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if kind.startswith("bench"):
        for line in text:
            if line.startswith("info string bench depth "):
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
    else:
        for line in reversed(text):
            if line.startswith("nodes ") and line[6:].isdigit():
                return int(line.split()[1])
    sys.exit(f"STOP: no nodes line in {path}")


def main():
    folder = Path(sys.argv[1])
    for tag in ("B", "P"):
        for kind, expected in EXPECTED.items():
            path = folder / f"honesty_{tag}_{kind}.txt"
            got = nodes_of(path, kind)
            status = "OK" if got == expected else "MISS"
            print(f"{tag} {kind} nodes {got} expected {expected} {status}")


if __name__ == "__main__":
    main()
