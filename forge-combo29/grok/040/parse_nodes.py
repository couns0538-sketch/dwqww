#!/usr/bin/env python3
"""Read a search transcript and print one node count per position, then the sum.

The node count is the nodes field of the last info line before each bestmove.
"""
import sys
from pathlib import Path

def nodes_of(info: str):
    parts = info.split()
    if "nodes" not in parts:
        return None
    return int(parts[parts.index("nodes") + 1])

def depth_of(info: str):
    parts = info.split()
    if "depth" not in parts:
        return None
    return int(parts[parts.index("depth") + 1])

def main() -> int:
    raw = Path(sys.argv[1]).read_text().splitlines()
    expect = int(sys.argv[2]) if len(sys.argv) > 2 else None
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    counts = []
    depths = []
    last_info = None
    for line in raw:
        if line.startswith(">>"):
            continue
        if line.startswith("info ") and " nodes " in line and " depth " in line:
            last_info = line
        elif line.startswith("bestmove "):
            if last_info is None:
                raise SystemExit("bestmove with no info line")
            counts.append(nodes_of(last_info))
            depths.append(depth_of(last_info))
            last_info = None
    if out is not None:
        out.write_text("\n".join(str(n) for n in counts) + "\n")
    total = sum(counts)
    first = " ".join(str(n) for n in counts[:3])
    bad_depth = sum(1 for d in depths if expect is not None and d != expect)
    print(f"positions {len(counts)} sum {total} first {first} depth_mismatch {bad_depth}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
