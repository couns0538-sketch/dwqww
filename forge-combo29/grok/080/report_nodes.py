#!/usr/bin/env python3
"""Read raw engine output and print node sums. Optional second file: position compare."""
import sys


def nodes_of(path: str) -> list[int]:
    found: list[int] = []
    current = None
    for line in open(path, encoding="utf-8"):
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


def main() -> None:
    left = nodes_of(sys.argv[1])
    print(f"file {sys.argv[1]}")
    print(f"count {len(left)}")
    print(f"sum {sum(left)}")
    head = left[:3]
    print("first " + " ".join(str(n) for n in head))
    if len(sys.argv) == 3:
        right = nodes_of(sys.argv[2])
        if len(left) != len(right):
            raise SystemExit(f"length {len(left)} vs {len(right)}")
        differ = sum(1 for a, b in zip(left, right) if a != b)
        print(f"compared {sys.argv[2]}")
        print(f"differ {differ} of {len(left)}")
        print(f"equal {differ == 0}")


if __name__ == "__main__":
    main()
