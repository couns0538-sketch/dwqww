#!/usr/bin/env python3
"""Read a measure_depth raw file and print one node count per position, then the sum.

Optional second raw file: print how many positions differ.
"""
import sys
from pathlib import Path


def nodes_per_position(text: str, depth: int) -> list[int]:
    rows: list[int] = []
    current = None
    for line in text.splitlines():
        if line.startswith("info ") and " nodes " in line and f" depth {depth} " in (" " + line + " "):
            parts = line.split()
            # info depth D ... nodes N
            if "depth" in parts and "nodes" in parts:
                d_at = parts.index("depth")
                if d_at + 1 < len(parts) and parts[d_at + 1] == str(depth):
                    n_at = parts.index("nodes")
                    current = int(parts[n_at + 1])
        elif line.startswith("bestmove "):
            if current is None:
                raise SystemExit(f"bestmove without a depth {depth} info line")
            rows.append(current)
            current = None
    return rows


def main() -> int:
    depth = int(sys.argv[1])
    primary = nodes_per_position(Path(sys.argv[2]).read_text(), depth)
    print(f"count {len(primary)}")
    print(f"sum {sum(primary)}")
    if primary:
        shown = min(3, len(primary))
        print("first " + " ".join(str(primary[i]) for i in range(shown)))
    if len(sys.argv) > 3:
        other = nodes_per_position(Path(sys.argv[3]).read_text(), depth)
        n = min(len(primary), len(other))
        differ = sum(1 for i in range(n) if primary[i] != other[i])
        print(f"compared {n}")
        print(f"differ {differ}")
        if len(primary) != len(other):
            print(f"length {len(primary)} {len(other)}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
