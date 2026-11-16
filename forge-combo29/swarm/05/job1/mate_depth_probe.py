#!/usr/bin/env python3
"""mate_depth_probe.py EXE FEN DEPTH... -- run `go depth D` in a live conversation (never pre-feed quit,
which aborts the search), print the LAST pv line's score for each depth.
Decides whether a too-long mate distance is a depth artifact or a consistent reporting defect.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
FEN = sys.argv[2]
DEPTHS = [int(x) for x in sys.argv[3:]]

S14 = [
    "setoption name Threads value 1", "setoption name Hash value 16",
    "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe, options):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.lines = []
        self.send("uci")
        self.until("uciok")
        for o in options:
            self.send(o)
            self.send("isready")
            self.until("readyok")

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def until(self, token, limit=300):
        got = []
        t0 = time.time()
        while time.time() - t0 < limit:
            line = self.p.stdout.readline()
            if line == "":
                break
            line = line.rstrip("\n")
            got.append(line)
            if line.startswith(token):
                break
            if any(b in line for b in BAD):
                got.append("### HARNESS_STOP " + line)
                break
        return got

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


opts = [] if "--default" in sys.argv else S14
print(f"exe: {EXE}")
print(f"fen: {FEN}")
print(f"options: {'engine defaults' if not opts else 'S14 + Threads 1 + Hash 16'}")
print(f"{'depth':>5} {'score':>10} {'plies':>6} {'nodes':>10}  last pv line")
e = Engine(EXE, opts)
e.send("ucinewgame")
e.send("isready")
e.until("readyok")
for d in DEPTHS:
    e.send(f"position fen {FEN}")
    e.send("isready")
    e.until("readyok")
    e.send(f"go depth {d}")
    block = e.until("bestmove")
    pvlines = [l for l in block if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pvlines:
        print(f"{d:5d} {'(no pv)':>10}")
        continue
    last = pvlines[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    mv = last.split(" pv ", 1)[1].split() if " pv " in last else []
    nm = re.search(r"nodes (\d+)", last)
    bm = [l for l in block if l.startswith("bestmove")]
    print(f"{d:5d} {m.group(1)+' '+m.group(2) if m else '?':>10} {len(mv):6d} "
          f"{nm.group(1) if nm else '?':>10}  {last}")
    print(f"      bestmove line: {bm[0] if bm else '(none)'}")
e.close()
