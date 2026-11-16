#!/usr/bin/env python3
"""Structural check for FINDINGS.md: every S-F row must have 7 columns, every S-C row 6.

WHY: this file is edited by string surgery, and pipes inside shell commands and maths ("grep 'a|b'",
"2|M|-1") silently split table cells. That happened four times; the table still LOOKED fine in a
terminal while being malformed as markdown. Run this after any edit.

Also verifies that no finding id is missing from the sequence S-F1..S-F<N>.
"""
import re
import sys

PATH = "FINDINGS.md"
EXPECT_F, EXPECT_C = 7, 6

rows = []
for n, line in enumerate(open(PATH), 1):
    if line.startswith("| S-"):
        cols = len(line.rstrip("\n").split("|"))
        rows.append((n, cols, line.strip()[:70]))

f_rows = [r for r in rows if re.match(r"\| S-F\d+ ", r[2])]
c_rows = [r for r in rows if re.match(r"\| S-C\d+ ", r[2])]
bad = [r for r in f_rows if r[1] != EXPECT_F] + [r for r in c_rows if r[1] != EXPECT_C]

ids = sorted(int(re.match(r"\| S-F(\d+)", r[2]).group(1)) for r in f_rows)
missing = [i for i in range(1, (max(ids) if ids else 0) + 1) if i not in ids]

print("S-F rows: %d (all %d columns: %s)" % (len(f_rows), EXPECT_F, not [r for r in f_rows if r[1] != EXPECT_F]))
print("S-C rows: %d (all %d columns: %s)" % (len(c_rows), EXPECT_C, not [r for r in c_rows if r[1] != EXPECT_C]))
print("missing ids in S-F1..S-F%d: %s" % (max(ids) if ids else 0, missing or "none"))
if bad:
    print("\nMALFORMED ROWS:")
    for n, c, txt in bad:
        print("  line %-4d %d columns: %s" % (n, c, txt))
    sys.exit(1)
if missing:
    sys.exit(1)
print("\nOK: structure intact.")
