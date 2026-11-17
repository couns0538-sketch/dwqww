#!/usr/bin/env python3
"""sync_counts.py : rewrite the FINAL's stated counts from FINDINGS.md. Run this after adding a row.

The fourth time the gate blocked a commit because the row being added incremented the count the FINAL quotes. Each time
the repair was the same manual recompute, so it is now a script — the check that catches it and the repair it demands
belong together (23-F181's adjacency, applied to tooling).
"""
import io, re, subprocess

rows = [l for l in io.open('FINDINGS.md', encoding='utf-8').read().split('\n') if l.startswith('| 23-')]
ids = [l.split('|')[1].strip() for l in rows]
nf = sum(1 for i in ids if '-F' in i)
nc = sum(1 for i in ids if '-C' in i)
nt = len(ids)
stamp = subprocess.run(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], capture_output=True, text=True).stdout.strip()

p = 'FINAL_CHAIN_LINE.txt'
s = io.open(p, encoding='utf-8').read()
s = re.sub(r"\*\*\d+ `F` rows are this seat's own findings; \d+ `C` rows are confirmations of OTHER seats' findings; \d+ rows in total\.\*\*",
           "**%d `F` rows are this seat's own findings; %d `C` rows are confirmations of OTHER seats' findings; %d rows in total.**" % (nf, nc, nt), s)
s = re.sub(r'\*\*\d+ distinct rows at [0-9TZ:\-]+\*\* — \d+ `F`', "**%d distinct rows at %s** — %d `F`" % (nt, stamp, nf), s)
s = re.sub(r'So "\d+ rows, 0 duplicates" is a claim', 'So "%d rows, 0 duplicates" is a claim' % nt, s)
io.open(p, 'w', encoding='utf-8').write(s)
print("synced: %d F + %d C = %d rows at %s" % (nf, nc, nt, stamp))
