#!/usr/bin/env python3
"""Compare my depth-12 raw file with the partner's one-number-per-line node list."""
import re
import sys
from pathlib import Path

def from_raw(path: Path, depth: int) -> list[int]:
    rows = []
    pending = None
    depth_re = re.compile(rf"^info depth {depth}(?: multipv \d+)? .* nodes (\d+) ")
    for line in path.read_text(errors="replace").splitlines():
        match = depth_re.match(line)
        if match:
            pending = int(match.group(1))
        elif line.startswith("bestmove ") and pending is not None:
            rows.append(pending)
            pending = None
        elif line.startswith("bestmove "):
            rows.append(-1)
    return rows

def from_list(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(int(line))
    return rows

mine = from_raw(Path(sys.argv[1]), int(sys.argv[3]))
theirs = from_list(Path(sys.argv[2]))
n = min(len(mine), len(theirs))
differ = [i for i in range(n) if mine[i] != theirs[i]]
print(f"mine {len(mine)} sum {sum(x for x in mine if x >= 0)}")
print(f"theirs {len(theirs)} sum {sum(theirs)}")
print(f"compared {n}")
print(f"differ {len(differ)} of {n}")
print(f"equal {len(differ) == 0 and len(mine) == len(theirs)}")
print("first_diffs " + " ".join(f"{i}:{mine[i]}!={theirs[i]}" for i in differ[:8]))
