#!/usr/bin/env python3
"""recount56.py — seat 20, area 10 job 2.

Recount deepseek6's REPORT_deepseek6_long56.md from ITS OWN committed raw files
(no re-run of their exe): what the report says vs what the raw files support.

Inputs are fetched text dumps in ./ds6/ (written by fetch_ds6.sh from the branch
for-fable-and-opus/deepseek6-work); nothing is typed by hand into the result.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DS6 = os.path.join(HERE, "ds6")
out = []


def say(s=""):
    out.append(s)
    print(s)


def mangled(name):
    return name.replace("/", "_")


def slurp(name):
    p = os.path.join(DS6, mangled(name))
    if not os.path.exists(p):
        return None
    return open(p, encoding="utf-8", errors="replace").read()


say("== A. which files exist on the branch for tests_deepseek6_long56/")
listing = slurp("ls_long56.txt")
say(listing.strip() if listing else "(no listing)")
files = [l.strip() for l in (listing or "").splitlines() if l.strip()]
say(f"count = {len(files)}")

say()
say("== B. the raw summary file, as committed")
summary = slurp("out/fuzz56_summary.txt")
say(repr(summary))

say()
say("== C. the dict in the raw summary, parsed")
d = None
try:
    d = eval(summary.strip(), {"__builtins__": {}}, {})  # a python dict literal, no code
except Exception as e:
    say(f"parse failed: {e}")
if isinstance(d, dict):
    for k in sorted(d):
        say(f"  {k} = {d[k]}")
    say()
    say("== D. report claim vs raw summary")
    checks = [
        ("ok", "every sequence completed (ok 2000)", 2000),
        ("crashes", "ZERO crashes", 0),
        ("hangs", "ZERO hangs", 0),
        ("san", "ZERO sanitizer lines", 0),
        ("illegal", "ZERO illegal bestmoves", 0),
    ]
    for key, claim, expect in checks:
        got = d.get(key)
        verdict = "EQUAL" if got == expect else "DIFFERS"
        say(f"  {key:8s} raw={got!r:6s} report says {claim!r:45s} -> {verdict}")
    say(f"  seqs     raw={d.get('seqs')!r} (the report's own count of sequences is 2,000) -> "
        f"{'DIFFERS' if d.get('seqs') != 2000 else 'EQUAL'}  [counter never incremented]")

say()
say("== E. does the runner's legality check ever execute? (stdout 'position' branch)")
runner = slurp("fuzzuci56.py") or ""
dead = []
for i, line in enumerate(runner.splitlines(), 1):
    if "pos_line" in line:
        dead.append(f"  L{i}: {line.strip()}")
say("\n".join(dead))
say("  the assignment `pos_line = l` only fires for a stdout line starting with 'position';")
say("  `if line.startswith(\"position\")` inside the SEND loop only sets `lastpos` (the sent text).")
say("  => pos_line stays None unless the ENGINE echoes 'position' on stdout.")

say()
say("== F. sanitizer evidence present in the job folder?")
want = [".meta", "nm -C", "__asan_", "sha256", "planted"]
have = " ".join(files).lower()
for w in want:
    say(f"  {w!r:12s} in the folder listing: {w.lower() in have}")
say("  files mentioning each token in their committed content (only the 7 files are checked):")
for f in files:
    body = slurp(f) 
    if body is None:
        continue
    hits = [w for w in want if w.lower() in body.lower()]
    if hits:
        say(f"    {f}: {hits}")

say()
say("== G. is the run reproducible from the branch?")
seqfile = "/tmp/uci56_seqs.txt"
inrepo = [f for f in files if "seq" in f.lower()]
say(f"  the runner reads sequences from {seqfile}; a file with 'seq' in its name on the branch: "
    f"{inrepo if inrepo else 'NONE'}")
say(f"  folder file count = {len(files)} (report's own `ls` block names: CLAIM.txt, fuzzuci56.py,")
say("   make_uci56.py, out, PREDICTION.md, stamps.txt = 6 entries, i.e. 7 files with out/ expanded)")

say()
say("== H. the hang detector's window")
for i, line in enumerate(runner.splitlines(), 1):
    if "out[len(out) - 30:]" in line:
        say(f"  L{i}: {line.strip()}")
say("  a 30-line trailing scan is not cleared per isready: an earlier readyok can satisfy a later one.")
bad = slurp("out/bad_sequences.txt")
say(f"  out/bad_sequences.txt content = {repr(bad)} (empty => no sequence flagged)")

say()
say("== I. does the report's own `git status --short` match the folder?")
say("  report's ls block lists: CLAIM.txt fuzzuci56.py make_uci56.py out PREDICTION.md stamps.txt")
say(f"  branch listing top-level entries = "
    f"{sorted({f.split('/')[0] for f in files})}")

say()
say("== J. the brief named REPORT_deepseek6_longK.md / tests_deepseek6_longK/")
say("  grep of every path on the branch for 'longK':")
hit = slurp("ls_longK.txt") or ""
say(f"  {hit.strip() or '(none)'}")

res = os.path.join(HERE, "recount56.txt")
open(res, "w").write("\n".join(out) + "\n")
print(f"\nwritten to {res}")
