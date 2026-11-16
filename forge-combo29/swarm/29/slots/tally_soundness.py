#!/usr/bin/env python3
"""Tally the PC20-vs-S14 move-soundness disagreements CORRECTLY, including mate scores.

A previous version of this tally used a regex that only matched `cp` scores, so it silently dropped the four rows
whose judgement was a mate score. That is exactly the class of bug the FIRST RULE exists to prevent, so this parser
requires EVERY `| n | ... |` row to parse, and aborts listing any row it could not read.

Score handling: the judge reports a score for the side to move AFTER the move under test, so the mover's advantage is
the negation. For mates, `mate N` for the opponent means the opponent mates in N -> mover's value is very bad; the
sign convention is applied the same way (negate), and mate magnitudes are compared as ±(100000 - N) so a mate in 1
outranks a mate in 3.
"""
import re
import sys

PATH = sys.argv[1]
rows = []
unparsed = []

CP = re.compile(r'^cp (-?\d+)$')
MATE = re.compile(r'^mate (-?\d+)$')


def value(kind, n):
    """Convert an engine score (for the side to move) into a comparable integer."""
    if kind == "cp":
        return n, ("cp", n)
    # mate n: n>0 -> we mate in n; n<0 -> we are mated in |n|
    v = 100000 - abs(n) if n > 0 else -(100000 - abs(n))
    return v, ("mate", n)


row_re = re.compile(r'^\| (\d+) \| (\S+) (cp|mate) (-?\d+) \| (\S+) (cp|mate) (-?\d+) \| (cp|mate) (-?\d+) \| (cp|mate) (-?\d+) \|$')
for line in open(PATH):
    line = line.rstrip("\n")
    if not re.match(r'^\| \d+ \|', line):
        continue
    m = row_re.match(line)
    if not m:
        unparsed.append(line)
        continue
    pos = int(m.group(1))
    v14 = value(m.group(8), int(m.group(9)))[0]
    v20 = value(m.group(10), int(m.group(11)))[0]
    # negate: score is for the side to move after our move
    rows.append((pos, m.group(2), m.group(5), -v14, -v20,
                 (m.group(3), int(m.group(4))), (m.group(6), int(m.group(7)))))

if unparsed:
    print("ABORT: could not parse these rows -- refusing to tally a subset:")
    for u in unparsed:
        print("   " + u)
    sys.exit(1)
if not rows:
    print("ABORT: no disagreement rows found")
    sys.exit(1)

better = sum(1 for r in rows if r[4] > r[3])
worse = sum(1 for r in rows if r[4] < r[3])
tie = sum(1 for r in rows if r[4] == r[3])
print(f"disagreements parsed: {len(rows)}  (every row parsed)")
print()
print("| pos | S14 mv (d-score) | PC20 mv (d-score) | S14 line | PC20 line | better |")
print("|---|---|---|---|---|---|")
for pos, m14, m20, s14, s20, d14, d20 in rows:
    w = "PC20" if s20 > s14 else ("S14" if s20 < s14 else "tie")
    def fmt(v):
        return ("mate " + str(abs(v) - 100000)) if abs(v) > 90000 else f"{v:+d}"
    print(f"| {pos} | {m14} {d14[0]} {d14[1]} | {m20} {d20[0]} {d20[1]} | {fmt(s14)} | {fmt(s20)} | {w} |")
print()
print(f"PC20's move better: {better}   S14's better: {worse}   tie: {tie}")
