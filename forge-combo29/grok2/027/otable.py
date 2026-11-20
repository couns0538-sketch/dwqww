#!/usr/bin/env python3
"""otable.py DIR
Read the three raw O transcripts and print sums, first three, and differences.
"""
import sys
from pathlib import Path

DIR = Path(sys.argv[1])
EXPECT_B = (9500069, (41311, 24872, 28574))
EXPECT_ON = (8921190, (24693, 26341, 35070), 200)


def nodes_of(path):
    counts = []
    last = None
    bestmoves = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("info ") and " nodes " in line and not line.startswith("info string"):
            last = int(line.split(" nodes ", 1)[1].split()[0])
        elif line.startswith("bestmove "):
            bestmoves += 1
            if last is None:
                raise SystemExit(f"STOP: bestmove with no info nodes in {path}")
            counts.append(last)
            last = None
    if bestmoves != 200 or len(counts) != 200:
        raise SystemExit(f"STOP: {path} bestmoves {bestmoves} rows {len(counts)}")
    return counts


def show(label, counts):
    print(f"{label} sum {sum(counts)} first {counts[0]} {counts[1]} {counts[2]}")
    return counts


base = show("B", nodes_of(DIR / "o_b.txt"))
off = show("Poff", nodes_of(DIR / "o_poff.txt"))
on = show("Pon", nodes_of(DIR / "o_pon.txt"))
same_off = sum(1 for a, b in zip(base, off) if a == b)
differ_on = sum(1 for a, b in zip(base, on) if a != b)
print(f"Poff identical {same_off} of 200")
print(f"Pon differ {differ_on} of 200")
b_sum, b_first = EXPECT_B
on_sum, on_first, on_differ = EXPECT_ON
print(
    "B expect sum {0} first {1} {2} {3} {4}".format(
        b_sum, b_first[0], b_first[1], b_first[2],
        "MATCH" if (sum(base), tuple(base[:3])) == (b_sum, b_first) else "MISS",
    )
)
print(
    "Pon expect sum {0} first {1} {2} {3} differ {4} {5}".format(
        on_sum, on_first[0], on_first[1], on_first[2], on_differ,
        "MATCH" if (sum(on), tuple(on[:3]), differ_on) == (on_sum, on_first, on_differ) else "MISS",
    )
)
