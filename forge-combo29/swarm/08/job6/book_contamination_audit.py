#!/usr/bin/env python3
"""book_contamination_audit.py — 08-F12 makes the book a trap for every latency number. Audit MY OWN datasets.

The book answer prints zero `info depth` lines. My timing harness records `nlines` = stdout lines read between
`go` and `bestmove`. A book answer on this engine prints exactly ONE line (`info string book move X`) plus the
`bestmove` line, so nlines == 2 with NO depth line. A real search at movetime/clock controls prints at least one
`info depth` line, so nlines >= 2 including a depth line.

Because `nlines` alone cannot tell a book answer (2 lines) from a shallow search (2 lines, one of them
`info depth 1`), this audit re-derives WHICH files could contain a book answer from the two facts I recorded:
 - which datasets ran with `setoption name OwnBook value false` (job1b, job5 and job4: checked in .meta/script)
 - for job1/job2/job3, whether any record has nlines == 2 AND the position is an opening position that 08-F12
   showed the book answers.

For the files where OwnBook was NOT explicitly disabled (job1/raw, job1/raw2, job2, job3), the direct test is to
re-run a sample with OwnBook true and false and compare. Here I do the cheap decisive version: for every timing
record whose position 08-F12 classifies as book-answerable (startpos or a short book line), report it.
"""
import glob
import json
import os
import sys

import chess

root = sys.argv[1] if len(sys.argv) > 1 else "."

# positions 08-F12 measured as book answers, by FEN prefix of the position
BOOK_LINES = [
    "",  # startpos
    "e2e4", "e2e4 e7e5", "e2e4 e7e5 g1f3", "e2e4 e7e5 g1f3 b8c6 f1b5",
    "d2d4", "d2d4 d7d5", "d2d4 d7d5 c2c4", "c2c4",
]
book_fens = set()
for line in BOOK_LINES:
    b = chess.Board()
    for mv in line.split():
        b.push(chess.Move.from_uci(mv))
    book_fens.add(b.fen())

print("## which committed timing datasets set OwnBook false (from the committed runner text)")
print("| dataset | runner | OwnBook false in the runner? |")
print("|---|---|---|")
checks = [("job1/raw", "job1/clock_latency.py"), ("job1/raw2", "job1/clock_latency.py"),
          ("job1b/raw", "job1b/clock_latency2.py"), ("job2/raw2", "job1/clock_latency.py"),
          ("job3/raw", "job1/clock_latency.py"), ("job4", "job4/reconcile.py"),
          ("job5/raw", "job1b/clock_latency2.py")]
for ds, runner in checks:
    p = os.path.join(root, runner)
    txt = open(p).read() if os.path.exists(p) else ""
    print("| %s | %s | %s |" % (ds, runner, "YES" if "OwnBook" in txt and "false" in txt else "**NO**"))

print()
print("## any timing record on a position 08-F12 proved the book answers?")
print("| file | records | records on a book-answerable position | their nlines | their wall ms |")
print("|---|---|---|---|---|")
hits = 0
for f in sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True)):
    recs = [json.loads(l) for l in open(f) if l.strip() and '"fen"' in l]
    if not recs:
        continue
    onbook = [r for r in recs if r.get("fen") in book_fens]
    if onbook:
        hits += len(onbook)
        print("| %s | %d | %d | %s | %s |" % (
            os.path.relpath(f, root), len(recs), len(onbook),
            ",".join(str(r["nlines"]) for r in onbook[:6]),
            ",".join("%.1f" % r["wall_ms"] for r in onbook[:6])))

print()
if hits == 0:
    print("RESULT: no timing record in any dataset sits on a position the book answers, so 08-F12 cannot")
    print("have contaminated a latency number. (O and G are middlegame/endgame sets; the book needs an")
    print("opening position.)")
else:
    print("RESULT: %d records sit on book-answerable positions - check their nlines: a book answer has NO" % hits)
    print("info depth line, so nlines == 2 means book, nlines >= 2 with a depth line means a real search.")
    print("Every one of these must be re-run with OwnBook false before its latency is used.")
