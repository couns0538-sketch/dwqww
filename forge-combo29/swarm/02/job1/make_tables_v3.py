#!/usr/bin/env python3
"""S02 AREA 2 job 1 (v3) — build the report's table from the committed raw records only.

usage: make_tables_v3.py <outdir>

Every number is a re-count of the per-sequence records. The script refuses to print if the record set is
not the size it should be or if a count it needs is missing — an empty or short set must never read as
"0 faults" (the failure mode seat 19 warned about).
"""
import json
import os
import sys

out = sys.argv[1] if len(sys.argv) > 1 else "out3"
path = os.path.join(out, "results.jsonl")
if not os.path.exists(path):
    sys.exit("FAIL: %s missing" % path)
rs = [json.loads(l) for l in open(path)]
EXPECTED = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
if len(rs) != EXPECTED:
    sys.exit("FAIL: %d records, expected %d" % (len(rs), EXPECTED))
for r in rs:
    for k in ("n_go", "n_bestmove", "sanitizer_lines", "missing_bestmove", "illegal", "readyok_missing",
              "uciok_missing", "zero_no_sm", "zero_sm", "no_info_bestmoves", "book_answers",
              "driver_stopped_go", "wall_s", "bad"):
        if k not in r:
            sys.exit("FAIL: record %s has no %r; refusing to build a table" % (r.get("id"), k))

n = len(rs)


def tot(k):
    return sum(r[k] for r in rs)


w = sorted(r["wall_s"] for r in rs)
print("| quantity | value |")
print("|---|---|")
print("| sequences run | %d |" % n)
print("| engine processes started | %d (one fresh process per sequence) |" % n)
print("| `go` lines sent | %d |" % tot("n_go"))
print("| `bestmove` lines received | %d |" % tot("n_bestmove"))
print("| searches with NO bestmove | %d |" % len([0 for r in rs for _ in r["missing_bestmove"]]))
print("| crashes (signal / non-zero exit) | %d |" % sum(r["crashed"] for r in rs))
print("| hangs (process alive after 5 s of quit) | %d |" % sum(r["hung"] for r in rs))
print("| sanitizer lines (ASan/UBSan) | %d |" % tot("sanitizer_lines"))
print("| illegal bestmoves | %d |" % sum(len(r["illegal"]) for r in rs))
print("| `bestmove 0000` on a board with legal moves, go WITHOUT searchmoves | %d |" % tot("zero_no_sm"))
print("| `bestmove 0000` on a board with legal moves, go WITH searchmoves (empty restriction) | %d |"
      % tot("zero_sm"))
print("| `isready` without `readyok` | %d |" % tot("readyok_missing"))
print("| `uci` without `uciok` | %d |" % tot("uciok_missing"))
print("| bestmoves with 0 preceding `info depth` lines (counted, NOT a fault) | %d |"
      % tot("no_info_bestmoves"))
print("| bestmoves answered from the built-in book | %d |" % tot("book_answers"))
print("| searches the driver had to stop itself (unbounded/ponder/opponent-clock-only) | %d |"
      % tot("driver_stopped_go"))
print("| sequences with any fault flag | %d |" % sum(1 for r in rs if r["bad"]))
print("| wall per sequence: median / p99 / max (s) | %.3f / %.3f / %.3f |"
      % (w[n // 2], w[int(n * 0.99)], w[-1]))
print()
bad = [r for r in rs if r["bad"]]
print("### sequences that set a fault flag")
print("count %d%s" % (len(bad), "" if bad else " (none; out/bad/ is empty by construction)"))
for r in bad:
    print("- seq %04d crashed=%s hung=%s san=%d illegal=%r missing=%r"
          % (r["id"], r["crashed"], r["hung"], r["sanitizer_lines"],
             [x["bestmove"] for x in r["illegal"]], [x["go"] for x in r["missing_bestmove"]]))
