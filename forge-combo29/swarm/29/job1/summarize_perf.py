#!/usr/bin/env python3
"""Parse `perf report --stdio --no-children` text and aggregate samples by shared object and by
symbol family. Reads the saved raw text file; prints a table (this output is what goes in the report)."""
import re, sys, collections

path = sys.argv[1]
rows = []
pat = re.compile(r'^\s+(\d+\.\d+)%\s+(\S+)\s+(\S+)\s+\[\S\]\s+(.*)$')
with open(path) as f:
    for line in f:
        m = pat.match(line.rstrip("\n"))
        if m:
            rows.append((float(m.group(1)), m.group(2), m.group(3), m.group(4).strip()))

total = sum(r[0] for r in rows)
bysw = collections.Counter()
for pct, cmd, so, sym in rows:
    bysw[so] += pct

print("parsed symbols: %d, sum of overheads: %.2f%%" % (len(rows), total))
print()
print("| shared object | samples % |")
print("|---|---|")
for so, pct in bysw.most_common():
    print("| %s | %.2f |" % (so, pct))
print()
print("top ten symbols (exclusive):")
print()
print("| rank | symbol | % |")
print("|---|---|---|")
top = sorted(rows, reverse=True)[:10]
t10 = 0.0
for i, (pct, cmd, so, sym) in enumerate(top, 1):
    t10 += pct
    print("| %d | %s | %.2f |" % (i, sym, pct))
print()
print("top ten sum: %.2f%% of %.2f%% parsed" % (t10, total))

NNUE_KEYS = ("nnue::", "Evaluator", "evaluate_position", "RuntimePsqt", "corrected_eval", "static_evaluate")
LIBC_KEYS = ("__memset", "__memcpy", "__memmove", "malloc", "free", "_int_malloc", "page fault", "[.] ")
nnue = libc = 0.0
nnue_list, libc_list = [], []
for pct, cmd, so, sym in rows:
    if any(k in sym for k in NNUE_KEYS):
        nnue += pct; nnue_list.append((pct, sym))
    if so != "forge" and ("libc" in so or "libstdc" in so or "ld-linux" in so or "kernel" in so):
        libc += pct; libc_list.append((pct, sym))
print()
print("NNUE/eval family total: %.2f%%" % nnue)
for pct, sym in sorted(nnue_list, reverse=True):
    print("   %6.2f%%  %s" % (pct, sym))
print()
print("C/C++ runtime + kernel total: %.2f%%" % libc)
for pct, sym in sorted(libc_list, reverse=True):
    print("   %6.2f%%  %s" % (pct, sym))
print()
print("largest non-forge, non-runtime symbol: %.2f%%" % max([p for p, c, s, y in rows if s == "forge"] or [0]))
