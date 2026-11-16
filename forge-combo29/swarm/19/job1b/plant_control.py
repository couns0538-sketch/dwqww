#!/usr/bin/env python3
"""plant_control.py EXE OUTDIR : a control that proves the quit-abort harness can SEE the difference.

Opus's Rule 1: a "0 nodes" result counts only when the same harness, unchanged, is shown to detect the
non-zero case. My harness for 19-F12 is `quit_abort.py`; this file runs it in a mode where the search DOES
run (the terminator delayed), so the harness reports a large node count, and a mode where it must report
0. If both come out as expected, the harness can see the difference.
"""
import os
import subprocess
import sys
import time

exe, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
for var in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(var, None)


def measure(wait):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    proc.stdin.write("uci\nisready\nposition startpos\nisready\ngo depth 12\n")
    proc.stdin.flush()
    time.sleep(wait)
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    out, _ = proc.communicate(timeout=120)
    nodes = [int(l.split("nodes ")[1].split()[0]) for l in out.splitlines() if " nodes " in l]
    best = [l for l in out.splitlines() if l.startswith("bestmove")]
    return (max(nodes) if nodes else 0), (best[-1] if best else "(none)"), out


planted_nodes, planted_best, planted_out = measure(0.0)   # must be 0 -> the aborted case
real_nodes, real_best, real_out = measure(2.5)            # must be > 0 -> the searched case

with open(os.path.join(outdir, "planted.txt"), "w") as fh:
    fh.write("terminator immediately after go (the ABORTED case, expected 0 nodes)\n")
    fh.write(planted_out)
with open(os.path.join(outdir, "real.txt"), "w") as fh:
    fh.write("terminator 2.5 s after go (the SEARCHED case, expected > 0 nodes)\n")
    fh.write(real_out)

ok = planted_nodes == 0 and real_nodes > 1000
text = ("plant: aborted case nodes = %d, bestmove = %s\n"
        "real:  searched case nodes = %d, bestmove = %s\n"
        "the harness distinguishes the two: %s\n"
        % (planted_nodes, planted_best, real_nodes, real_best, "YES" if ok else "NO"))
open(os.path.join(outdir, "RESULT.txt"), "w").write(text)
print(text)
