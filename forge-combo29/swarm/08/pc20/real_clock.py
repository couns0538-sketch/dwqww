#!/usr/bin/env python3
"""real_clock.py OUT — the owner's ACTUAL match clock: 6 seconds + 0.06 s per move.

FABLE_TO_swarm_6: "the clock 6 seconds + 0.06 per move (its strength matches)". Every control I have measured so far
was a different shape (movetime, or sudden-death wtime 200 ms .. 30 s with winc 0). This measures the shape the owner
actually plays, PC build, PC20, Threads 1, Hash 16.

What "6 s + 0.06 per move" means at the engine's interface: the match program sends `wtime` and `btime` = the
remaining clock and `winc`/`binc` = 60 ms. This harness therefore walks a REAL game forward: start from a position,
ask the engine for a move on the clock, subtract the time it used, add the increment, and repeat, so the clock
DECREASES the way it does in a match. Two sweeps:

  A  the clock held AT 6000 ms for every move (isolates the per-move behaviour at the owner's clock size)
  B  a real countdown from 6000 ms with +60 ms per move, so the tail is measured at every clock level the game
     actually passes through, including the low end near the flag

For each move: wall time, plan (soft/hard from clock_plan.hpp with overhead 10, divisor 22), the clock BEFORE the
move, and whether the move exceeded the clock.

ARGUMENT ORDER: OUT first.
"""
import json
import subprocess
import sys
import time

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
INC = 60
OVERHEAD, DIV, HARDPCT, MULT = 10, 22, 60, 5

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

# a real-game start: the opening position, and a middlegame from set G
STARTS = [
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("G middlegame 1", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("G middlegame 2", "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"),
]
MAX_MOVES = 40


def plan_ms(clock):
    if clock <= OVERHEAD:
        return 0, 0, True
    avail = clock - OVERHEAD
    soft = avail // DIV + INC * 75 // 100
    hard = min(avail * HARDPCT // 100, soft * MULT)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard, False


class Eng:
    def __init__(self):
        self.p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.send("uci")
        while not self.p.stdout.readline().startswith("uciok"):
            pass
        for n, v in PC20:
            self.send("setoption name %s value %s" % (n, v))
            self.sync()

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def sync(self):
        self.send("isready")
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise EOFError
            if l.startswith("readyok"):
                return

    def move(self, fen, wtime, btime, side_white):
        self.send("ucinewgame")
        self.sync()
        self.send("position fen " + fen)
        self.sync()
        t0 = time.monotonic()
        self.send("go wtime %d btime %d winc %d binc %d" % (wtime, btime, INC, INC))
        lines = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise EOFError
            l = l.rstrip("\n")
            lines.append(l)
            if l.startswith("bestmove"):
                break
        wall = (time.monotonic() - t0) * 1000.0
        self.sync()
        bm = lines[-1].split()[1]
        lastd = 0
        for l in lines:
            if l.startswith("info depth"):
                try:
                    lastd = max(lastd, int(l.split()[2]))
                except (IndexError, ValueError):
                    pass
        return wall, bm, lastd

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


out = []
def emit(s):
    out.append(s)
    print(s)

# ---- Sweep A: clock pinned at 6000 ms every move
emit("## Sweep A — the owner's clock held AT 6000 ms + 60 ms increment, PC r15, PC20, Threads 1")
emit("")
emit("| start | move | clock ms | plan soft | plan hard | wall ms | over soft | over hard | over clock | depth |")
emit("|---|---|---|---|---|---|---|---|---|---|")
rowsA = []
e = Eng()
for label, fen in STARTS:
    for i in range(MAX_MOVES):
        soft, hard, empty = plan_ms(6000)
        wall, bm, d = e.move(fen, 6000, 6000, True)
        rowsA.append({"start": label, "clock": 6000, "soft": soft, "hard": hard, "wall": wall, "depth": d})
        if i < 6 or wall > soft:
            emit("| %s | %d | 6000 | %d | %d | %.1f | %s | %s | %s | %d |" %
                 (label, i + 1, soft, hard, wall, "YES" if wall > soft else "no",
                  "YES" if wall > hard else "no", "YES" if wall > 6000 else "no", d))
e.close()

# ---- Sweep B: a real countdown from 6000 with +60 per move
emit("")
emit("## Sweep B — a real countdown from 6000 ms, +60 ms per move, so the tail is seen at every clock level")
emit("")
emit("| start | move | clock before ms | plan soft | wall ms | clock after ms | over soft | over hard | over clock |")
emit("|---|---|---|---|---|---|---|---|---|")
rowsB = []
e = Eng()
for label, fen in STARTS:
    clock = 6000
    for i in range(MAX_MOVES):
        soft, hard, empty = plan_ms(clock)
        wall, bm, d = e.move(fen, clock, clock, True)
        after = clock - int(wall) + INC
        rowsB.append({"start": label, "clock": clock, "soft": soft, "hard": hard, "wall": wall, "after": after})
        emit("| %s | %d | %d | %d | %.1f | %d | %s | %s | %s |" %
             (label, i + 1, clock, soft, wall, max(after, 0), "YES" if wall > soft else "no",
              "YES" if (hard and wall > hard) else "no", "YES" if wall > clock else "no"))
        clock = max(after, 0)
        if clock <= OVERHEAD:
            emit("| %s | — | %d | reserve empty reached; sweep ends | | | | | |" % (label, clock))
            break
e.close()

def pct(v, p):
    s = sorted(v)
    k = (len(s) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)

emit("")
emit("## The numbers that matter at the owner's clock")
emit("")
emit("| sweep | moves | median ms | p99 ms | worst ms | worst as % of clock | over soft | over hard | over clock |")
emit("|---|---|---|---|---|---|---|---|---|")
for name, rows, pinned in (("A pinned 6000", rowsA, True), ("B countdown", rowsB, False)):
    w = [r["wall"] for r in rows]
    over_soft = sum(1 for r in rows if r["wall"] > r["soft"])
    over_hard = sum(1 for r in rows if r["hard"] and r["wall"] > r["hard"])
    over_clock = sum(1 for r in rows if r["wall"] > r["clock"])
    worstr = max(rows, key=lambda r: r["wall"])
    emit("| %s | %d | %.1f | %.1f | **%.1f** | %.1f %% | %d | %d | **%d** |" %
         (name, len(rows), pct(w, 50), pct(w, 99), max(w), 100.0 * max(w) / worstr["clock"], over_soft,
          over_hard, over_clock))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
