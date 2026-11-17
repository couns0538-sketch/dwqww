#!/usr/bin/env python3
"""exe_identity_audit.py — seat 20: does every job folder record WHICH BINARY produced its numbers?

Written after S-F63: I could not re-check another seat's behavioural claim because their files carried no exe hash, and
then found the same gap in **seven of my own** job folders (job55/61/64/66/69/70/71). A setting without a binary is
half a citation.

For each job directory, report whether it records an exe sha256 (in any of its .md/.py/.json/.txt files). Jobs that
predate the rule are listed as LEGACY rather than failures — the point of the list is that a reader knows which numbers
come with an identity and which do not.

usage: exe_identity_audit.py [root]     exit 0 = every job from LEGACY_FROM onward records identity
"""
import os
import re
import sys

root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Jobs created after the rule existed. Earlier ones are LEGACY: their evidence is real but carries no binary stamp,
# and re-running them is the only way to add one (recorded rather than silently grandfathered).
LEGACY_FROM = 73

jobs = sorted([d for d in os.listdir(root) if re.fullmatch(r"job\d+", d)],
              key=lambda s: int(s[3:]))
missing_new, legacy, ok = [], [], []
for j in jobs:
    n = int(j[3:])
    d = os.path.join(root, j)
    found = False
    for dirpath, _dn, fns in os.walk(d):
        for fn in fns:
            if not fn.endswith((".md", ".py", ".json", ".txt")):
                continue
            try:
                body = open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if re.search(r"\bsha256\b", body, re.I):
                found = True
                break
        if found:
            break
    if found:
        ok.append(j)
    elif n >= LEGACY_FROM:
        missing_new.append(j)
    else:
        legacy.append(j)

print(f"job folders: {len(jobs)}")
print(f"record an exe sha256: {len(ok)}  ({', '.join(ok) if ok else 'none'})")
print()
print(f"== MISSING (job >= {LEGACY_FROM}, i.e. after the rule existed) — these are failures")
if not missing_new:
    print("  none")
for j in missing_new:
    print(f"  {j}")
print()
print(f"== LEGACY (job < {LEGACY_FROM}) — real evidence, no binary stamp; a re-run is the only way to add one")
print("  " + (", ".join(legacy) if legacy else "none"))

print()
if missing_new:
    print(f"FAIL: {len(missing_new)} post-rule job folder(s) carry no executable identity.")
    sys.exit(1)
print("CLEAN: every post-rule job folder records which binary produced its numbers.")
sys.exit(0)
