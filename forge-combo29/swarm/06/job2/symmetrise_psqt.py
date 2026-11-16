#!/usr/bin/env python3
"""Make a left-right SYMMETRISED copy of src/eval_params_table.inc for a diagnostic build.

For every PSQT block (6 blocks of 64 entries, white-relative), replace entry (rank, file) with the
average of (rank, file) and (rank, 7-file), rounding toward zero. Everything outside the PSQT blocks
is left untouched. Writes the new include next to nothing else; prints a summary.

usage: symmetrise_psqt.py SRC DEST
"""
import re
import sys

src, dest = sys.argv[1:3]
lines = open(src).read().split("\n")
entries = []  # (line_index, mg, eg)
for i, line in enumerate(lines):
    m = re.search(r"S\((-?\d+),\s*(-?\d+)\)", line)
    if m:
        entries.append((i, int(m.group(1)), int(m.group(2))))

assert len(entries) >= 6 * 64, len(entries)
mg = [e[1] for e in entries]
eg = [e[2] for e in entries]
changed = 0
for t in range(6):
    base = t * 64
    for r in range(8):
        for f in range(4):
            a, b = base + r * 8 + f, base + r * 8 + (7 - f)
            for arr in (mg, eg):
                avg = int((arr[a] + arr[b]) / 2)
                if arr[a] != avg or arr[b] != avg:
                    changed += 1
                arr[a] = arr[b] = avg

for n, (i, _m, _e) in enumerate(entries):
    lines[i] = re.sub(r"S\(-?\d+,\s*-?\d+\)", "S(%d, %d)" % (mg[n], eg[n]), lines[i])

open(dest, "w").write("\n".join(lines))
print("entries=%d values_changed=%d" % (len(entries), changed))
