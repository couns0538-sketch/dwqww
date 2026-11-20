#!/usr/bin/env python3
"""Print sum, first three, and how many rows differ. Reads .rows files."""
import sys
from pathlib import Path


def load(path: str) -> list[int]:
    return [int(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: compare_rows.py A.rows [B.rows]", file=sys.stderr)
        return 2
    left = load(sys.argv[1])
    print(f"file={sys.argv[1]} n={len(left)} sum={sum(left)} first3={' '.join(str(n) for n in left[:3])}")
    if len(sys.argv) == 2:
        return 0
    right = load(sys.argv[2])
    n = min(len(left), len(right))
    differ = sum(1 for i in range(n) if left[i] != right[i])
    print(f"file={sys.argv[2]} n={len(right)} sum={sum(right)} first3={' '.join(str(n) for n in right[:3])}")
    print(f"compared={n} differ={differ} length_mismatch={len(left) != len(right)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
