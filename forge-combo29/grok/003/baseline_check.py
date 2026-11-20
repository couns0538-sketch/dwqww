#!/usr/bin/env python3
"""Print the exe-B honesty lines and the O/G depth-12 sums from the raw result files."""
from pathlib import Path

root = Path(__file__).resolve().parent


def sum_line(name: str) -> tuple[int, int]:
    lines = (root / name).read_text(encoding="utf-8").splitlines()
    rows = [line for line in lines if line and not line.startswith("SUM")]
    total = int(lines[-1].split()[1])
    return len(rows), total


def main() -> None:
    print("file key value")
    for line in (root / "HONESTY_B.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("bench") or line.startswith("perft") or line.startswith("expect"):
            key, value = line.split("=", 1)
            print(f"HONESTY_B.txt {key} {value}")
    smoke = (root / "smoke_O_B.nodes").read_text(encoding="utf-8").splitlines()
    print("smoke_O_B.nodes first3 " + " ".join(line.split()[1] for line in smoke[:3]))
    print("smoke_O_B.nodes expect 41311 24872 28574")
    for name, expect in (("O_B.nodes", 9500069), ("G_B.nodes", 18466239)):
        count, total = sum_line(name)
        print(f"{name} positions {count} sum {total} expect {expect} {'PASS' if total == expect else 'FAIL'}")


if __name__ == "__main__":
    main()
