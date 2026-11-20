#!/usr/bin/env python3
"""Compare node rows. Usage: compare_rows.py A.nodes B.nodes"""
import sys
from pathlib import Path


def load(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rows.append(int(line.split("\t")[1]))
    return rows


def main() -> None:
    a = load(Path(sys.argv[1]))
    b = load(Path(sys.argv[2]))
    n = min(len(a), len(b))
    differ = sum(1 for i in range(n) if a[i] != b[i])
    print(f"a={sys.argv[1]} n={len(a)} sum={sum(a)}")
    print(f"b={sys.argv[2]} n={len(b)} sum={sum(b)}")
    print(f"compared={n} differ={differ} same={n - differ}")
    if len(a) != len(b):
        print(f"length_mismatch {len(a)} {len(b)}")


if __name__ == "__main__":
    main()
