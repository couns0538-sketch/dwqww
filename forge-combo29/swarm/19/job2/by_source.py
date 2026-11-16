#!/usr/bin/env python3
"""by_source.py ANNOTATE_HOT OUT : sums the instruction percentages of hot_instructions.txt per source line.

hot_instructions.txt lines look like

      8.14% lea ... <= 584: (attacks::rook(square, occupancy) & ...);

so the source line number and its text are already there, put there by perf annotate. This script only ADDS
those percentages up per (symbol, source line) and prints the rows above MIN_PCT.
"""
import re
import sys
from collections import OrderedDict

src, dst = sys.argv[1], sys.argv[2]
MIN_PCT = 0.30
LINE = re.compile(r"^\s*(\d+\.\d+)%\s.*?<=\s*(\d+):\s*(.*)$")

sym = None
per_sym = OrderedDict()
for line in open(src, encoding="utf-8", errors="replace"):
    line = line.rstrip("\n")
    if line.startswith("## "):
        sym = line[3:].strip()
        per_sym.setdefault(sym, OrderedDict())
        continue
    m = LINE.match(line)
    if not m or sym is None:
        continue
    pct, lineno, text = float(m.group(1)), m.group(2), m.group(3).strip()
    key = (int(lineno), text[:110])
    per_sym[sym][key] = per_sym[sym].get(key, 0.0) + pct

with open(dst, "w", encoding="utf-8") as fh:
    fh.write("# hot instruction time summed per source line, from perf annotate (only lines >= %.2f %%)\n"
             % MIN_PCT)
    for s, rows in per_sym.items():
        top = sorted(rows.items(), key=lambda kv: -kv[1])
        top = [(k, v) for k, v in top if v >= MIN_PCT]
        if not top:
            continue
        fh.write("\n## {}\n".format(s))
        fh.write("| summed % | source line | text |\n|---|---|---|\n")
        for (lineno, text), pct in top:
            fh.write("| {:.2f} % | {} | `{}` |\n".format(pct, lineno, text.replace("|", "\\|")))
print("written", dst)
