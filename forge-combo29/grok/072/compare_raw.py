#!/usr/bin/env python3
"""Position-by-position node compare of two search_set.py raw files."""
import re
import sys
from pathlib import Path

def nodes(path: Path, depth: int) -> list[int]:
    text = path.read_text(errors="replace")
    rows = []
    pending = None
    depth_re = re.compile(rf"^info depth {depth}(?: multipv \d+)? .* nodes (\d+) ")
    for line in text.splitlines():
        match = depth_re.match(line)
        if match:
            pending = int(match.group(1))
        elif line.startswith("bestmove ") and pending is not None:
            rows.append(pending)
            pending = None
        elif line.startswith("bestmove "):
            rows.append(-1)
    return rows

def main() -> None:
    left = nodes(Path(sys.argv[1]), int(sys.argv[3]))
    right = nodes(Path(sys.argv[2]), int(sys.argv[3]))
    n = min(len(left), len(right))
    differ = [i for i in range(n) if left[i] != right[i]]
    print(f"left {sys.argv[1]} positions {len(left)}")
    print(f"right {sys.argv[2]} positions {len(right)}")
    print(f"compared {n}")
    print(f"differ {len(differ)} of {n}")
    print("first_diffs " + " ".join(f"{i}:{left[i]}!={right[i]}" for i in differ[:8]))

if __name__ == "__main__":
    main()
