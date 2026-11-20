#!/usr/bin/env python3
"""Print the node count from each honesty raw file."""
import sys
from pathlib import Path


def nodes(path: Path) -> str:
    last = None
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if "nodes" in parts:
            last = parts[parts.index("nodes") + 1]
    if last is None:
        sys.exit(f"STOP: no nodes line in {path}")
    return last


def main() -> None:
    for arg in sys.argv[1:]:
        path = Path(arg)
        print(f"{path.name} {nodes(path)}")


if __name__ == "__main__":
    main()
