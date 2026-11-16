#!/usr/bin/env python3
"""hot_lines.py ANNOTATE_TXT OUT_TXT : compress `perf annotate --stdio` text to only the hot instructions.

perf annotate prints every instruction of every symbol with a leading `percent : addr: insn` and a
preceding `: <src>` comment/source line. This keeps, for each symbol, only instructions whose percent is
at or above MIN_PCT, together with that instruction's nearest source line above it. Nothing is recomputed
and nothing is added: everything printed here is text that perf printed.
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
MIN_PCT = 0.20

SYM = re.compile(r"^\s*:\s*\d+\s+([0-9a-f]+) <(.*)>:$")
INS = re.compile(r"^\s*(\d+\.\d+)\s*:\s*([0-9a-f]+):\s+(.*)$")
ANY_INS = re.compile(r"^\s*:\s*[0-9a-f]+:\s+(.*)$")
SRC = re.compile(r"^\s*:\s*(\d+)\s+(.*)$")

out = ["# only instructions at or above %.2f%% of their symbol; text copied from perf annotate" % MIN_PCT]
cur = None
last_src = ""
for line in open(src, encoding="utf-8", errors="replace"):
    line = line.rstrip("\n")
    m = SYM.match(line)
    if m:
        cur = m.group(2)
        last_src = ""
        out.append("")
        out.append("## " + cur)
        continue
    m = SRC.match(line)
    if m and not ANY_INS.match(line):
        last_src = "{}: {}".format(m.group(1), m.group(2).strip())
        continue
    m = INS.match(line)
    if m and float(m.group(1)) >= MIN_PCT:
        out.append("{:>6}% {}   <= {}".format(m.group(1), m.group(3).strip(), last_src))

with open(dst, "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) + "\n")
print("{} hot instruction lines written to {}".format(sum(1 for l in out if l.startswith(" ")), dst))
