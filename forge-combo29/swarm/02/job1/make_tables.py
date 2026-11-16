#!/usr/bin/env python3
"""S02 AREA 2 job 1 — build every table of REPORT_job1.md from the raw files only.

usage: make_tables.py <outdir>   (reads outdir/results.jsonl, outdir/meta.txt, outdir/bad/)
Every number printed here comes out of results.jsonl, which run_sequences.py wrote from the engine's
own output. Nothing is typed by hand.
"""
import json
import os
import sys

out = sys.argv[1] if len(sys.argv) > 1 else "out"
rs = [json.loads(l) for l in open(os.path.join(out, "results.jsonl"))]
n = len(rs)


def tot(k):
    return sum(r[k] for r in rs)


print("| quantity | value |")
print("|---|---|")
print("| sequences run | %d |" % n)
print("| engine processes started | %d (one fresh process per sequence) |" % n)
print("| crashes (non-zero exit, not a timeout) | %d |" % sum(r["crashed"] for r in rs))
print("| hangs (no exit within 25 s -> SIGKILL) | %d |" % sum(r["hung"] for r in rs))
print("| sanitizer lines (ASan/UBSan) | %d |" % tot("sanitizer_lines"))
print("| `go` lines sent | %d |" % tot("n_go"))
print("| `bestmove` lines seen | %d |" % tot("n_bestmove"))
print("| sequences where go/bestmove counts differ | %d |" % sum(r["unpaired"] for r in rs))
print("| sequences where at least one search was judged | %d |" % sum(1 for r in rs if r["bestmove_checked"]))
print("| illegal bestmoves | %d |" % sum(len(r["illegal_bestmoves"]) for r in rs))
print("| `bestmove 0000` on a board WITH legal moves, go without searchmoves | %d |"
      % tot("zero_no_searchmoves"))
print("| `bestmove 0000` on a board WITH legal moves, go WITH searchmoves | %d |"
      % tot("zero_with_searchmoves"))
print("| `isready` answered late/missing (`readyok` absent) | %d |" % tot("readyok_missing"))
print("| `uci` answered without `uciok` | %d |" % tot("uciok_missing"))
print("| sequences with any flag set | %d |"
      % sum(1 for r in rs if r["crashed"] or r["hung"] or r["sanitizer_lines"]
            or r["illegal_bestmoves"] or r["readyok_missing"] or r["uciok_missing"]
            or r["zero_no_searchmoves"]))
w = sorted(r["wall_s"] for r in rs)
print("| wall time per sequence: median / p99 / max (s) | %.3f / %.3f / %.3f |"
      % (w[n // 2], w[int(n * 0.99)], w[-1]))
print("| sum of all wall times (s) | %.1f |" % sum(w))
print()
print("### every sequence that set a flag (raw output in out/bad/)")
bad = [r for r in rs if r["crashed"] or r["hung"] or r["sanitizer_lines"] or r["illegal_bestmoves"]
       or r["readyok_missing"] or r["uciok_missing"] or r["zero_no_searchmoves"]]
print("count %d" % len(bad))
for r in bad:
    print("- seq %04d rc=%r hung=%s san=%d illegal=%r note=%s"
          % (r["id"], r["rc"], r["hung"], r["sanitizer_lines"],
             [x["bestmove"] for x in r["illegal_bestmoves"]], r["check_note"]))
print()
print("### the go forms that were exercised (counted from seqs.jsonl)")
import collections
forms = collections.Counter()
for rec in map(json.loads, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "seqs.jsonl"))):
    for line in rec["lines"]:
        t = line.split()
        if t[:1] == ["go"]:
            key = t[1] if len(t) > 1 else "(bare go)"
            if key in ("depth", "nodes", "movetime", "searchmoves", "mate"):
                key = key
            forms[key] += 1
for k, v in forms.most_common():
    print("- `go %s` %d" % (k, v))
