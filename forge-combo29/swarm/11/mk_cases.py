#!/usr/bin/env python3
"""mk_cases.py MUTED_FENS OUT_TSV [--limit N] : id<TAB>fen<TAB>note line per mutated FEN."""
import sys

src, out = sys.argv[1], sys.argv[2]
limit = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[3] == "--limit" else None
with open(src) as f, open(out, "w") as g:
    for i, line in enumerate(f):
        if limit is not None and i >= limit:
            break
        g.write(f"{i}\t{line.rstrip()}\tmutant\n")
print("cases written to", out)
