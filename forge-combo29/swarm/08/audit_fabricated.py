#!/usr/bin/env python3
"""audit_fabricated.py — audit EVERY raw timing file this seat committed against the
"fabricated bestmove" signature seat 19 reported (finding 19-F12):
a pipelined harness that sends `quit` while a search runs gets `bestmove a2a3` with ZERO info lines.

For each jsonl record I have the bestmove and the number of stdout lines read between `go` and `bestmove`
(the field `nlines`). A real search always prints at least one `info depth` line, so nlines >= 1. A fabricated
answer prints only the bare `bestmove` line, so nlines == 1 ... unless the search legitimately produced nothing
(the book answer, the reserve-empty emergency branch, or `go nodes 0`).

This script prints, per file: records, records with nlines <= 1, how many of those are a2a3, and the wall-time
range of the suspicious ones. A file is CLEAN when every a2a3-with-no-info record has a wall time consistent
with a real reason (book / tiny budget), which I then check individually.
"""
import glob
import json
import os
import sys

import chess

root = sys.argv[1] if len(sys.argv) > 1 else "."
files = sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True))

print("| file | records | nlines<=1 | of those a2a3 | their wall ms (min-max) | any a2a3 with wall > 5 ms |")
print("|---|---|---|---|---|---|")
total_suspicious_hard = 0
for f in files:
    recs = []
    for l in open(f):
        l = l.strip()
        if not l:
            continue
        try:
            recs.append(json.loads(l))
        except Exception:
            print("| %s | UNREADABLE line | | | | |" % f)
            break
    if not recs:
        continue
    if "nlines" not in recs[0]:
        print("| %s | %d | (no nlines field - not a timing file) | | | |" % (f, len(recs)))
        continue
    few = [r for r in recs if r.get("nlines", 99) <= 1]
    a2a3 = [r for r in few if r["bestmove"].strip().lower() == "bestmove a2a3" or r["bestmove"].strip().lower() == "a2a3"]
    hard = [r for r in a2a3 if r["wall_ms"] > 5.0]
    total_suspicious_hard += len(hard)
    w = [r["wall_ms"] for r in a2a3]
    print("| %s | %d | %d | %d | %s | %d |" %
          (os.path.relpath(f, root), len(recs), len(few), len(a2a3),
           ("%.2f - %.2f" % (min(w), max(w))) if w else "-", len(hard)))

print()
print("### the individual a2a3-with-no-info records and what position they were")
print("| file | i | wall ms | fen | legal moves | a2a3 legal? | plausible real reason |")
print("|---|---|---|---|---|---|---|")
for f in files:
    recs = [json.loads(l) for l in open(f) if l.strip() and '"nlines"' in l]
    for r in recs:
        if r.get("nlines", 99) <= 1 and r["bestmove"].replace("bestmove ", "").strip() == "a2a3":
            try:
                b = chess.Board(r["fen"])
                nm = b.legal_moves.count()
                legal = chess.Move.from_uci("a2a3") in b.legal_moves
            except Exception:
                nm, legal = -1, False
            reason = ""
            if nm <= 0:
                reason = "no legal moves"
            elif not legal:
                reason = "a2a3 not legal - IMPOSSIBLE, would be fabricated"
            elif r["wall_ms"] < 1.0:
                reason = "instant answer (book / reserve-empty / tiny node budget)"
            else:
                reason = "SLOW with no info - SUSPICIOUS"
            print("| %s | %s | %.3f | %s | %d | %s | %s |" %
                  (os.path.relpath(f, root), r.get("i"), r["wall_ms"], r["fen"], nm, legal, reason))

print()
print("TOTAL a2a3-no-info records with wall > 5 ms: %d" % total_suspicious_hard)
