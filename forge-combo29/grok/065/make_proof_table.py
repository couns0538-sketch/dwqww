#!/usr/bin/env python3
"""Read the raw result files and print the proof numbers. Nothing is typed."""
from pathlib import Path

here = Path(__file__).resolve().parent


def nodes_line(name: str) -> str:
    text = (here / name).read_text()
    found = ""
    for raw in text.splitlines():
        if raw.startswith("info string bench ") or raw.startswith("nodes "):
            found = raw
    return found


def load(name: str) -> list[int]:
    rows = (here / name).read_text().splitlines()[1:]
    return [int(row.split("\t")[1]) for row in rows]


def differ(a: str, b: str) -> tuple[int, int, int]:
    left, right = load(a), load(b)
    n = sum(x != y for x, y in zip(left, right))
    return n, sum(left), sum(right)


print("honesty B")
for name in ("honesty_b_bench11.txt", "honesty_b_bench13.txt", "honesty_b_bench16.txt", "honesty_b_perft5.txt"):
    print(nodes_line(name))
print("honesty P")
for name in ("honesty_p_bench11.txt", "honesty_p_bench13.txt", "honesty_p_bench16.txt", "honesty_p_perft5.txt"):
    print(nodes_line(name))
print("O B", sum(load("b_O_d12.tsv")), "first3", load("b_O_d12.tsv")[:3])
print("G B", sum(load("b_G_d12.tsv")))
n, sb, sp = differ("b_O_d12.tsv", "p_off_O_d12.tsv")
print(f"O off vs B differ {n} sums {sb} {sp}")
n, sb, sp = differ("b_G_d12.tsv", "p_off_G_d12.tsv")
print(f"G off vs B differ {n} sums {sb} {sp}")
n, sb, sp = differ("b_O_d12.tsv", "p_on_O_d12.tsv")
print(f"O on vs B differ {n} of {len(load('b_O_d12.tsv'))} sums {sb} {sp}")
n, sb, sp = differ("b_G_d12.tsv", "p_on_G_d12.tsv")
print(f"G on vs B differ {n} of {len(load('b_G_d12.tsv'))} sums {sb} {sp}")
id_text = (here / "honesty_p_id.txt").read_text().splitlines()
for line in id_text:
    if "IdeaS15" in line:
        print(line)
print("asan_nm", (here / "asan_nm_count.txt").read_text().strip())
print("fire")
print((here / "s15_fire_counts.txt").read_text().rstrip())
