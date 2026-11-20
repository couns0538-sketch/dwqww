#!/usr/bin/env python3
"""Read o_B.txt, o_Poff.txt, o_Pon.txt and print the STEP 2 table."""
from pathlib import Path

OUT = Path(__file__).resolve().parent


def load(name):
    rows = []
    for line in (OUT / name).read_text(encoding="utf-8").splitlines():
        i, n, _info = line.split("\t", 2)
        rows.append((int(i), int(n)))
    return rows


def main():
    b = load("o_B.txt")
    off = load("o_Poff.txt")
    on = load("o_Pon.txt")
    if [i for i, _ in b] != list(range(1, 201)):
        raise SystemExit("STOP: B rows are not 1..200")
    same = sum(1 for (i, nb), (j, no) in zip(b, off) if i == j and nb == no)
    differ = sum(1 for (_i, nb), (_j, no) in zip(b, on) if nb != no)
    def show(tag, rows):
        total = sum(n for _, n in rows)
        a, b3, c = rows[0][1], rows[1][1], rows[2][1]
        print(f"{tag} sum {total} first {a} {b3} {c}")
    show("B", b)
    show("Poff", off)
    show("Pon", on)
    print(f"Poff identical to B: {same} of {len(b)}")
    print(f"Pon positions differing from B: {differ} of {len(b)}")


if __name__ == "__main__":
    main()
