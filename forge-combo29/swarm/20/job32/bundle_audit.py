#!/usr/bin/env python3
"""bundle_audit.py — seat 20 job 32: find every place my files could let a reader re-merge the PC20 bundle
with the MateAlphaGuard isolation, and report which files carry the isolation and which do not.

Task from the owner: "Keep the MateAlphaGuard result separate from any bundle claim in every file, since that is
the correction most likely to be undone by a reader skimming."

This script lists, for every text file of mine that mentions PC20 or MateAlphaGuard, whether it
  (a) contains the isolation claim explicitly (the phrase "MateAlphaGuard" together with "alone"/"ONLY"/"sufficient"),
  (b) mentions PC20 as if it were the cause,
  (c) carries the correction marker (S-F34a / "bundle").

It does not edit anything; it prints a worklist I then act on.

usage: bundle_audit.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = []


def say(s=""):
    out.append(s)
    print(s)


iso = re.compile(r"(MateAlphaGuard[^.\n]{0,80}(alone|ONLY|only|sufficient))", re.I)
risk = re.compile(r"(PC20[^.\n]{0,60}(fix|correct|repair|cure))", re.I)
fixed = re.compile(r"(S-F34a|bundle|not the cause|independent of PC20)", re.I)

say("== files of mine mentioning PC20 or MateAlphaGuard, and what they say")
say()
say(f"{'file':52s} {'has isolation':>13s} {'bundle-risk':>11s} {'carries correction':>18s}")
files = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    if "/gl" in dirpath or "/ds6" in dirpath:
        continue
    for fn in filenames:
        if not fn.endswith((".md", ".py", ".txt")):
            continue
        p = os.path.join(dirpath, fn)
        try:
            body = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if "PC20" not in body and "MateAlphaGuard" not in body:
            continue
        rel = os.path.relpath(p, ROOT)
        a = bool(iso.search(body))
        b = bool(risk.search(body))
        c = bool(fixed.search(body))
        files.append((rel, a, b, c))
        say(f"{rel:52s} {str(a):>13s} {str(b):>11s} {str(c):>18s}")

say()
say("== worklist: files that mention PC20 as a cause but do NOT carry the isolation + correction")
need = [f for f in files if f[2] and not (f[1] and f[3])]
if need:
    for rel, a, b, c in need:
        say(f"  NEEDS EDIT: {rel}  (isolation={a}, bundle-risk={b}, correction={c})")
else:
    say("  none — every file that could mislead already carries both")

say()
say("== files that carry the isolation claim")
for rel, a, b, c in files:
    if a:
        say(f"  OK: {rel}")

open(os.path.join(ROOT, "job32", "bundle_audit.txt"), "w").write("\n".join(out) + "\n")
print("\nwrote job32/bundle_audit.txt")
