#!/usr/bin/env python3
"""deepseek6 long 25: compare two rows files position by position.

Prints "N of N equal" when the node counts AND best moves agree on every row, otherwise
prints the FIRST position that differs with both rows, and the count of differing rows.

usage: cmp_rows.py <rows A> <rows B>
exit 0 = all equal, 1 = a difference, 2 = the files cannot be compared (row count differs)
"""
import sys

a_path, b_path = sys.argv[1], sys.argv[2]


def load(p):
    rows = []
    for line in open(p):
        line = line.rstrip("\n")
        if line:
            rows.append(line.split("|"))
    return rows


A, B = load(a_path), load(b_path)
if len(A) != len(B):
    print("CANNOT COMPARE: %s has %d rows, %s has %d rows" % (a_path, len(A), b_path, len(B)))
    sys.exit(2)

diff = 0
first = None
for i, (ra, rb) in enumerate(zip(A, B), 1):
    if ra[1] != rb[1] or ra[2] != rb[2]:
        diff += 1
        if first is None:
            first = (i, ra, rb)

if diff == 0:
    print("%d of %d equal" % (len(A), len(A)))
    sys.exit(0)

row, ra, rb = first
print("%d of %d equal; first difference at row %d" % (len(A) - diff, len(A), row))
print("  A (%s): nodes=%s bestmove=%s" % (a_path, ra[1], ra[2]))
print("  B (%s): nodes=%s bestmove=%s" % (b_path, rb[1], rb[2]))
sys.exit(1)
