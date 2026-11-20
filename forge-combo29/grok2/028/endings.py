#!/usr/bin/env python3
"""endings.py DIR

Counts brace phrases in chunk_*.out and the Termination column of chunk_*.tsv.
"""
import collections
import pathlib
import re
import sys

d = pathlib.Path(sys.argv[1])
braces = collections.Counter()
terms = collections.Counter()
outs = sorted(d.glob("chunk_*.out"))
tsvs = sorted(d.glob("chunk_*.tsv"))
for path in outs:
    braces.update(re.findall(r"\{([^}]+)\}", path.read_text(encoding="utf-8", errors="replace")))
for path in tsvs:
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) != 7:
            terms["BAD_ROW"] += 1
            continue
        terms[parts[4]] += 1
print(f"out files {len(outs)} brace phrases {sum(braces.values())}")
for key, count in braces.most_common():
    print(f"{count}\t{key}")
print(f"tsv files {len(tsvs)} games {sum(terms.values())}")
for key, count in terms.most_common():
    print(f"{count}\t{key}")
