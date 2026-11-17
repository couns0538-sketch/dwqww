#!/usr/bin/env python3
"""perf_shares.py PERF_REPORT [LABEL] : the share of a symbol family in a perf report, parsed correctly.

WHY THIS EXISTS AS A FILE: a perf report's demangled symbol names WRAP onto following lines, so a naive parse that
expects "percent, then a complete symbol on the same line" silently under-counts — I got 0.96 % and 2.06 % from two
different bad parses before settling on this one. The share belongs to the line carrying the percentage; the name may
continue below it, so matching on the prefix of the name is what works.

usage: python3 perf_shares.py v3/prof/perf_report_full.txt bench13
Prints: parsed lines, accounted %, and the % for nnue:: and for the picker/generation family.
"""
import re
import sys

path = sys.argv[1]
label = sys.argv[2] if len(sys.argv) > 2 else path

# Two report formats occur: the default (percent, process, dso, [.] symbol) and `--sort symbol`
# (percent, [.] symbol). Accept both rather than maintaining two parsers.
PAT_DEFAULT = re.compile(r"\s+([\d.]+)%\s+\S+\s+\S+\s+\[[.\w]*\]\s+(.*)$")
PAT_SYMBOL = re.compile(r"\s+([\d.]+)%\s+\[[.\w]*\]\s+(.*?)\s{2,}")

rows = []
for line in open(path, errors="replace"):
    m = PAT_DEFAULT.match(line)
    if m:
        rows.append((float(m.group(1)), m.group(2)))
        continue
    m = PAT_SYMBOL.match(line)
    if m:
        rows.append((float(m.group(1)), m.group(2)))

tot = sum(p for p, _ in rows)
nnue = sum(p for p, s in rows if "nnue::" in s)
picker = sum(p for p, s in rows
             if re.search(r"MovePicker|generate_evasions|fill_pseudo_legal|is_legal_complete|see_ge|refresh_king_lines", s))
search = sum(p for p, s in rows if re.search(r"Worker::search|Worker::qsearch", s))

print(f"# {label}")
print(f"parsed_lines\t{len(rows)}")
print(f"accounted_pct\t{tot:.2f}")
print(f"nnue_pct\t{nnue:.2f}")
print(f"picker_pct\t{picker:.2f}")
print(f"search_pct\t{search:.2f}")
