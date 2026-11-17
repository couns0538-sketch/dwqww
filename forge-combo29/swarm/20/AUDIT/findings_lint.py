#!/usr/bin/env python3
"""findings_lint.py — seat 20: does my own FINDINGS.md hold together?

Written after a half-failed heredoc appended a FINDINGS row, failed before writing its job file, and I re-appended:
the file ended up with the same finding TWICE, and another row kept a stale "STILL LIVE" status after its finding
was withdrawn. Both were invisible to a normal read.

Checks:
  1. duplicate finding ids — allowed ONLY when the duplicate set includes a retraction row (an add-only file keeps the
     original plus a WITHDRAWN row for it);
  2. a row whose ID CELL claims a retraction but whose status cell is a bare NEW/LIVE/ACTIVE (a real conflict);
  3. rows that do not have the 4-cell shape (id | finding | evidence | status).

Prose that merely MENTIONS a withdrawal (e.g. a finding about a withdrawal, or one that references a retracted id) is
NOT a conflict — an earlier version of this check flagged four innocent rows that way.

usage: findings_lint.py [path]     exit 0 = clean, 1 = problems
"""
import re
import sys
from collections import Counter

path = sys.argv[1] if len(sys.argv) > 1 else "forge-combo29/swarm/20/FINDINGS.md"
lines = open(path, encoding="utf-8").read().split("\n")

rows = []
shape_bad = []
for i, line in enumerate(lines, 1):
    if not line.startswith("| S-"):
        continue
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) < 4:
        shape_bad.append((i, len(cells)))
    rows.append({"line": i, "id_cell": cells[0], "status": cells[-1] if cells else "",
                 "id": re.match(r"S-[A-Z]+[0-9]+[a-z]?", cells[0]).group(0) if re.match(r"S-[A-Z]+[0-9]+[a-z]?", cells[0]) else cells[0]})

fail = 0
print(f"== {len(rows)} finding rows in {path}")

print("\n== duplicate finding ids")
counts = Counter(r["id"] for r in rows)
dups = [k for k, v in counts.items() if v > 1]
if not dups:
    print("  none")
for d in dups:
    group = [r for r in rows if r["id"] == d]
    retract = [r for r in group if re.search(r"WITHDRAWN|SUPERSEDED", r["id_cell"] + r["status"], re.I)]
    if retract:
        print(f"  ok (retraction pair): {d} appears {len(group)}x; retraction marked on line(s) "
              f"{[r['line'] for r in retract]}")
    else:
        print(f"  DUPLICATE with no retraction marker: {d} appears {len(group)}x on lines "
              f"{[r['line'] for r in group]}")
        fail = 1

print("\n== rows whose ID CELL retracts but whose status cell is a bare NEW/LIVE/ACTIVE")
conf = [r for r in rows
        if re.search(r"WITHDRAWN|SUPERSEDED", r["id_cell"], re.I)
        and re.fullmatch(r"\**\s*(NEW|LIVE|ACTIVE)\s*\**", r["status"], re.I)]
if not conf:
    print("  none")
for r in conf:
    print(f"  CONFLICT line {r['line']}: id cell retracts, status says {r['status']!r}")
    fail = 1

print("\n== rows that do not carry the 4-cell shape")
if not shape_bad:
    print("  none")
for i, n in shape_bad:
    print(f"  line {i}: only {n} cells")
    fail = 1

print("\n== retraction rows (informational — deliberate add-only entries)")
ret = [r for r in rows if re.search(r"WITHDRAWN|SUPERSEDED", r["id_cell"], re.I)]
for r in ret:
    print(f"  line {r['line']}: {r['id_cell'][:78]}")
print(f"  {len(ret)} retraction row(s)")

# --- METHOD.md structural check (added after a rule insertion silently overwrote a heading) --------------------
import os as _os
# METHOD.md lives beside THIS SCRIPT (AUDIT/), not beside FINDINGS.md — my first version looked in the wrong place
# and silently skipped the whole check, which is the same silent-skip class the check exists to catch.
method = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "METHOD.md")
if not _os.path.exists(method):
    print(f"\n  FATAL: METHOD.md not found at {method} — the structure check cannot run, refusing to report CLEAN")
    fail = 1
if _os.path.exists(method):
    print("\n== METHOD.md: duplicate section headings and list numbering")
    mlines = open(method, encoding="utf-8").read().split("\n")
    heads = [(i + 1, l[3:].strip()) for i, l in enumerate(mlines) if l.startswith("## ")]
    seen = {}
    dup_heads = 0
    for ln, h in heads:
        key = h.upper()
        if key in seen:
            print(f"  DUPLICATE heading line {ln}: {h!r} (first at line {seen[key]})")
            dup_heads += 1
        seen[key] = ln
    if not dup_heads:
        print(f"  no duplicate headings ({len(heads)} sections)")
    # numbered list must not restart or skip within a section
    num_bad = 0
    expect = 1
    for i, l in enumerate(mlines):
        m = re.match(r"^(\d+)\. \*\*", l)
        if m:
            n = int(m.group(1))
            if n != expect:
                print(f"  NUMBERING line {i+1}: expected {expect}, found {n}")
                num_bad += 1
            expect = n + 1
        elif l.startswith("## "):
            expect = 1
        elif l.strip() == "":
            pass
        elif not l.startswith((" ", "\t")):
            # a non-indented, non-list paragraph line begins a NEW list; a restart to 1 is legitimate
            expect = 1
    if not num_bad:
        print("  numbered lists are sequential within each section")
    if dup_heads or num_bad:
        fail = 1

print()
if fail == 0:
    print("CLEAN: FINDINGS.md and METHOD.md hold together.")
else:
    print("PROBLEMS FOUND (see above).")
sys.exit(fail)
