#!/usr/bin/env python3
"""trace_anomaly.py EXE FEN OUTDIR : why does one position take 2.1x its last completed iteration?

19-F52 observed: `7r/2k2p2/2p3P1/2Ppn3/PP2p1b1/4P3/4BK2/R6R b - - 0 1` takes 1585.8 ms wall while its last
completed iteration reports 749 ms. Two candidate mechanisms:
  H1 fail-high re-search: an iteration fails high, the window is widened, and the re-search cost is paid but the
     final reported `info` line still carries only the last COMPLETED iteration's `time`. Signature: several
     `info depth D` lines with the same D and increasing time/nodes, or a final `info` whose nodes are far below
     the actual work.
  H2 hard-limit abort: the clock's hard limit cut an iteration off, so its cost was paid and discarded.
     Signature: the search ends with the last `info` at depth D, and the NEXT `info depth D+1` never appears but
     wall time keeps running past the last report.

Method: run the clock search once, recording for EVERY `info` line its depth, time and nodes, plus the wall clock
at the moment each line ARRIVED. Then compare:
  - the monotonic sequence of (depth, time) pairs (re-searches show repeated depths with rising time)
  - the gap between the LAST report and bestmove (a hard-limit abort shows a long silent gap)
  - total nodes reported at the end vs the node count on the last line (work done after the last report)
"""
import os
import re
import subprocess
import sys
import time

exe, fen, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Hash", "16"), ("Move Overhead", "10")]

p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)


def send(l):
    p.stdin.write(l + "\n")
    p.stdin.flush()


def readto(pred):
    got = []
    for _ in range(800000):
        l = p.stdout.readline()
        if not l:
            return got
        l = l.rstrip("\n")
        got.append(l)
        if pred(l):
            return got
    return got


send("uci")
readto(lambda l: l.startswith("uciok"))
for k, v in S14:
    send("setoption name %s value %s" % (k, v))
    send("isready")
    readto(lambda l: l.startswith("readyok"))
send("ucinewgame")
send("isready")
readto(lambda l: l.startswith("readyok"))
send("position fen " + fen)
send("isready")
readto(lambda l: l.startswith("readyok"))

t0 = time.monotonic()
send("go wtime 6000 btime 6000 winc 60 binc 60")
events = []
while True:
    line = p.stdout.readline()
    if not line:
        break
    now = (time.monotonic() - t0) * 1000.0
    line = line.rstrip()
    if line.startswith("info depth") and " pv " in line:
        d = nodes = tm = None
        try:
            d = int(line.split("info depth ")[1].split()[0])
        except (IndexError, ValueError):
            pass
        try:
            nodes = int(line.split("nodes ")[1].split()[0])
        except (IndexError, ValueError):
            pass
        try:
            tm = int(line.split("time ")[1].split()[0])
        except (IndexError, ValueError):
            pass
        events.append(("info", now, d, tm, nodes))
    if line.startswith("info depth") and " pv " not in line:
        events.append(("info-nopv", now, None, None, None))
    if line.startswith("bestmove"):
        events.append(("bestmove", now, line.split()[1] if len(line.split()) > 1 else None, None, None))
        break
send("quit")
try:
    p.communicate(timeout=60)
except subprocess.TimeoutExpired:
    p.kill()

infos = [e for e in events if e[0] == "info"]
best = [e for e in events if e[0] == "bestmove"]
lines = ["# trace of the 19-F52 anomaly", "", "position: " + fen, "",
         "PC r15, PC20, Threads 1, Hash 16, 6 s + 0.06, cold", "",
         "| arrival ms | depth | engine time ms | nodes |", "|---|---|---|---|"]
for kind, now, d, tm, nodes in infos:
    lines.append("| %.1f | %s | %s | %s |" % (now, d, tm, nodes))
last = infos[-1] if infos else None
b = best[0] if best else None
lines += ["", "## the three diagnostics", ""]
if last and b:
    gap = b[1] - last[1]
    lines.append("- wall time of the whole search: **%.1f ms**" % b[1])
    lines.append("- last completed iteration: depth %s, engine time %s ms, %s nodes" % (last[2], last[3], last[4]))
    lines.append("- **silent gap after the last report**: **%.1f ms**" % gap)
    depths = [e[2] for e in infos]
    repeats = [(d, sum(1 for x in depths if x == d)) for d in sorted(set(depths)) if depths.count(d) > 1]
    lines += ["", "### H1 (fail-high re-search) — repeated depths would show it", ""]
    lines.append("- depths reported more than once: %s" % (repeats if repeats else "**none — every depth reported exactly once**"))
    lines += ["", "### H2 (hard-limit abort) — a silent gap after the last report would show it", ""]
    if gap > 100:
        lines.append("- the gap is **%.1f ms**, i.e. **%.0f %%** of the whole search ran AFTER the last report: "
                     "consistent with H2, an iteration paid for and discarded" % (gap, 100 * gap / b[1]))
    else:
        lines.append("- the gap is only %.1f ms, so almost nothing ran after the last report: H2 is NOT supported" % gap)
text = "\n".join(lines)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print(text)
