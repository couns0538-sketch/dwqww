#!/usr/bin/env python3
"""audit_findings.py : the pre-FINAL evidence + structure audit of FINDINGS.md.

Checks, all of which must pass:
  1. every row parses: F rows have 5 cells, C rows have 4 or 5 (the optional detail cell).
  2. every row carries at least one file path.
  3. every path RESOLVES to a file that exists in this checkout.
  4. the row count is reported so the reader can see what was covered.

Path resolution is deliberately generous (repo root, seat dir, every job and check subdirectory, one level below those)
because the rows were written at different times with different conventions — but the resolver itself carries a control:
a known-good path must resolve and a deliberately false one must NOT, printed at the top of every run. Without that
control this audit would "pass" while resolving nothing, which is instance 18 of the missing-parse family.

Run from within forge-combo29/swarm/23.
"""
import re, os, sys

HERE = os.path.abspath(os.getcwd())
ROOT = '/agent/repos/dwqww'
SEAT = 'forge-combo29/swarm/23'

prefixes = ['', './', HERE + '/', ROOT + '/', os.path.join(ROOT, SEAT) + '/']
for b in (HERE, os.path.join(ROOT, SEAT)):
    if not os.path.isdir(b):
        continue
    for j in sorted(os.listdir(b)):
        jd = os.path.join(b, j)
        if os.path.isdir(jd):
            prefixes.append(jd + '/')
            for k in sorted(os.listdir(jd)):
                if os.path.isdir(os.path.join(jd, k)):
                    prefixes.append(os.path.join(jd, k) + '/')


def resolve(c):
    c = os.path.expanduser(c)
    for pre in prefixes:
        p = os.path.normpath(pre + c)
        if os.path.exists(p):
            return p
    return None


print("== control: the resolver must find a file that exists and MISS one that does not ==")
ctl_ok = resolve('FINDINGS.md')
ctl_bad = resolve('this_file_does_not_exist_9f3a.out')
print("  FINDINGS.md ->", "RESOLVED" if ctl_ok else "NOT RESOLVED")
print("  this_file_does_not_exist_9f3a.out ->", "resolved (BAD)" if ctl_bad else "NOT resolved (correct)")
if not ctl_ok or ctl_bad:
    print("HARD FAILURE: the resolver itself is broken; no verdict below is meaningful.")
    sys.exit(2)

rows = []
for line in open('FINDINGS.md'):
    if not line.startswith('| 23-'):
        continue
    cells = [c.strip() for c in line.rstrip('\n').strip('|').split('|')]
    rows.append((cells[0], cells))

shape_bad = []
for rid, cells in rows:
    n = len(cells)
    if '-F' in rid and n != 5:
        shape_bad.append((rid, n))
    if '-C' in rid and n not in (4, 5):
        shape_bad.append((rid, n))

nopath, unresolved, resolved = [], [], []
for rid, cells in rows:
    ev = cells[2] if '-C' in rid else (cells[3] if len(cells) > 3 else '')
    cands = re.findall(r'[\w./~-]+\.(?:out|txt|json|jsonl|fens|sh|py|md|csv)', ev)
    if not cands:
        nopath.append(rid)
        continue
    hit = next((resolve(c) for c in cands if resolve(c)), None)
    if hit:
        resolved.append((rid, hit))
    else:
        unresolved.append((rid, cands[:3]))

print()
print("finding rows: %d" % len(rows))
print("rows with a file path: %d" % (len(rows) - len(nopath)))
print("rows whose path RESOLVES: %d" % len(resolved))
print("rows with NO path in the evidence cell: %d %s" % (len(nopath), nopath))
print("rows whose paths do NOT resolve: %d %s" % (len(unresolved), unresolved))
print("rows with a malformed column count: %d %s" % (len(shape_bad), shape_bad))
print()
ok = not nopath and not unresolved and not shape_bad
print("VERDICT:", "PASS — %d of %d rows parse and point at a file present in this checkout." % (len(resolved), len(rows))
      if ok else "FAIL — see the lines above.")
sys.exit(0 if ok else 1)
