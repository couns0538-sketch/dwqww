#!/usr/bin/env python3
"""Read a raw search transcript and print one nodes value per go, then the sum."""
import sys
from pathlib import Path


def nodes_of(text: str) -> list[int]:
    values = []
    pending = None
    for line in text.splitlines():
        if line.startswith("info ") and " nodes " in line:
            parts = line.split()
            pending = int(parts[parts.index("nodes") + 1])
        elif line.startswith("bestmove "):
            if pending is None:
                raise SystemExit(f"bestmove without info nodes: {line}")
            values.append(pending)
            pending = None
    return values


def main() -> int:
    path = Path(sys.argv[1])
    values = nodes_of(path.read_text())
    print(f"positions {len(values)}")
    print(f"sum {sum(values)}")
    head = " ".join(str(v) for v in values[:3])
    print(f"first3 {head}")
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text("\n".join(str(v) for v in values) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
