#!/usr/bin/env python3
"""symmetrise_psqt.py SRC DST : make every PSQT entry left-right symmetric.

For each piece type t and relative rank r, the entry at file f and the entry at file 7-f are replaced by
their average, MG and EG separately. Every other line of the table is copied unchanged. This is MY script:
it edits a COPY of the engine's table, never the original, and it is applied to a scratch worktree.
"""
import re
import sys

SRC, DST = sys.argv[1], sys.argv[2]
LINE_RE = re.compile(r"^(/\* )(\d+)( \w+)\[(\d+)\]( \*/ S\()(-?\d+)(, )(-?\d+)(\),?)\s*$")
entries = {}
lines = open(SRC).read().splitlines()
for i, line in enumerate(lines):
    m = LINE_RE.match(line)
    if m:
        name = m.group(3).strip()
        idx = int(m.group(4))
        entries[(name, idx)] = (i, int(m.group(6)), int(m.group(8)))

psqt_names = [n for (n, _) in entries if n.endswith("Psqt")]
psqt_names = sorted(set(psqt_names))
changed = 0
for name in psqt_names:
    for r in range(8):
        for f in range(4):
            a = entries.get((name, r * 8 + f))
            b = entries.get((name, r * 8 + (7 - f)))
            if a is None or b is None:
                continue
            ia, mga, ega = a
            ib, mgb, egb = b
            amg, aeg = (mga + mgb) // 2, (ega + egb) // 2
            for idx_line, new_mg, new_eg in ((ia, amg, aeg), (ib, amg, aeg)):
                old = lines[idx_line]
                m = LINE_RE.match(old)
                lines[idx_line] = (f"{m.group(1)}{m.group(2)}{m.group(3)}[{m.group(4)}]{m.group(5)}"
                                   f"{new_mg}{m.group(7)}{new_eg}{m.group(9)}")
                if lines[idx_line] != old:
                    changed += 1
with open(DST, "w") as fh:
    fh.write("\n".join(lines) + "\n")
print(f"psqt piece types {len(psqt_names)}: {psqt_names}")
print(f"table lines rewritten: {changed}")
