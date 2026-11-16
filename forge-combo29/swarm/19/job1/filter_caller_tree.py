#!/usr/bin/env python3
"""filter_caller_tree.py IN OUT : turns perf's ASCII caller tree into a compact one-line-per-frame list.

perf draws its caller tree with indentation made of '|', '-' and spaces plus a leading share.
This keeps every frame and its share, in tree order, one line per frame:

    <depth><TAB><children%><TAB><self%><TAB><symbol>

so the full tree survives as plain text a fraction of the size (no binary, nothing dropped).
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
ROW = re.compile(r"^((?:[ |]*)(?:\||)-+|\s+)(\d+\.\d+)%--(.*)$")
HDR = re.compile(r"^\s+(\d+\.\d+)%\s+(\d+\.\d+)%\s+(?:\[\.\]\s+)?(.*)$")

out = []
for line in open(src, encoding="utf-8", errors="replace"):
    line = line.rstrip("\n")
    m = HDR.match(line)
    if m:
        sym = re.sub(r"\s+-\s+-\s*$", "", m.group(3)).strip()
        out.append("0\t{}\t{}\t{}".format(m.group(1), m.group(2), sym))
        continue
    m = ROW.match(line)
    if not m:
        continue
    lead, pct, sym = m.groups()
    depth = lead.count("|") + lead.count(" ") // 4
    out.append("{}\t{}\t-\t{}".format(depth, pct, sym.strip()))

with open(dst, "w", encoding="utf-8") as fh:
    fh.write("# columns: depth <tab> children% <tab> self% <tab> symbol\n")
    fh.write("# 'depth' is the indentation perf drew; a deeper frame was called by the shallower one above it.\n")
    fh.write("\n".join(out) + "\n")
print("{} frames written to {}".format(len(out), dst))
