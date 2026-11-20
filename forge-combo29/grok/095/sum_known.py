#!/usr/bin/env python3
"""Print O and G depth-12 sums from harness tsv files."""
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent


def col(path: pathlib.Path) -> list[int]:
    lines = path.read_text().splitlines()[1:]
    return [int(line.split("\t")[1]) for line in lines if line.strip()]


def main() -> None:
    o_name = sys.argv[1] if len(sys.argv) > 1 else "B_O_d12.tsv"
    g_name = sys.argv[2] if len(sys.argv) > 2 else "B_G_d12.tsv"
    o = col(root / o_name)
    g = col(root / g_name)
    print(f"O_POSITIONS {len(o)}")
    print(f"O_SUM {sum(o)}")
    print(f"O_FIRST3 {o[0]} {o[1]} {o[2]}")
    print(f"O_EXPECT_SUM 9500069")
    print(f"O_EXPECT_FIRST3 41311 24872 28574")
    print(f"O_MATCH {sum(o) == 9500069 and o[:3] == [41311, 24872, 28574]}")
    print(f"G_POSITIONS {len(g)}")
    print(f"G_SUM {sum(g)}")
    print(f"G_EXPECT_SUM 18466239")
    print(f"G_MATCH {sum(g) == 18466239}")


if __name__ == "__main__":
    main()
