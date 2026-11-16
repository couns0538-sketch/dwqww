#!/usr/bin/env python3
"""global_by_line.py SYMBOLS_ALL ANNOTATE_HOT OUT : global self time per SOURCE EXPRESSION.

perf annotate with --stdio prints, for each instruction, that instruction's share *of its own symbol*
("percent: local period"). That is not the global share. So:

    global instruction %  =  symbol self % (from `perf report --no-children -g none`)
                             x  instruction % of that symbol / 100

This script only multiplies the two numbers perf printed and sums them by source expression. It invents no
number. Symbols the two reports don't share by exact name are reported as unmatched, not silently dropped.
"""
import re
import sys

symbols_all, annotate_hot, dst = sys.argv[1], sys.argv[2], sys.argv[3]

# 1. symbol -> global self percent, from perf report
SYMROW = re.compile(r"^\s+(\d+\.\d+)%\s+(?:\[\.\]\s+)?(.*)$")
sym_pct = {}
started = False
for line in open(symbols_all, encoding="utf-8", errors="replace"):
    if line.startswith("# Overhead"):
        started = True
        continue
    if not started:
        continue
    m = SYMROW.match(line.rstrip("\n"))
    if not m:
        continue
    pct = float(m.group(1))
    sym = re.sub(r"\s+-\s+-\s*$", "", m.group(2)).strip()
    sym_pct[sym] = pct

# 2. annotate: symbol -> [(local pct, lineno, text)]
INS = re.compile(r"^\s*(\d+\.\d+)%\s.*?<=\s*(\d+):\s*(.*)$")
per_sym = {}
cur = None
for line in open(annotate_hot, encoding="utf-8", errors="replace"):
    line = line.rstrip("\n")
    if line.startswith("## "):
        cur = line[3:].strip()
        per_sym.setdefault(cur, [])
        continue
    m = INS.match(line)
    if m and cur is not None:
        per_sym[cur].append((float(m.group(1)), int(m.group(2)), m.group(3).strip()))

matched, unmatched = 0, []
by_line = {}
for sym, rows in per_sym.items():
    if sym not in sym_pct:
        unmatched.append(sym)
        continue
    matched += 1
    weight = sym_pct[sym] / 100.0
    for local, lineno, text in rows:
        by_line.setdefault((text[:110], sym), 0.0)
        by_line[(text[:110], sym)] += weight * local

with open(dst, "w", encoding="utf-8") as fh:
    fh.write("# global self time per (source expression, symbol), computed as in this script's docstring\n")
    fh.write("# symbols matched between the two reports: %d of %d\n\n" % (matched, len(per_sym)))
    fh.write("| global self % | source line | symbol |\n|---|---|---|\n")
    for (text, sym), pct in sorted(by_line.items(), key=lambda kv: -kv[1])[:25]:
        fh.write("| {:.2f} % | `{}` | `{}` |\n".format(pct, text.replace("|", "\\|"), sym[:70]))
    if unmatched:
        fh.write("\n## symbols in the annotate report with no row in the symbol report\n")
        for s in unmatched:
            fh.write("- `{}`\n".format(s))
print("matched {} of {} symbols; wrote {}".format(matched, len(per_sym), dst))
