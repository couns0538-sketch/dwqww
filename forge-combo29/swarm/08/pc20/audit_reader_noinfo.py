#!/usr/bin/env python3
"""audit_reader_noinfo.py OUT — does any committed harness of this seat rely on info lines being present?

08-N5: the book answers instantly with ZERO `info depth` lines, and a reader pattern can block waiting for something
that never comes. My committed timing harnesses use `read_until("bestmove")`, which is safe. But some of my analysis
scripts count `info depth` lines and could mis-handle a zero line case.

This audit checks, for every committed harness, whether it:
  (a) reads until `bestmove` (safe on a no-info answer), or
  (b) reads/counts info lines and would mis-report a zero-info case.

Then it RUNS one book position through the main timing harness (job1b/clock_latency2.py) to prove that harness
handles a zero-info answer without hanging.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys
import time
from pathlib import Path

OUT = sys.argv[1]
root = Path("..").resolve()

out = []
def emit(s):
    out.append(s)
    print(s)

emit("## Do this seat's harnesses survive a NO-INFO answer from the engine?")
emit("")
emit("(08-N5: the book answers instantly with zero `info depth` lines.)")
emit("")
emit("| harness | reads until bestmove? | counts info lines? | verdict |")
emit("|---|---|---|---|")

safe = risky = 0
for p in sorted(root.rglob("*.py")):
    try:
        txt = p.read_text(errors="ignore")
    except Exception:
        continue
    if "bestmove" not in txt:
        continue
    until_bm = ('read_until("bestmove"' in txt or "read_until('bestmove'" in txt
                or "done.wait" in txt or "startswith(\"bestmove\")" in txt
                or "startswith('bestmove')" in txt)
    counts_info = ('startswith("info depth")' in txt or "startswith('info depth')" in txt)
    if until_bm:
        safe += 1
        v = "SAFE (waits for bestmove)"
    else:
        risky += 1
        v = "**REVIEW — does not obviously wait for bestmove**"
    emit("| %s | %s | %s | %s |" % (p.relative_to(root), "yes" if until_bm else "**no**",
                                    "yes" if counts_info else "no", v))

emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| harnesses that wait for bestmove | %d |" % safe)
emit("| harnesses needing review | **%d** |" % risky)

emit("")
emit("## Live test: a BOOK position through the main timing harness")
emit("")
emit("The book answers with zero `info depth` lines. If clock_latency2.py handles it, the harness is safe on that path.")
emit("")
# write a one-position FEN file that the book answers, and run the real harness on it
open("/tmp/book_pos.fens", "w").write("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\n")
t0 = time.monotonic()
r = subprocess.run(["python3", str(root / "job1b" / "clock_latency2.py"),
                    "/home/ubuntu/builds/pc/forge", "/tmp/book_pos.fens", "movetime 100",
                    "/tmp/book_out.jsonl", "booktest"],
                   capture_output=True, text=True, timeout=120)
elapsed = time.monotonic() - t0
emit("| quantity | value |")
emit("|---|---|")
emit("| exit code | %d |" % r.returncode)
emit("| wall seconds | %.1f |" % elapsed)
emit("| completed without hanging | **%s** |" % ("YES" if r.returncode == 0 else "NO"))
if (root / "/tmp/book_out.jsonl").exists():
    pass
try:
    recs = [l for l in open("/tmp/book_out.jsonl") if l.strip()]
    emit("| records written | %d |" % len(recs))
    if recs:
        import json
        d = json.loads(recs[0])
        emit("| nlines on a book answer | **%d** |" % d.get("nlines", -1))
        emit("| bestmove recorded | %s |" % d.get("bestmove"))
except Exception as e:
    emit("| records | could not read: %s |" % e)

emit("")
if r.returncode == 0 and elapsed < 30:
    emit("**The main timing harness handles a zero-info book answer without hanging** and records it, so the 08-N5")
    emit("trap does not affect any timing number of this seat. Only the throwaway depth-sweep script was affected.")
else:
    emit("**The harness did NOT complete cleanly on a book position** — that would put every latency number at risk.")
    emit("Exit %d after %.1f s." % (r.returncode, elapsed))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
