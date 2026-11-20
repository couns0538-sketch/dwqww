#!/usr/bin/env python3
"""Compare node rows parsed from raw search transcripts. Prints the table."""
import sys
from pathlib import Path


def rows(path: Path):
    found = []
    pending = []
    in_go = False
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith(">> go "):
            in_go = True
            pending = []
            continue
        if not in_go:
            continue
        if line.startswith("info ") and " nodes " in line:
            parts = line.split()
            pending.append(int(parts[parts.index("nodes") + 1]))
        if line.startswith("bestmove "):
            if not pending:
                raise SystemExit(f"no nodes before bestmove in {path}")
            found.append(pending[-1])
            in_go = False
    return found


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare_raw.py LEFT.txt RIGHT.txt", file=sys.stderr)
        return 2
    left = rows(Path(sys.argv[1]))
    right = rows(Path(sys.argv[2]))
    n = min(len(left), len(right))
    differ = [i + 1 for i in range(n) if left[i] != right[i]]
    print(f"left={sys.argv[1]}")
    print(f"right={sys.argv[2]}")
    print(f"left_count={len(left)} right_count={len(right)}")
    print(f"left_sum={sum(left)} right_sum={sum(right)}")
    print(f"differ={len(differ)} of {n}")
    if len(left) != len(right):
        print("length_mismatch=yes")
    if differ[:20]:
        print("first_differ_positions=" + ",".join(str(i) for i in differ[:20]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
