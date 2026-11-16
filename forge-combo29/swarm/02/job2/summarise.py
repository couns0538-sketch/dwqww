#!/usr/bin/env python3
"""S02 AREA 2 job 2 — build REPORT_job2.md's table from the committed per-run records only.

usage: summarise.py <outdir>
Exits non-zero if any expected arm file is missing: a table built from a partial set of arms would be a
quiet lie (every arm's absence would read as "0 faults").
"""
import collections
import json
import os
import sys

out = sys.argv[1] if len(sys.argv) > 1 else "out"
ARMS = ["stop", "ponderhit", "ucinewgame", "setoption_Hash", "quit"]
per = {}
for a in ARMS:
    f = os.path.join(out, "runs_%s.json" % a)
    if not os.path.exists(f):
        sys.exit("FAIL: arm file %s is missing; refusing to print a table" % f)
    rows = json.load(open(f))
    if not rows:
        sys.exit("FAIL: arm %s has no runs; an empty arm would read as 0 faults" % a)
    per[a] = rows

print("| command | runs | crashes | hung | san lines | readyok after | follow-up answered | illegal |")
print("|---|---|---|---|---|---|---|---|")
for a, rows in per.items():
    disp = a.replace("_", " ")
    print("| %s | %d | %d | %d | %d | %d | %d | %d |" % (
        disp, len(rows),
        sum(r["crashed"] for r in rows), sum(r["hung"] for r in rows),
        sum(r["sanitizer_lines"] for r in rows),
        sum(1 for r in rows if r["readyok_after"] is True),
        sum(1 for r in rows if r["followup_answered"] is True),
        sum(len(r["illegal"]) for r in rows)))
print()
ph = per["ponderhit"]
q = per["quit"]
print("ponderhit continued searching (no bestmove from the ponderhit itself): %d / %d"
      % (sum(1 for r in ph if r["continued_after_ponderhit"]), len(ph)))
print("quit exited within 5 s: %d / %d ; bestmove emitted before exit: %d"
      % (sum(1 for r in q if r["exited_after_quit"] is True), len(q),
         sum(1 for r in q if r["bestmove_after_quit"])))
st = per["stop"]
moves = collections.Counter(
    (r["interrupted_bestmove"][0].split()[1] if r["interrupted_bestmove"] else "NONE") for r in st)
print("stop arm: %d distinct bestmoves over %d runs; most common %s"
      % (len(moves), len(st), moves.most_common(3)))
