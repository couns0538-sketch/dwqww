#!/usr/bin/env python3
"""fixedpoint.py EXE

Test the claim that the clock drain CONVERGES to a fixed point rather than emptying.

The mechanism: the engine's hard time limit SCALES WITH THE REMAINING CLOCK
(TmHardPercent default 60 => hard limit ~ 60% of the clock, less Move Overhead default 10 ms).
So the per-move cost is not a constant: as the clock shrinks, the search shrinks with it.

If cost(C) = max( something, 0.6*C - 10 ) then a clock at C shrinks by cost(C) - increment per move,
and the fixed point is where cost(C) = increment:
    0.6*C - 10 = 60   =>   C = 116.67 ms
The claim to check is that measured behaviour lands near that.

METHOD (empirical, not algebra): give the engine a series of very small clocks and measure what it
actually uses. If the per-move cost tracks the clock down, the drain decelerates and converges; if the
cost stayed at its median (~104 ms) while the clock shrank, it would empty.
Threads 1, PC20.
"""
import argparse
import queue
import re
import subprocess
import threading
import time

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

FEN = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"   # a middlegame, real work


def one(exe, wtime, btime, inc, limit=20.0):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    q = queue.Queue()

    def rd():
        for line in p.stdout:
            q.put(line.rstrip("\n"))
        q.put(None)

    threading.Thread(target=rd, daemon=True).start()

    def send(c):
        p.stdin.write(c + "\n"); p.stdin.flush()

    def wait(pred, lim):
        t0 = time.monotonic()
        while True:
            rem = lim - (time.monotonic() - t0)
            if rem <= 0:
                return None
            try:
                line = q.get(timeout=rem)
            except queue.Empty:
                return None
            if line is None:
                return None
            if pred(line):
                return line

    send("uci"); wait(lambda l: l.startswith("uciok"), 30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
    send("isready"); wait(lambda l: l == "readyok", 30)
    send("ucinewgame"); send("isready"); wait(lambda l: l == "readyok", 30)
    send("position fen " + FEN); send("isready"); wait(lambda l: l == "readyok", 30)
    t0 = time.monotonic()
    send("go wtime %d btime %d winc %d binc %d" % (wtime, btime, inc, inc))
    bm = wait(lambda l: l.startswith("bestmove"), limit)
    wall = (time.monotonic() - t0) * 1000
    try:
        send("quit"); p.wait(timeout=5)
    except Exception:
        p.kill()
    return wall, (bm.split()[1] if bm and len(bm.split()) > 1 else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--inc", type=int, default=60)
    a = ap.parse_args()
    print("exe: %s  PC20  Threads 1  increment %d ms" % (a.exe, a.inc), flush=True)
    print("Q: does the per-move cost TRACK THE CLOCK DOWN (converging) or stay flat (emptying)?", flush=True)
    print()
    print("%-10s %-10s %-10s %-14s %s" % ("clock", "used_ms", "net_drain", "hard_limit_est", "note"),
          flush=True)
    clocks = [6000, 1000, 400, 250, 180, 150, 130, 120, 110, 100, 90, 80, 70, 60, 50]
    rows = []
    for c in clocks:
        used, mv = one(a.exe, c, c, a.inc)
        net = used - a.inc
        hard = 0.60 * c - 10      # the engine's own hard limit at this clock, from its defaults
        note = ""
        if used < hard * 0.75:
            note = "used well under its own hard limit (position finished first)"
        rows.append((c, used, net))
        print("%-10d %-10.0f %-10.0f %-14.1f %s" % (c, used, net, hard, note), flush=True)
    print()
    print("=== FIXED POINT CHECK ===", flush=True)
    print("  claim: the fixed point is where hard_limit(C) == increment, i.e. 0.60*C - 10 = %d" % a.inc,
          flush=True)
    print("  => C* = (%d + 10) / 0.60 = %.1f ms" % (a.inc, (a.inc + 10) / 0.60), flush=True)
    below = [r for r in rows if r[0] < (a.inc + 10) / 0.60]
    print("  clocks BELOW the claimed fixed point: %s" % ([r[0] for r in below] or "none"), flush=True)
    for c, used, net in below:
        print("    at clock %3d, used %5.0f ms -> net %+6.0f ms %s"
              % (c, used, net, "DRAINS" if net > 0 else "does not drain"), flush=True)


if __name__ == "__main__":
    main()
