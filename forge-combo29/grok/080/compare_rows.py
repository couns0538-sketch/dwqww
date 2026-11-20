#!/usr/bin/env python3
"""Compare node lists. A raw engine log, or a 'index nodes' rows file."""
import sys


def from_raw(path: str) -> list[int]:
    found: list[int] = []
    current = None
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        if line.startswith("info ") and " nodes " in line:
            parts = line.split()
            current = int(parts[parts.index("nodes") + 1])
        elif line.startswith("bestmove"):
            if current is None:
                raise SystemExit(f"{path}: bestmove with no info nodes")
            found.append(current)
            current = None
    if not found:
        raise SystemExit(f"{path}: no searches")
    return found


def from_rows(path: str) -> list[int]:
    found = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("SUM "):
            continue
        parts = line.split()
        found.append(int(parts[-1]))
    return found


def load(path: str) -> list[int]:
    if path.endswith(".rows"):
        return from_rows(path)
    return from_raw(path)


def main() -> None:
    left = load(sys.argv[1])
    right = load(sys.argv[2])
    print(f"left {sys.argv[1]} count {len(left)} sum {sum(left)}")
    print(f"right {sys.argv[2]} count {len(right)} sum {sum(right)}")
    n = min(len(left), len(right))
    differ = sum(1 for i in range(n) if left[i] != right[i])
    print(f"differ {differ} of {n}")
    if len(left) != len(right):
        print(f"length mismatch {len(left)} vs {len(right)}")


if __name__ == "__main__":
    main()
